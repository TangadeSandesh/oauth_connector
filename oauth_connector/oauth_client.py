import frappe

DEFAULT_CLIENT_NAME = "StudioOS"
DEFAULT_REDIRECT_URIS = ("https://app.studioos.com/auth/callback",)
DEFAULT_SCOPES = "all openid"

# Frappe's own default. Every System User has it, so this keeps the usual case
# working, but it is emphatically not "everyone" -- see get_allowed_roles.
DEFAULT_ALLOWED_ROLES = ("Desk User",)


def get_client_app_name() -> str:
	"""Name shown to the user on the consent screen.

	Override in site_config.json:  "oauth_connector_client_name": "StudioOS"
	"""
	return frappe.conf.get("oauth_connector_client_name") or DEFAULT_CLIENT_NAME


def get_scopes() -> str:
	"""Override in site_config.json:  "oauth_connector_scopes": "all openid" """
	return frappe.conf.get("oauth_connector_scopes") or DEFAULT_SCOPES


def get_redirect_uris() -> list[str]:
	"""Redirect URIs this site will accept back from the client application.

	Override per site in site_config.json, which is how a local bench points at
	a dev server instead of production:

	    "oauth_connector_redirect_uris": ["http://localhost:8787/auth/callback"]

	A single string is accepted as well as a list.
	"""
	configured = frappe.conf.get("oauth_connector_redirect_uris") or frappe.conf.get(
		"oauth_connector_redirect_uri"
	)

	if not configured:
		return list(DEFAULT_REDIRECT_URIS)

	if isinstance(configured, str):
		configured = [configured]

	uris = [uri.strip() for uri in configured if uri and uri.strip()]
	return uris or list(DEFAULT_REDIRECT_URIS)


def get_allowed_roles() -> list[str]:
	"""Which roles may sign in through this client.

	This is the single most confusing thing about Frappe's OAuth, so it is worth
	stating plainly. `validate_client_id` calls the client's
	`user_has_allowed_role()`, which intersects this list with the user's roles:

	    return bool(allowed_roles & set(frappe.get_roles()))

	Two consequences follow, and both bite in production.

	1. **An empty list refuses everyone.** The empty intersection is falsy, so a
	   client with no allowed roles rejects every user including the owner.
	2. **The refusal is reported as "Invalid client_id".** Frappe blames the
	   client, not the user's roles, so the site administrator goes looking for
	   a typo in the client id while the real cause is a missing role.

	The practical failure is a studio's newly created employee: they exist, they
	have a password, and sign-in refuses them with an error that points at
	entirely the wrong thing.

	Override per site in site_config.json:

	    "oauth_connector_allowed_roles": ["Desk User", "Projects User"]

	A single string is accepted as well as a list.
	"""
	configured = frappe.conf.get("oauth_connector_allowed_roles") or frappe.conf.get(
		"oauth_connector_allowed_role"
	)

	if not configured:
		return list(DEFAULT_ALLOWED_ROLES)

	if isinstance(configured, str):
		configured = [configured]

	roles = [r.strip() for r in configured if r and r.strip()]

	# Never hand Frappe an empty list: it would lock every user out of sign-in,
	# and the resulting error names the wrong cause.
	if not roles:
		return list(DEFAULT_ALLOWED_ROLES)

	return roles


def resolve_allowed_roles() -> tuple[list[str], list[str]]:
	"""Configured roles split into (roles that exist here, roles that do not).

	A role named in site_config but absent from the site silently contributes
	nothing to the intersection, so a client can end up effectively empty while
	looking configured. Callers surface the missing ones rather than dropping
	them quietly.
	"""
	wanted = get_allowed_roles()
	existing = [r for r in wanted if frappe.db.exists("Role", r)]
	missing = [r for r in wanted if r not in existing]
	return existing, missing


def get_client_name() -> str | None:
	"""Name of this site's OAuth client, which is also its client_id."""
	return frappe.db.get_value("OAuth Client", {"app_name": get_client_app_name()}, "name")


def register() -> str:
	"""Create the OAuth client, or bring an existing one in line with site config.

	Idempotent, so it is safe to run on both install and migrate.
	"""
	uris = get_redirect_uris()
	joined = "\n".join(uris)
	scopes = get_scopes()
	roles, missing_roles = resolve_allowed_roles()

	if missing_roles:
		print(
			f"[oauth-connector] WARNING: these roles do not exist on this site and were "
			f"skipped: {', '.join(missing_roles)}"
		)

	if not roles:
		# Refuse rather than write a client that rejects every user with a
		# message blaming the client id. Better to fail here, loudly, than
		# there, misleadingly.
		frappe.throw(
			"None of the roles in `oauth_connector_allowed_roles` exist on this site, "
			"so nobody would be able to sign in. Fix the list in site_config.json "
			"and run `bench migrate`."
		)

	name = get_client_name()

	if name:
		client = frappe.get_doc("OAuth Client", name)
		current_roles = sorted(d.role for d in client.allowed_roles)
		changed = (
			client.redirect_uris != joined
			or client.default_redirect_uri != uris[0]
			or client.scopes != scopes
			or current_roles != sorted(roles)
		)
		if changed:
			client.redirect_uris = joined
			client.default_redirect_uri = uris[0]
			client.scopes = scopes
			set_allowed_roles(client, roles)
			client.save(ignore_permissions=True)
			frappe.db.commit()
			print(
				f"[oauth-connector] configuration updated, client_id={client.client_id}, "
				f"allowed_roles={', '.join(roles)}"
			)
		else:
			print(f"[oauth-connector] already registered, client_id={client.client_id}")
		return client.name

	client = frappe.get_doc(
		{
			"doctype": "OAuth Client",
			"app_name": get_client_app_name(),
			"scopes": scopes,
			"redirect_uris": joined,
			"default_redirect_uri": uris[0],
			"grant_type": "Authorization Code",
			"response_type": "Code",
			"skip_authorization": 0,
		}
	)
	set_allowed_roles(client, roles)
	client.insert(ignore_permissions=True)
	frappe.db.commit()

	print(
		f"[oauth-connector] registered, client_id={client.client_id}, "
		f"allowed_roles={', '.join(roles)}"
	)
	return client.name


def set_allowed_roles(client, roles: list[str]) -> None:
	"""Replace the client's allowed roles wholesale.

	Set rather than merged, so removing a role from site_config actually removes
	it. A merge would make the list grow-only, and an access list you cannot
	narrow is not an access list.
	"""
	client.set("allowed_roles", [])
	for role in roles:
		client.append("allowed_roles", {"role": role})


def deregister() -> None:
	"""Remove the OAuth client and every token issued against it.

	`OAuth Client` is a Frappe core doctype, so uninstalling this app does not
	take it along. Without this, a site that drops the client application is
	left holding a live credential that still grants access to its data.
	"""
	name = get_client_name()

	if not name:
		print("[oauth-connector] no OAuth client to remove")
		return

	# Issued tokens link to the client, so they have to go first.
	for doctype in ("OAuth Bearer Token", "OAuth Authorization Code"):
		for row in frappe.get_all(doctype, filters={"client": name}, pluck="name"):
			frappe.delete_doc(doctype, row, force=True, ignore_permissions=True)

	frappe.delete_doc("OAuth Client", name, force=True, ignore_permissions=True)
	frappe.db.commit()

	print(f"[oauth-connector] removed OAuth client {name} and its tokens")

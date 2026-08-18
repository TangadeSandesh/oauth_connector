import frappe

DEFAULT_SCOPES = "all openid"

# Frappe's own default. Every System User has it, so this keeps the usual case
# working, but it is emphatically not "everyone" -- see get_allowed_roles.
DEFAULT_ALLOWED_ROLES = ("Desk User",)

# The application's name and callback URL have NO defaults, deliberately.
#
# They used to default to one particular product and its domain. On a site that
# installed this app without configuring it, that registered a client named
# after someone else's application, pointing at someone else's server, on a
# stranger's data -- and the consent screen would show that name to the site's
# own users as though they had asked for it.
#
# There is no safe value to guess here, so nothing is guessed. An unconfigured
# install registers nothing at all and says what to set; see `register`.

# Where the created client's id is remembered, so it can still be found after
# the configured app name changes. Looking it up by app_name alone means
# renaming the application orphans the old client -- leaving exactly the live,
# unowned credential this app exists to clean up.
CLIENT_KEY = "oauth_connector_client"


def get_client_app_name() -> str | None:
	"""Name shown to the user on the consent screen, or None if unconfigured.

	Required. Set in site_config.json:

	    "oauth_connector_client_name": "Your App Name"
	"""
	configured = frappe.conf.get("oauth_connector_client_name")
	return configured.strip() if isinstance(configured, str) and configured.strip() else None


def get_scopes() -> str:
	"""Override in site_config.json:  "oauth_connector_scopes": "all openid" """
	return frappe.conf.get("oauth_connector_scopes") or DEFAULT_SCOPES


def get_redirect_uris() -> list[str]:
	"""Redirect URIs this site will accept back from the client application.

	Required, and with no default: this is where the site sends a user's
	authorization code, so a guessed value sends it to the wrong host.

	Set per site in site_config.json, which is also how a local bench points at
	a dev server instead of production:

	    "oauth_connector_redirect_uris": ["http://localhost:8787/auth/callback"]

	A single string is accepted as well as a list.
	"""
	configured = frappe.conf.get("oauth_connector_redirect_uris") or frappe.conf.get(
		"oauth_connector_redirect_uri"
	)

	if not configured:
		return []

	if isinstance(configured, str):
		configured = [configured]

	return [uri.strip() for uri in configured if uri and uri.strip()]


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
	"""Name of this site's OAuth client, which is also its client_id.

	Read from the remembered id first. Falling back to an app_name lookup keeps
	clients created before that id was recorded findable, and is also what makes
	renaming the application safe: the rename updates the existing client rather
	than stranding it and creating a second one.
	"""
	remembered = frappe.db.get_default(CLIENT_KEY)
	if remembered and frappe.db.exists("OAuth Client", remembered):
		return remembered

	app_name = get_client_app_name()
	if not app_name:
		return None

	return frappe.db.get_value("OAuth Client", {"app_name": app_name}, "name")


def register() -> str | None:
	"""Create the OAuth client, or bring an existing one in line with site config.

	Idempotent, so it is safe to run on both install and migrate.

	Returns None when the site has not been configured yet. That is deliberately
	not an error: on the Marketplace route people install first and configure
	afterwards, and an install that hard-fails would look like a broken app.
	Nothing is registered until there is something real to register.
	"""
	app_name = get_client_app_name()
	uris = get_redirect_uris()

	if not app_name or not uris:
		missing = []
		if not app_name:
			missing.append('"oauth_connector_client_name": "Your App Name"')
		if not uris:
			missing.append(
				'"oauth_connector_redirect_uris": ["https://yourapp.com/auth/callback"]'
			)
		print(
			"[oauth-connector] not configured yet, so no OAuth client was created.\n"
			"[oauth-connector] Add to this site's config:\n"
			+ "".join(f"[oauth-connector]     {line}\n" for line in missing)
			+ "[oauth-connector] then run `bench --site <site> migrate` "
			"(or trigger a migrate from the Frappe Cloud dashboard)."
		)
		return None

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
			client.app_name != app_name
			or client.redirect_uris != joined
			or client.default_redirect_uri != uris[0]
			or client.scopes != scopes
			or current_roles != sorted(roles)
		)
		if changed:
			# Renaming the application renames this client rather than leaving
			# the old one behind. A second, unowned client would still grant
			# access to the site's data.
			client.app_name = app_name
			client.redirect_uris = joined
			client.default_redirect_uri = uris[0]
			client.scopes = scopes
			set_allowed_roles(client, roles)
			client.save(ignore_permissions=True)
			frappe.db.set_default(CLIENT_KEY, client.name)
			frappe.db.commit()
			print(
				f"[oauth-connector] configuration updated, client_id={client.client_id}, "
				f"allowed_roles={', '.join(roles)}"
			)
		else:
			frappe.db.set_default(CLIENT_KEY, client.name)
			frappe.db.commit()
			print(f"[oauth-connector] already registered, client_id={client.client_id}")
		return client.name

	client = frappe.get_doc(
		{
			"doctype": "OAuth Client",
			"app_name": app_name,
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
	frappe.db.set_default(CLIENT_KEY, client.name)
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
	frappe.db.set_default(CLIENT_KEY, None)
	frappe.db.commit()

	print(f"[oauth-connector] removed OAuth client {name} and its tokens")

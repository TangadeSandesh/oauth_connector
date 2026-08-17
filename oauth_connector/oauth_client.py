import frappe

DEFAULT_CLIENT_NAME = "StudioOS"
DEFAULT_REDIRECT_URIS = ("https://app.studioos.com/auth/callback",)
DEFAULT_SCOPES = "all openid"


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

	name = get_client_name()

	if name:
		client = frappe.get_doc("OAuth Client", name)
		changed = (
			client.redirect_uris != joined
			or client.default_redirect_uri != uris[0]
			or client.scopes != scopes
		)
		if changed:
			client.redirect_uris = joined
			client.default_redirect_uri = uris[0]
			client.scopes = scopes
			client.save(ignore_permissions=True)
			frappe.db.commit()
			print(f"[oauth-connector] configuration updated, client_id={client.client_id}")
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
	client.insert(ignore_permissions=True)
	frappe.db.commit()

	print(f"[oauth-connector] registered, client_id={client.client_id}")
	return client.name


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

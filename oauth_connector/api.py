import frappe

from oauth_connector.oauth_client import get_client_app_name, get_client_name


@frappe.whitelist()
def get_registration():
	"""Everything the client application needs to talk to this site.

	System Manager only - this returns the client secret. Intended for the site
	owner during onboarding, and later for the connector to self-register this
	site with the client application.
	"""
	frappe.only_for("System Manager")

	name = get_client_name()
	if not name:
		app_name = get_client_app_name()
		if not app_name:
			frappe.throw(
				"This site has not been configured yet. Set "
				"`oauth_connector_client_name` and `oauth_connector_redirect_uris` "
				"in the site config, then run a migrate."
			)
		frappe.throw(f"No OAuth client is registered for {app_name} on this site.")

	client = frappe.get_doc("OAuth Client", name)

	return {
		"site": frappe.utils.get_url(),
		"openid_configuration": frappe.utils.get_url("/.well-known/openid-configuration"),
		"app_name": client.app_name,
		"client_id": client.client_id,
		"client_secret": client.client_secret,
		"redirect_uris": (client.redirect_uris or "").splitlines(),
		"scopes": client.scopes,
		# Surfaced because Frappe reports "Invalid client_id" when a user lacks
		# these roles, which sends anyone debugging it to the wrong place.
		"allowed_roles": sorted(d.role for d in client.allowed_roles),
	}

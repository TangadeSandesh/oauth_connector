# OAuth Connector

Registers an external application as an OAuth client on a Frappe/ERPNext site,
so that application can offer **"Sign in with ERPNext"** against this site — and
removes the credential cleanly when the app is uninstalled.

Frappe already ships a full OAuth 2.0 / OpenID Connect provider. What it does not
ship is a way to get a client registered without a site administrator creating an
`OAuth Client` record by hand. This app does that on install.

## Why the uninstall half matters

`OAuth Client` is a **Frappe core doctype**. It does not belong to this app's
module, so `bench uninstall-app` leaves the record behind. A site that removed
the integration would keep a live client ID and secret still granting access to
its data. `before_uninstall` deletes the client along with every bearer token
and authorization code issued against it.

## Install

```bash
bench get-app https://github.com/TangadeSandesh/OAuth-connector
bench --site <your-site> install-app oauth_connector
```

On install you will see:

```
[oauth-connector] registered, client_id=xxxxxxxxxx
```

## Configure

Defaults target StudioOS in production. Override per site in
`sites/<your-site>/site_config.json`:

| Key | Default | Purpose |
|---|---|---|
| `oauth_connector_client_name` | `StudioOS` | Application name shown on the consent screen |
| `oauth_connector_redirect_uris` | `https://app.studioos.com/auth/callback` | String or list of accepted callback URLs |
| `oauth_connector_scopes` | `all openid` | Scopes granted to the client |

Pointing a local bench at a dev server:

```json
{
  "oauth_connector_redirect_uris": ["http://localhost:8787/auth/callback"]
}
```

Then `bench --site <your-site> migrate` to apply it — `after_migrate` re-runs
registration, and updating config never creates a second client.

## Reading the credentials

```
GET /api/method/oauth_connector.api.get_registration
```

System Manager only, as it returns the client secret. Response:

```json
{
  "site": "https://studio.example.com",
  "openid_configuration": "https://studio.example.com/.well-known/openid-configuration",
  "app_name": "StudioOS",
  "client_id": "...",
  "client_secret": "...",
  "redirect_uris": ["https://app.studioos.com/auth/callback"],
  "scopes": "all openid"
}
```

The client application should read `openid_configuration` rather than hardcoding
endpoints — Frappe serves a complete OIDC discovery document, so authorization,
token, userinfo, introspection and revocation endpoints are all discoverable
from the site domain alone.

## Notes for the client application

- **ID tokens are HS256-signed** with the client secret, not a public key. There
  is no JWKS, so tokens cannot be verified in a browser. Keep token handling
  server-side.
- Use the **authorization code flow with PKCE**. The site also advertises
  implicit response types; do not use them.
- Requests made with a user's access token run **as that user**, so the site's
  own role permissions apply without the client application implementing any.

## Uninstall

```bash
bench --site <your-site> uninstall-app oauth_connector
```

```
[oauth-connector] removed OAuth client xxxxxxxxxx and its tokens
```

## Contributing

This app uses `pre-commit` for formatting and linting (ruff, eslint, prettier,
pyupgrade):

```bash
cd apps/oauth_connector
pre-commit install
```

## License

MIT

from oauth_connector.oauth_client import deregister, register


def after_install():
	"""Register the client application on the site this app was installed into."""
	register()


def after_migrate():
	"""Re-apply registration so changed site_config values take effect."""
	register()


def before_uninstall():
	"""Take the credential with us. See oauth_client.deregister."""
	deregister()

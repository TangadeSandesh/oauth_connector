app_name = "oauth_connector"
app_title = "OAuth Connector"
app_publisher = "Sandesh"
app_description = "Registers a client application as an OAuth client on this Frappe site, and removes it cleanly on uninstall."
app_email = "cloudshapeddreamsstudio@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "oauth_connector",
# 		"logo": "/assets/oauth_connector/logo.png",
# 		"title": "OAuth Connector",
# 		"route": "/oauth_connector",
# 		"has_permission": "oauth_connector.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/oauth_connector/css/oauth_connector.css"
# app_include_js = "/assets/oauth_connector/js/oauth_connector.js"

# include js, css files in header of web template
# web_include_css = "/assets/oauth_connector/css/oauth_connector.css"
# web_include_js = "/assets/oauth_connector/js/oauth_connector.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "oauth_connector/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "oauth_connector/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "oauth_connector.utils.jinja_methods",
# 	"filters": "oauth_connector.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "oauth_connector.install.before_install"
after_install = "oauth_connector.install.after_install"

# Re-apply registration so changed site_config values take effect on migrate.
after_migrate = ["oauth_connector.install.after_migrate"]

# Uninstallation
# ------------

# `OAuth Client` is a core doctype and does not leave with this app, so the
# credential has to be removed explicitly. See oauth_client.deregister.
before_uninstall = "oauth_connector.install.before_uninstall"
# after_uninstall = "oauth_connector.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "oauth_connector.utils.before_app_install"
# after_app_install = "oauth_connector.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "oauth_connector.utils.before_app_uninstall"
# after_app_uninstall = "oauth_connector.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "oauth_connector.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"oauth_connector.tasks.all"
# 	],
# 	"daily": [
# 		"oauth_connector.tasks.daily"
# 	],
# 	"hourly": [
# 		"oauth_connector.tasks.hourly"
# 	],
# 	"weekly": [
# 		"oauth_connector.tasks.weekly"
# 	],
# 	"monthly": [
# 		"oauth_connector.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "oauth_connector.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "oauth_connector.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "oauth_connector.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["oauth_connector.utils.before_request"]
# after_request = ["oauth_connector.utils.after_request"]

# Job Events
# ----------
# before_job = ["oauth_connector.utils.before_job"]
# after_job = ["oauth_connector.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"oauth_connector.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


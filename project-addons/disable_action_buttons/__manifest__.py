{
    "name": "Disable Action buttons",
    "description": "Disable archive and unarchive fields on a list view in partners and disable action button for group 'group_comercial_ext' ",
    "version": "0.1",
    "category": "Extra Tools",
    'author': 'Visiotech',
    'website': 'www.visiotechsecurity.com',
    "data": [
        "views/assets.xml",
        "security/groups.xml"
    ],
    "depends": [
        "web",
        "stock_custom",
        "web_export_view"
    ],
    "auto_install": False,
    "installable": True,
}

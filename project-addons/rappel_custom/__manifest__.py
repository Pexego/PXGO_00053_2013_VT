# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Rappel custom",
    'version': '1.0',
    'category': 'Custom',
    'description': """Several little customizations in rappels""",
    'author': 'Nadia Ferreyra',
    "depends": ['base', 'rappel', 'product_brand'],
    "data": ["views/rappel_view.xml", "data/rappel_mail_advice_data.xml"],
    "installable": True
}

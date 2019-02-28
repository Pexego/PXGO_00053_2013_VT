# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Partner sale graphic",
    'version': '11.0.1.0.0',
    'category': '',
    'description': """Adds a graphic of sales in the partner form view""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ["base",
                "sale",
                "partner_risk__stock_reserve__rel"],
    "data": ["data/ir_cron.xml",
             "views/res_partner_view.xml"],
    "installable": True
}

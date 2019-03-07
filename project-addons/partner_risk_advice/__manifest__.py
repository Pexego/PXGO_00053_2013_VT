# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Partner Risk Advice",
    'version': '11.0.1.0.0',
    'category': 'partner',
    'description': """Manage Risk Advices by Email""",
    'author': 'Comunitea Servicios Tecnológicos',
    'website': 'www.comunitea.com',
    "depends": ['base', 'mail', 'crm_claim'],
    "data": [
            'views/res_partner_view.xml',
            'views/partner_risk_advice_mail.xml',
            'views/risk_advice_view.xml',
            'data/ir_cron.xml',
            'security/ir.model.access.csv'],
    "installable": True
}

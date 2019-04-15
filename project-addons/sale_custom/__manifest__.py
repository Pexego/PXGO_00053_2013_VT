# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "VT sale customizations",
    "summary": "sale order line tree reorganization",
    "version": "11.0.1.0.0",
    "category": "Uncategorized",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "sale",
        "purchase",
        "sale_stock",
        "sale_display_stock",
        "sale_margin_percentage",
        "partner_risk_advice",
        'reserve_without_save_sale'
    ],
    "data": [
        'views/sale_view.xml',
        'wizard/sale_confirm_wizard_view.xml'
    ],
}

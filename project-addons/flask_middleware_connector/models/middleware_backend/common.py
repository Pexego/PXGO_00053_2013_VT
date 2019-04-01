# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MiddlewareBackend(models.Model):
    _name = 'middleware.backend'
    _description = 'Middleware Backend'
    _inherit = 'connector.backend'
    _rec_name = "location"

    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_stock_conservative')],
            limit=1)
        return field

    @api.model
    def _get_price_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'list_price3')],
            limit=1)
        return field

    @api.model
    def _select_versions(self):
        return [('1.0', 'Middleware 1.0')]

    name = fields.Char(string='Name', required=True)
    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    location = fields.Char(
        string='Location',
        required=True,
        help="Url to middleware application xmlrpc api",
    )
    username = fields.Char(
        string='Username',
        help="Webservice user", required=True
    )
    password = fields.Char(
        string='Password', required=True,
        help="Webservice password",
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the '
             'stock quantities.',
    )
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language."
    )
    product_stock_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Stock Field',
        default=_get_stock_field_id,
        domain="[('model', '=', 'product.product'),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "stock inventory updates.", required=True
    )
    '''price_unit_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Price Field',
        default=_get_price_field_id,
        domain="[('model', '=', 'product.product'),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "sale price unit updates.", required=True
    )'''

    @api.multi
    def export_current_web_data(self):
        for midd in self:
            #~ countries = self.env['res.country'].search([])
            #~ for country in countries:
                #~ export_country(session, 'res.country', country.id)
            #~ brands = self.env['product.brand'].search([])
            #~ for brand in brands:
                #~ export_product_brand(session, 'product.brand', brand.id)
            #~ brand_country_rels = self.env['brand.country.rel'].search([])
            #~ for rel in brand_country_rels:
                #~ export_product_brand_rel(session, 'brand.country.rel', rel.id)
            #~ categories = self.env['product.category'].search([])
            #~ for category in categories:
                #~ export_product_category(session, 'product.category', category.id)
            #~ products = self.env["product.product"].\
                #~ search([('web', '=', 'published')])
            #~ for product in products:
                #~ export_product(session, "product.product", product.id)
            #~ users = self.env['res.users'].search([('web', '=', True)])
            #~ for user in users:
                #~ export_commercial(session, 'res.users', user.id)
            #~ partner_obj = self.env['res.partner']
            #~ partner_ids = partner_obj.search([('is_company', '=', True),
                                              #~ ('web', '=', True),
                                              #~ ('customer', '=', True)])
            #~ picking_obj = self.env['stock.picking']
            #~ picking_ids = picking_obj.search([('partner_id', 'child_of', partner_ids.ids),
                                              #~ ('state', '!=', 'cancel'),
                                              #~ ('picking_type_id.code', '=', 'outgoing')])
            #~ for picking in picking_ids:
                #~ export_picking.delay(session, 'stock.picking', picking.id)

            #~ contact_ids = partner_obj.search([('parent_id', 'in', partner_ids.ids),
                                              #~ ('active', '=', True),
                                              #~ ('customer', '=', True),
                                              #~ ('is_company', '=', False),
                                              #~ ('web', '=', False)])
            #~ for contact in contact_ids:
                #~ export_partner.delay(session, "res.partner", contact.id)
            #~ for partner in partner_ids:
            #~     export_partner.delay(session, "res.partner", partner.id)
            #~ substates = self.env['substate.substate'].search([])
            #~ for substate in substates:
                #~ export_rma_status(session, 'substate.substate', substate.id)

            #~ rmas = self.env['crm.claim'].search(['|', ('partner_id.web', '=', True),
                                                 #~ ('partner_id.commercial_partner_id.web', '=', True)])
            #~ for rma in rmas:
                #~ export_rma.delay(session, 'crm.claim', rma.id)
                #~ for line in rma.claim_line_ids:
                    #~if line.product_id.web == 'published':
                    #~ export_rmaproduct.delay(session, 'claim.line', line.id)
            invoices = self.env['account.invoice'].\
                search([('commercial_partner_id.web', '=', True),
                        ('state', 'in', ['open', 'paid']),
                        ('number', 'not like', '%ef%')])
            for invoice in invoices:
                invoice.with_delay().export_invoice()
            #~ products = self.env["product.product"]. \
            #~     search(['manufacturer_ref', '!=', False])
            #~ for product in products:
            #~     update_product.delay(session, "product.template", product.product_tmpl_id.id)
                #~ product.web = 'published'

        return True


# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class MiddlewareBackend(models.TransientModel):
    _name = 'middleware.backend.export'

    type_export = fields.Selection(
        selection=[
            ('partner', 'Partner'),
            ('invoices', 'Invoices'),
            ('pickings', 'Pickings'),
            ('rmas', 'RMAs'),
            ('products', 'Products'),
            ('order', 'Orders'),
            ('tags', 'Tags'),
            ('customer_tags_rel', 'Customer Tags Rel'),
            ('rappel', 'Rappel'),
            ('rappelsection', 'Rappel Sections'),
            ('countrystate', 'States'),
            ('producttag', 'Product Tag'),
            ('producttagproductrel', 'Product Tags Rel')
        ],
        string='Export type',
        required=True,
    )

    mode_export = fields.Selection(
        selection=[
            ('export', 'Export'),
            ('update', 'Update')
        ],
        string='Export mode',
        required=True,
    )

    start_date = fields.Date('Start Date',
                             default=fields.Date.context_today)
    finish_date = fields.Date('Finish Date',
                              default=fields.Date.context_today)
    model_ids = fields.Char('Ids')

    @api.multi
    def do_export(self):
        if self.model_ids:
            object_ids = list(map(int, self.model_ids.split(',')))
        else:
            object_ids = False

        if self.type_export == 'partner':
            partner_obj = self.env['res.partner']
            if object_ids:
                partner_ids = partner_obj.browse(object_ids)
            else:
                partner_ids = partner_obj.search([('is_company', '=', True),
                                                  ('web', '=', True),
                                                  ('customer', '=', True)])
            contact_ids = partner_obj.search([('id', 'child_of', partner_ids.ids),
                                              ('id', 'not in', partner_ids.ids),
                                              ('customer', '=', True),
                                              ('is_company', '=', False)])
            if self.mode_export == 'export':
                for partner in partner_ids:
                    partner.with_delay().export_partner()
                for contact in contact_ids:
                    contact.with_delay().export_partner()
            else:
                for partner in partner_ids:
                    partner.with_delay().update_partner()
                for contact in contact_ids:
                    contact.with_delay().update_partner()
        elif self.type_export == 'invoices':
            if object_ids:
                invoices = self.env['account.invoice'].browse(object_ids)
            else:
                invoices = self.env['account.invoice']. \
                    search([('commercial_partner_id.web', '=', True),
                            ('state', 'in', ['open', 'paid']),
                            ('number', 'not like', '%ef%'),
                            ('company_id', '=', 1),
                            ('date_invoice', '>=', self.start_date),
                            ('date_invoice', '<=', self.finish_date)])
            if self.mode_export == 'export':
                for invoice in invoices:
                    invoice.with_delay().export_invoice()
            else:
                for invoice in invoices:
                    invoice.with_delay().update_invoice()
        elif self.type_export == 'pickings':
            if object_ids:
                picking_ids = self.env['stock.picking'].browse(object_ids)
            else:
                partner_obj = self.env['res.partner']
                partner_ids = partner_obj.search([('is_company', '=', True),
                                                  ('web', '=', True),
                                                  ('customer', '=', True)])
                picking_obj = self.env['stock.picking']
                picking_ids = picking_obj.search([('partner_id', 'child_of', partner_ids.ids),
                                                  ('state', '!=', 'cancel'),
                                                  ('company_id', '=', 1),
                                                  ('not_sync', '=', False),
                                                  ('date', '>=', self.start_date),
                                                  ('date', '<=', self.finish_date),
                                                  ('picking_type_id.code', '=', 'outgoing')])
            if self.mode_export == 'export':
                for picking in picking_ids:
                    picking.with_delay().export_picking()
                    for line in picking.move_lines:
                        line.with_delay().export_pickingproduct()
            else:
                for picking in picking_ids:
                    picking.with_delay().update_picking()
                    for line in picking.move_lines:
                        line.with_delay().update_pickingproduct()

        elif self.type_export == 'rmas':
            rma_obj = self.env['crm.claim']
            if object_ids:
                rmas = rma_obj.browse(object_ids)
            else:
                rmas = rma_obj.search(['|', ('partner_id.web', '=', True),
                                            ('partner_id.commercial_partner_id.web', '=', True),
                                       ('date', '>=', self.start_date),
                                       ('date', '<=', self.finish_date)])
            if self.mode_export == 'export':
                for rma in rmas:
                    rma.with_delay().export_rma()
                    for line in rma.claim_line_ids:
                        line.with_delay().export_rmaproduct()
            else:
                for rma in rmas:
                    rma.with_delay().update_rma()
                    for line in rma.claim_line_ids:
                        line.with_delay().update_rmaproduct()

        elif self.type_export == 'products':
            product_obj = self.env['product.product']
            if object_ids:
                product_ids = product_obj.browse(object_ids)
            else:
                product_ids = product_obj.search([])
            if self.mode_export == 'export':
                for product in product_ids:
                    product.with_delay().export_product()
            else:
                for product in product_ids:
                    product.with_delay().update_product()
            product.web = 'published'

        elif self.type_export == 'tags':

            tag_obj = self.env['res.partner.category']
            if object_ids:
                tag_ids = tag_obj.browse(object_ids)
            else:
                tag_ids = tag_obj.search([('active', '=', True)])
            if self.mode_export == 'export':
                for tag in tag_ids:
                    tag.with_delay().export_partner_tag()
            else:
                for tag in tag_ids:
                    tag.with_delay().update_partner_tag()

        elif self.type_export == 'customer_tags_rel':
            partner_obj = self.env['res.partner']
            if object_ids:
                partner_ids = partner_obj.browse(object_ids)
            else:
                partner_ids = partner_obj.search([('is_company', '=', True),
                                                  ('web', '=', True),
                                                  ('customer', '=', True)])
            if self.mode_export == 'export':
                for partner in partner_ids:
                    for category in partner.category_id:
                        category.with_delay().export_partner_tag_rel()
            else:
                for partner in partner_ids:
                    for category in partner.category_id:
                        category.with_delay().update_partner_tag_rel()

        elif self.type_export == 'order':
            if object_ids:
                sales = self.env['sale.order'].browse(object_ids)
            else:
                partner_obj = self.env['res.partner']
                partner_ids = partner_obj.search([('is_company', '=', True),
                                                  ('web', '=', True),
                                                  ('customer', '=', True)])
                sales = self.env['sale.order'].search([('partner_id', 'child_of', partner_ids.ids),
                                                          ('state', 'in', ['done', 'progress', 'draft', 'reserve']),
                                                          ('date_order', '>=', self.start_date),
                                                          ('date_order', '<=', self.finish_date),
                                                          ('company_id', '=', 1)])
            if self.mode_export == 'export':
                for sale in sales:
                    sale.with_delay().export_order()
                    for line in sale.order_line:
                        line.with_delay().export_orderproduct()
            else:
                for sale in sales:
                    sale.with_delay().update_order()
                    for line in sale.order_line:
                        line.with_delay().update_orderproduct()

        elif self.type_export == 'rappel':
            rappel_obj = self.env['rappel']
            if object_ids:
                rappel_ids = rappel_obj.browse(object_ids)
            else:
                rappel_ids = rappel_obj.search([])
            if self.mode_export == 'export':
                for rappel in rappel_ids:
                    rappel.with_delay().export_rappel()
            else:
                for rappel in rappel_ids:
                    rappel.with_delay().update_rappel()

        elif self.type_export == 'rappelsection':
            rappel_section_obj = self.env['rappel.section']
            if object_ids:
                rappel_section_ids = rappel_section_obj.browse(object_ids)
            else:
                rappel_section_ids = rappel_section_obj.search([])
            if self.mode_export == 'export':
                for section in rappel_section_ids:
                    section.with_delay().export_rappel_section()
            else:
                for section in rappel_section_ids:
                    section.with_delay().update_rappel_section()

        elif self.type_export == 'countrystate':
            country_state_obj = self.env['res.country.state']
            if object_ids:
                country_state_ids = country_state_obj.browse(object_ids)
            else:
                country_state_ids = country_state_obj.search([])
            if self.mode_export == 'export':
                for section in country_state_ids:
                    section.with_delay().export_country_state()
            else:
                for section in country_state_ids:
                    section.with_delay().update_country_state

        elif self.type_export == 'producttag':
            product_tag_obj = self.env['product.tag']
            if object_ids:
                product_tag_ids = product_tag_obj.browse(object_ids)
            else:
                product_tag_ids = product_tag_obj.search([])
            if self.mode_export == 'export':
                for tag in product_tag_ids:
                    tag.with_delay().export_product_tag()
            else:
                for tag in product_tag_ids:
                    tag.with_delay().update_product_tag()

        elif self.type_export == 'producttagproductrel':
            product_obj = self.env['product.product']
            if object_ids:
                product_ids = product_obj.browse(object_ids)
            else:
                product_ids = product_obj.search([])

            if self.mode_export == 'export':
                for product in product_ids:
                    for tag in product.tag_ids:
                        tag.with_delay().export_product_tag_rel()

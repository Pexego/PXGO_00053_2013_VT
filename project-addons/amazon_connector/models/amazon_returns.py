from .amazon_api_request import AmazonAPIRequest
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging
import csv
import json

_logger = logging.getLogger(__name__)


class AmazonReturn(models.Model):
    _name = 'amazon.return'

    return_date = fields.Datetime(help="Date the returned product was processed at the fulfillment center")
    amazon_order_id = fields.Many2one("amazon.sale.order")
    amazon_order_name = fields.Char()
    sku = fields.Char(help="Product identifier assigned by the vendor ")
    asin = fields.Char(help="Amazon Product Number")
    amazon_sku = fields.Char(help="SKU that FBA assigns to the product")
    product_qty = fields.Float()
    fulfillment_center = fields.Char(help="Amazon fulfillment center where the returned product was processed")
    product_state = fields.Selection(
        selection=[('SELLABLE', 'Sellable'),
                   ('DAMAGED', 'Damaged'),
                   ('CUSTOMER_DAMAGED', 'Customer Damaged'),
                   ('DEFECTIVE', 'Defective'),
                   ('CARRIER_DAMAGED', 'Carrier Damaged'),
                   ('EXPIRED', 'Expired')
                   ], help="""Status of the returned product. Meaning:
                           Disposition           Description
                            SELLABLE              The unit was returned to stock and is available for purchase.

                            DAMAGED               Amazon takes responsibility for the damage. Ownership transferred to Amazon.
                                                  Amazon compensates you based on the FBA Lost and Damaged Inventory Reimbursement Policy.

                            CUSTOMER DAMAGED      The unit was returned to stock as 'unsellable.' This does not necessarily
                                                  mean that the item itself is damaged (for example, external packaging may have been opened),
                                                  but it cannot be sold again in this condition. When this happens the customer is refunded,
                                                  but the unit stays in your inventory as "unsellable." You may request to have the unit returned to you.

                            DEFECTIVE             The unit was returned to stock as "unsellable." The unit is either obviously damaged
                                                  or the customer stated that it is faulty. The customer is refunded, but the unit stays
                                                  in your inventory as 'unsellable'. You may request to have the unit returned to you.

                            CARRIER DAMAGED       Amazon takes responsibility for the damage. Ownership transferred to Amazon.
                                                  Amazon compensates you based on the FBA Lost and Damaged Inventory Reimbursement Policy.

                            EXPIRED               Units that are within 50 days of the expiration date may be set aside as 'unsellable' and eventually removed
                                                  for disposal by Amazon. Units that have been disposed will not be available for return. You may request to have
                                                  expired units returned to you if they have not been disposed of.""")

    reason = fields.Selection(
        selection=[('OTHER', 'Other'),
                   ('ORDERED_WRONG_ITEM', 'Ordered Wrong Item'),
                   ('FOUND_BETTER_PRICE', 'Found Better Price'),
                   ('NO_REASON_GIVEN', 'No Reason Given'),
                   ('QUALITY_UNACCEPTABLE', 'Quality Unacceptable'),
                   ('NOT_COMPATIBLE', 'Not Compatible'),
                   ('DAMAGED_BY_FC', 'Damaged After Arrival'),
                   ('MISSED_ESTIMATED_DELIVERY', 'Missed Estimated Delivery'),
                   ('MISSING_PARTS', 'Missing Parts'),
                   ('DAMAGED_BY_CARRIER', 'Damaged By Carrier'),
                   ('SWITCHEROO', 'Wrong Item'),
                   ('DEFECTIVE', 'Defective'),
                   ('EXTRA_ITEM', 'Extra Item'),
                   ('UNWANTED_ITEM', 'Unwanted Item'),
                   ('WARRANTY', 'Warranty'),
                   ('UNAUTHORIZED_PURCHASE', 'Unauthorized Purchase'),
                   ('UNDELIVERABLE_INSUFFICIENT_ADDRESS', 'Undeliverable Insufficient Address'),
                   ('UNDELIVERABLE_FAILED_DELIVERY_ATTEMPTS', 'Undeliverable Failed Delivery Attemps'),
                   ('UNDELIVERABLE_REFUSED', 'Undeliverable Refused'),
                   ('UNDELIVERABLE_UNKNOWN', 'Undeliverable Unknown'),
                   ('UNDELIVERABLE_UNCLAIMED', 'Undeliverable Unclaimed'),
                   ('APPAREL_TOO_SMALL', 'Apparel too Small'),
                   ('APPAREL_TOO_LARGE', 'Apparel too Large'),
                   ('APPAREL_STYLE', 'Apparel Style'),
                   ('MISORDERED', 'Misordered'),
                   ('NOT_AS_DESCRIBED', 'Not as Described'),
                   ('JEWELRY_TOO_SMALL', 'Jewelry too small'),
                   ('JEWELRY_TOO_LARGE', 'Jewelry too large'),
                   ('JEWELRY_BATTERY', 'Jewelry battery'),
                   ('JEWELRY_NO_DOCS', 'Jewelry no docs'),
                   ('JEWELRY_BAD_CLASP', 'Jewelry bad clasp'),
                   ('JEWELRY_LOOSE_STONE', 'Jewelry loose stone'),
                   ('JEWELRY_NO_CERT', 'Jewelry no cert'),
                   ('PRODUCT_NOT_SPANISH', 'Product not spanish'),
                   ('NEVER_ARRIVED', 'Never Arrived'),
                   ('PRODUCT_NOT_ITALIAN', 'Product Not Italian'),
                   ('UNDELIVERABLE_CARRIER_MISS_SORTED', 'undeliverable_carrier_miss_sorted')
                   ], help="""Brief description of the reason for the return indicated by the customer. Meanings:
                                    Reason                                     Description
                                      OTHER                                     Return option not available
                                      ORDERED_WRONG_ITEM                        I accidentally ordered the wrong item
                                      FOUND_BETTER_PRICE                        I found better prices elsewhere
                                      NO_REASON_GIVEN                           No reason--I just don't want the product any more
                                      QUALITY_UNACCEPTABLE                      Product performance/quality is not up to my expectations
                                      NOT_COMPATIBLE                            Product is not compatible with my existing system
                                      DAMAGED_BY_FC                             Product became damaged/defective after arrival
                                      MISSED_ESTIMATED_DELIVERY                 Item took too long to arrive; I don't want it any more
                                      MISSING_PARTS                             Shipment was missing items or accessories
                                      DAMAGED_BY_CARRIER                        Product was damaged/defective on arrival
                                      SWITCHEROO                                Amazon sent me the wrong item
                                      DEFECTIVE                                 Item is defective
                                      EXTRA_ITEM                                Extra item included in shipment
                                      UNWANTED_ITEM                             Unwanted Item
                                      WARRANTY                                  Item defective after arrival -- Warranty
                                      UNAUTHORIZED_PURCHASE                     Unauthorized purchase -- i.e. fraud
                                      UNDELIVERABLE_INSUFFICIENT_ADDRESS        Undeliverable; Insufficient address
                                      UNDELIVERABLE_FAILED_DELIVERY_ATTEMPTS    Undeliverable; Failed delivery attempts
                                      UNDELIVERABLE_REFUSED                     Undeliverable; Refused
                                      UNDELIVERABLE_UNKNOWN                     Undeliverable; Unknown
                                      UNDELIVERABLE_UNCLAIMED                   Undeliverable; Unclaimed
                                      APPAREL_TOO_SMALL                         Apparel; Product was too small
                                      APPAREL_TOO_LARGE                         Apparel; Product was too large
                                      APPAREL_STYLE                             Apparel; Did not like style of garment
                                      MISORDERED                                Ordered wrong style/size/color
                                      NOT_AS_DESCRIBED                          Not as described on website
                                      JEWELRY_TOO_SMALL                         Jewelry; Too small/short
                                      JEWELRY_TOO_LARGE                         Jewelry; Too large/long
                                      JEWELRY_BATTERY                           Jewelry; Battery is dead
                                      JEWELRY_NO_DOCS                           Jewelry; Missing manual/warranty
                                      JEWELRY_BAD_CLASP                         Jewelry; Broken or malfunctioning clasp
                                      JEWELRY_LOOSE_STONE                       Jewelry; Missing or loose stone
                                      JEWELRY_NO_CERT                           Jewelry; Missing promised certification
                   """)

    status = fields.Selection(
        selection=[('Unit returned to inventory', 'Unit Returned to Inventory'),
                   ('Reimbursed', 'Reimbursed'),
                   ('Pending repackaging', 'Pending Repackaging'),
                   ('Repackaged Successfully', 'Repackaged Successfully')],
        help="""A short description of the status of the customer return. Meaning:
                   Status                          Description
                     Unit Returned to Inventory      Unit has been returned to your sellable or unsellable inventory
                     Reimbursed                      A reimbursement has been approved for the unit. The unit has not been returned to your inventory
                     Pending Repackaging             Unit is in the process of being repackaged.
                     Repackaged Successfully         Unit has been repackaged successfully and returned to your sellable inventory.""")
    lpn = fields.Char(
        help="Unique serial number that identifies a specific product throughout the Amazon fulfillment process.")

    customer_comments = fields.Text(
        help="When available, comments submitted by customers regarding the reason for the return are provided.")

    product_name_amazon = fields.Char(help="The name of the product as it appears on Amazon")

    deposit_ids = fields.One2many('stock.deposit', 'amazon_return_id')

    product_id = fields.Many2one('product.product')

    return_state = fields.Selection([
        ('error', 'Error'),
        ('read', 'Read'),
        ('done', 'Done'),
    ], string='Return Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='error')

    error_message = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = "%s - %s "%(record.amazon_order_name, record.product_id.default_code)
            res.append((record.id,name))
        return res

    def cron_read_amazon_returns(self, data_start_time=False, data_end_time=False):
        amazon_time_rate_limit = float(self.env['ir.config_parameter'].sudo().get_param('amazon.time.rate.limit'))
        amazon_api = AmazonAPIRequest(self.env.user.company_id, amazon_time_rate_limit)

        if not data_start_time:
            data_start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not data_end_time:
            data_end_time = datetime.utcnow().isoformat()
        report_created = amazon_api.create_report("GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA",
                                                       data_start_time,
                                                       data_end_time)
        report = amazon_api.get_report(report_created.get('reportId'))
        report_document = amazon_api.get_report_document(report.get('reportDocumentId'))
        document_lines = report_document.get('document').split("\n")
        reader = csv.DictReader(document_lines, delimiter="\t")
        data = list(reader)
        info = json.loads(json.dumps(data))
        returns_with_errors = self.env['amazon.return']

        for row in info:
            amazon_order_name = row.get('order-id')
            product_asin = row.get('asin')
            date = row.get('return-date')
            qty = row.get('quantity')
            a_return = self.env['amazon.return'].search([('amazon_order_name', '=', amazon_order_name),
                                                         ('asin', '=', product_asin),
                                                         ('return_date', '=', date), ('product_qty', '=', qty)])
            if a_return:
                continue
            amazon_return = self.env['amazon.return'].create({'return_date': date,
                                                              'amazon_order_id': self.env[
                                                                  'amazon.sale.order'].search(
                                                                  [('name', '=', amazon_order_name)]).id,
                                                              'sku': row.get('sku'),
                                                              'asin': product_asin,
                                                              'product_qty': qty,
                                                              'amazon_sku': row.get('fnsku'),
                                                              'fulfillment_center': row.get(
                                                                  'fulfillment-center-id'),
                                                              'product_state': row.get('detailed-disposition'),
                                                              'reason': row.get('reason'),
                                                              'status': row.get('status'),
                                                              'lpn': row.get('license-plate-number'),
                                                              'product_name_amazon': row.get('product-name'),
                                                              'customer_comments': row.get('customer-comments'),
                                                              'product_id': self.env['product.product'].search(
                                                                  [('asin_code', '=', product_asin)]).id,
                                                              'amazon_order_name': amazon_order_name
                                                              })
            error = ""
            if not amazon_return.amazon_order_id:
                error += _("Unable to find amazon order for name '%s' \n" % amazon_order_name)
            if not amazon_return.product_id:
                error += _("Unable to find product with this ASIN '%s'\n" % product_asin)
            if error:
                amazon_return.error_message = error
                returns_with_errors |= amazon_return
                continue
            if amazon_return.product_state == 'SELLABLE':
                deposit = amazon_return.amazon_order_id.deposits.filtered(
                    lambda dep: dep.product_id == amazon_return.product_id and dep.state == 'invoiced')

                if not deposit:
                    error += _("Unable to find a deposit for this order")
                    amazon_return.error_message = error
                    returns_with_errors |= amazon_return
                    continue
                qty_deposit = sum(deposit.mapped('product_uom_qty'))
                if qty_deposit < amazon_return.product_qty:
                    error += _("There is no enough qty in deposit for this return")
                    amazon_return.error_message = error
                    returns_with_errors |= amazon_return
                    continue
                else:
                    amazon_return.return_state = 'read'
                    deposits_to_return = self.env['stock.deposit']
                    qty_to_return = amazon_return.product_qty
                    for d in deposit:
                        if qty_to_return <= 0:
                            break
                        if d.product_uom_qty <= qty_to_return:
                            deposits_to_return |= d
                            qty_to_return -= d.product_uom_qty
                        else:
                            new_deposit = d.copy()
                            new_deposit.write({'product_uom_qty': qty_to_return})
                            d.write({'product_uom_qty': d.product_uom_qty - qty_to_return})
                            deposits_to_return |= new_deposit
                            qty_to_return -= new_deposit.product_uom_qty

                    deposits_to_return.with_context({'client_warehouse': True}).return_deposit()
                    amazon_return.deposit_ids = [(6, 0, deposits_to_return.ids)]
                    for d in deposits_to_return:
                        copy = d.copy({'amazon_order_id': False,
                                       'invoice_id': False,
                                       'state': 'draft',
                                       'sale_move_id': False,
                                       'loss_move_id': False,
                                       'amazon_return_id': False,
                                       'return_picking_id': False,
                                       'original_deposit_id': d.id})
                        copy.write({'product_uom_qty': d.product_uom_qty})

                    amazon_return.return_state = 'done'
            else:
                amazon_return.return_state = 'read'

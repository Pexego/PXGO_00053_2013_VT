from odoo import models, fields, api, exceptions, _

from odoo.exceptions import UserError
from requests import request


class CustomizationLine(models.TransientModel):
    _name = 'customization.line'

    product_id = fields.Many2one('product.product', 'Product', readonly=1)
    qty = fields.Float('Selected quantity', default=0)
    product_qty = fields.Float('Quantity Available', readonly=1)
    wizard_id = fields.Many2one('customization.wizard', 'wizard')
    sale_line_id = fields.Many2one('sale.order.line')
    erase_logo = fields.Boolean()
    type_ids = fields.Many2many('customization.type')
    product_erase_logo = fields.Boolean()
    sale_product_id = fields.Many2one('product.product')
    original_product_id = fields.Many2one('product.product')

    @staticmethod
    def create_wizard_line(product, line, qty):
        if qty:
            return {'qty': qty,
                    'product_qty': qty,
                    'product_id': product.id,
                    'original_product_id': product.id,
                    'sale_line_id': line.id,
                    'type_ids': None,
                    'product_erase_logo': product.erase_logo,
                    'sale_product_id': line.product_id.id
                    }
        return False


class CustomizationWizard(models.TransientModel):
    _name = 'customization.wizard'

    order_id = fields.Many2one('sale.order',
                               default=lambda self: self.env['sale.order'].browse(self.env.context.get('active_ids')))

    @api.model
    def _get_lines(self):
        wiz_lines = []
        for line in self.env['sale.order'].browse(self.env.context.get('active_ids')).order_line.filtered(
                lambda l: (l.product_id.customizable or l.product_id.erase_logo) and not l.deposit
                          and l.product_id.categ_id.with_context(lang='es_ES').name != 'Portes' and l.price_unit >= 0):
            if line.product_id.bom_ids:
                for bom in line.product_id.bom_ids[0].bom_line_ids.filtered(
                        lambda b: b.product_id.customizable or b.product_id.erase_logo):
                    new_line = self.env['customization.line'].create_wizard_line(bom.product_id, line,
                                                                                 line.product_qty * bom.product_qty)
                    if new_line:
                        wiz_lines.append(new_line)
            else:
                new_line = self.env['customization.line'].create_wizard_line(line.product_id, line, line.product_qty)
                if new_line:
                    wiz_lines.append(new_line)
        return wiz_lines

    customization_line = fields.One2many('customization.line',
                                         'wizard_id', 'lines', default=_get_lines)
    type_ids = fields.Many2many('customization.type', required=1)

    comments = fields.Text('Comments')

    notify_users = fields.Many2many('res.users', default=lambda self: [
        (6, 0, [self.env['sale.order'].browse(self.env.context.get('active_ids')).user_id.id])])

    def action_create(self):
        lines = []
        if self.order_id.state != 'reserve':
            raise UserError(_("you can't create a customization of a done order"))

        customization = self.env['kitchen.customization'].sudo().create({'partner_id': self.order_id.partner_id.id,
                                                                         'order_id': self.order_id.id,
                                                                         'commercial_id': self.order_id.user_id.id,
                                                                         'comments': self.comments,
                                                                         'notify_users': [
                                                                             (6, 0, self.notify_users.ids)],
                                                                         'notify_sales_team': self.notify_sales_team
                                                                         })
        old_previews = ""
        products_error_state = {}
        partner_ref = self.order_id.partner_id.ref
        previews_url = self.env['ir.config_parameter'].sudo().get_param('kitchen.previews.url')

        for line in self.customization_line:
            qty = line.qty
            if not line.type_ids and not line.product_erase_logo:
                raise UserError(_(
                    "You can't create a customization without a customization type: %s") % line.original_product_id.default_code)
            if not line.erase_logo and line.product_erase_logo:
                raise UserError(
                    _("You can't create a customization without check erase logo option of this product : %s") % line.original_product_id.default_code)
            line_type_ids = line.type_ids
            product_type_ids = line.original_product_id.customization_type_ids
            if line_type_ids - product_type_ids:
                raise UserError(_(
                    "You can't create a customization with different customization types (%s) than the product %s has %s") % (
                                    line.original_product_id.default_code, line_type_ids.mapped('name'),
                                    product_type_ids.mapped('name')))
            sale_qty = line.sale_line_id.product_qty
            if line.sale_line_id.product_id != line.original_product_id:
                bom_line = line.sale_line_id.product_id.bom_ids[0].bom_line_ids.filtered(
                    lambda b: b.product_id == line.original_product_id)
                sale_qty *= bom_line.product_qty
            if qty < 0:
                raise UserError(_(
                    "You can't create a customization with a quantity of less than zero of this product: %s") % line.original_product_id.default_code)
            elif sale_qty < qty:
                raise UserError(_(
                    "You can't create a customization with a bigger quantity of the product than what appears in the order: %s") % line.original_product_id.default_code)
            elif qty > 0:
                product_previews = []
                product_old_previews = []
                previews = []
                if line.mapped('type_ids').filtered(lambda t: t.preview):
                    req = request('POST', previews_url+'GetCreatedPreview?idOdooClient=%s&reference=%s' % (partner_ref,line.original_product_id.default_code),
                                  verify=False)
                    if req.status_code != 200:
                        raise UserError(_("There are no previews for this partner and this product %s") % line.original_product_id.default_code)
                    previews = req.json()
                for prev in previews:
                    state = prev.get('status', False)
                    if state == 'Approved':
                        product_previews.append(prev)
                    elif state == 'OldPreview':
                        product_old_previews.append(prev)
                    else:
                        products_error_state[line.original_product_id.default_code] = state

                    if product_previews and line.original_product_id.default_code in products_error_state:
                        del products_error_state[line.original_product_id.default_code]
                if not product_previews and product_old_previews:
                    product_previews = product_old_previews
                    old_previews += line.original_product_id.default_code
                    if line.original_product_id.default_code in products_error_state:
                        del products_error_state[line.original_product_id.default_code]
                if not products_error_state:
                    lines += customization.create_line(line.original_product_id, qty, line, product_previews)
        if products_error_state:
            raise UserError(_("There are no active previews of these products: %s" %str(products_error_state)))
        if lines:
            if old_previews:
                template = self.env.ref('kitchen.send_mail_old_previews')
                template.with_context({'lang': 'es_ES', 'old_previews': old_previews}).send_mail(customization.id)
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('kitchen.kitchen_customization_form').id,
                'res_model': 'kitchen.customization',
                'res_id': customization.id,
                'type': 'ir.actions.act_window',
            }
        else:
            raise UserError(_("You cannot create an empty customization"))

    notify_sales_team = fields.Boolean()

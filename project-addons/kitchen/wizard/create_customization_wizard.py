from odoo import models, fields, api, exceptions, _

from odoo.exceptions import UserError


class CustomizationLine(models.TransientModel):
    _name = 'customization.line'

    product_id = fields.Many2one('product.product', 'Product', readonly=1)
    qty = fields.Float('Selected quantity', default=0)
    product_qty = fields.Float('Quantity Available', readonly=1)
    wizard_id = fields.Many2one('customization.wizard', 'wizard')
    sale_line_id = fields.Many2one('sale.order.line')
    erase_logo = fields.Boolean()
    type_ids = fields.Many2many('customization.type')
    product_erase_logo = fields.Boolean(related="sale_line_id.product_id.erase_logo")


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
            new_line = {'product_id': line.product_id.id,
                        'sale_line_id': line.id,
                        'type_ids': None,
                        'product_erase_logo':line.product_id.erase_logo}
            if line.product_qty:
                new_line.update({'qty': line.product_qty,
                                 'product_qty': line.product_qty})
            if new_line.get('product_qty'):
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
                                                                  'notify_users': [(6, 0, self.notify_users.ids)],
                                                                  'notify_sales_team': self.notify_sales_team
                                                                  })
        for line in self.customization_line:
            qty = line.qty
            if not line.type_ids and not line.product_erase_logo:
                raise UserError(_(
                    "You can't create a customization without a customization type: %s") % line.sale_line_id.product_id.default_code)
            if not line.erase_logo and line.product_erase_logo:
                raise UserError(_("You can't create a customization without check erase logo option of this product : %s") % line.sale_line_id.product_id.default_code)
            line_type_ids = line.type_ids
            product_type_ids = line.sale_line_id.product_id.customization_type_ids
            if line_type_ids - product_type_ids:
                raise UserError(_(
                    "You can't create a customization with different customization types (%s) than the product %s has %s") % (line.sale_line_id.product_id.default_code,line_type_ids.mapped('name'),product_type_ids.mapped('name')))
            if qty < 0:
                raise UserError(_(
                    "You can't create a customization with a quantity of less than zero of this product: %s") % line.sale_line_id.product_id.default_code)
            elif line.sale_line_id.product_qty < qty:
                raise UserError(_(
                    "You can't create a customization with a bigger quantity of the product than what appears in the order: %s") % line.sale_line_id.product_id.default_code)
            elif qty > 0:
                new_line = {
                    'product_id': line.sale_line_id.product_id.id,
                    'product_qty': line.qty,
                    'customization_id': customization.id,
                    'sale_line_id': line.sale_line_id.id,
                    'erase_logo': line.erase_logo,
                    'type_ids': [(6, 0, line.type_ids.ids)]
                }
                lines += self.env['kitchen.customization.line'].create(new_line)
        if lines:
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

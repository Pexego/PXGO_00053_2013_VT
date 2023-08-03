from odoo import models, fields, api, exceptions, _

from odoo.exceptions import UserError
from requests import post,get,codes
import base64

class KitchenCustomizationPreviewWizard(models.TransientModel):
    _name = 'kitchen.customization.preview.wizard'

    name = fields.Char()
    photo = fields.Binary(attachment=True)
    url = fields.Char()
    status = fields.Char()
    sale_line_id = fields.Many2one("sale.order.line")


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
    preview_selector = fields.Many2one('kitchen.customization.preview.wizard')
    preview_ids = fields.Many2many('kitchen.customization.preview.wizard')
    photo = fields.Binary(related="preview_selector.photo")
    url = fields.Char(related="preview_selector.url")
    preview_error = fields.Boolean()

    def create_previews(self, previews, api_headers, sale_line):
        """
            Create previews for the sale_line given
        :param previews: json list with preview values
        :param api_headers: header for calling the rubrika api
        :param sale_line: line of the sale order
        :return: kitchen.customization.preview.wizard list created
        """
        new_previews = self.env['kitchen.customization.preview.wizard']
        for count, preview in enumerate(previews):
            if preview.get('status') == 'OldPreview':
                new_preview = self.env['kitchen.customization.preview.wizard'].create(
                    {'name': _('OldPreview - Go to Sharepoint'),
                     'url': 'The previews are on Sharepoint', 'status': 'OldPreview',
                     'sale_line_id':sale_line.id})
            else:
                photo = base64.b64encode(get(preview.get('logo'),headers=api_headers).content)
                new_preview = self.env['kitchen.customization.preview.wizard'].create(
                    {'photo': photo, 'name': 'Preview %s' % str(count + 1),
                     'url': preview.get('urlView'), 'status': preview.get('status'),'sale_line_id':sale_line.id})
            new_previews |= new_preview
        return new_previews

    @api.onchange("type_ids")
    def onchange_type_ids(self):
        preview_types = self.type_ids.filtered(lambda t: t.preview)
        if not self.sale_line_id.order_id.skip_checking_previews and preview_types and self.preview_ids:
            self.preview_selector = self.preview_ids[0]
        elif not preview_types:
            self.preview_selector = False

    def create_wizard_line(self, product, line, qty):
        dicc = {}
        if qty:
            dicc = {'qty': qty,
                    'product_qty': qty,
                    'product_id': product.id,
                    'original_product_id': product.id,
                    'sale_line_id': line.id,
                    'type_ids': [(6,0, product.customization_type_ids.ids)],
                    'product_erase_logo': product.erase_logo,
                    'sale_product_id': line.product_id.id
                    }
            preview_types = product.customization_type_ids.filtered(lambda t: t.preview)
            if not line.order_id.skip_checking_previews and preview_types:
                previews_url, headers = self.env['kitchen.customization']._get_previews_params()
                req = post(previews_url + 'GetCreatedPreview?idOdooClient=%s&reference=%s' % (
                    line.order_id.partner_id.ref, product.default_code), headers=headers)
                if req.status_code != codes.ok or len(req.json()) == 0:
                    dicc['preview_error'] = True
                    return dicc
                previews = req.json()
                new_previews = [x for x in previews if x.get('status') in ['Approved', 'OldPreview']]
                if new_previews:
                    previews_created = self.create_previews(new_previews, headers, line)
                    if previews_created:
                        dicc.update({'preview_selector':previews_created[0],
                                     'photo': previews_created[0].photo,
                                     'preview_ids': [(6,0,previews_created.ids)]})

        return dicc


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
            old_previews = self.env['kitchen.customization.preview.wizard'].search(
                [('sale_line_id', '=', line.id), ('status', '!=', 'used_to_create_preview')])
            old_previews.sudo().unlink()
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
    @api.depends("customization_line","customization_line.type_ids")
    def _get_errors(self):
        """ Calculate the products that do not have a preview in rubrika"""
        for wiz in self:
            errors = ''
            products = ", ".join(line.original_product_id.default_code % line for line in wiz.customization_line if
                                 line.preview_error and line.type_ids.filtered(lambda t: t.preview))
            if products:
                errors += _("There are no previews for this partner and these products: %s") % products
            wiz.errors = errors

    errors = fields.Text(compute=_get_errors, store=True)

    comments = fields.Text('Comments')

    notify_users = fields.Many2many('res.users', default=lambda self: [
        (6, 0, [self.env['sale.order'].browse(self.env.context.get('active_ids')).user_id.id])])

    def _get_old_previews(self):
        """
            Gets the previews of the customization lines that are in the old state
        :return: old previews list
        """
        return self.customization_line.mapped('preview_selector').filtered(lambda p: p.name == "OldPreview - Go to Sharepoint")

    def action_create(self):
        lines = self.env['customization.line']
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
        for line in self.customization_line:
            qty = line.qty
            if not line.type_ids and not line.product_erase_logo:
                raise UserError(_(
                    "You can't create a customization without a customization type: %s") % line.original_product_id.default_code)
            if not line.erase_logo and line.product_erase_logo:
                raise UserError(
                    _("You can't create a customization without check erase logo option of this product : %s") % line.original_product_id.default_code)
            if not self.order_id.skip_checking_previews and line.type_ids.filtered(lambda t:t.preview):
                if line.preview_error:
                    raise UserError(
                        _("There are no previews for this partner and this product %s") % line.original_product_id.default_code)
                if not line.preview_selector:
                    raise UserError(
                        _("You can't create a customization with no preview selected : %s") % line.original_product_id.default_code)
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
                lines += customization.create_line(line.original_product_id, qty, line)
        if lines:
            old_previews = self._get_old_previews()
            if old_previews:
                template = self.env.ref('kitchen.send_mail_old_previews')
                template.with_context({'lang': 'es_ES', 'old_previews': old_previews.mapped(
                    'sale_line_id.product_id.default_code')}).send_mail(customization.id)
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

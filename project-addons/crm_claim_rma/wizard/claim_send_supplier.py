##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, api, exceptions, _


class ClaimSendSupplier(models.TransientModel):

    _name = "claim.send.supplier"

    @api.multi
    def create_lines(self):
        if not self.env.context.get('active_ids', False):
            return {'type': 'ir.actions.act_window_close'}
        wh_obj = self.env['stock.warehouse']
        partner_obj = self.env['res.partner']
        claim_obj = self.env['crm.claim']
        wh_ids = wh_obj.search([('company_id', '=',
                                 self.env.user.company_id.id)])
        supplier_type = self.env.ref('crm_claim_type.crm_claim_type_supplier').id

        lines = self.env['claim.line'].browse(self.env.context['active_ids'])
        supplier_lines = {}
        # Se agrupan las lineas por proveedor.
        for line in lines:
            if line.move_in_customer_state != 'done':
                continue
            if line.supplier_id.id not in supplier_lines.keys():
                supplier_lines[line.supplier_id.id] = []
            supplier_lines[line.supplier_id.id].append(line)
        if supplier_lines.get(False, False):
            raise exceptions.except_orm(
                _('Supplier error'),
                _('Some of the selected lines not have supplier.\nLines: ') +
                '%s, ' * len(supplier_lines[False]) %
                tuple(x.name for x in supplier_lines[False]))
        claims_used = []
        for supplier in partner_obj.browse(supplier_lines.keys()):
            claims_created = claim_obj.search(
                [('partner_id', '=', supplier.id),
                 ('claim_type', '=', supplier_type),
                 ('stage_id.closed', '=', False)])
            if claims_created:
                claim = claims_created[0]
            else:
                claim_vals = {
                    'name': supplier.name,
                    'user_id': self.env.user.id,
                    'claim_type': supplier_type,
                    'partner_id': supplier.id,
                    'partner_phone': supplier.phone,
                    'email_from': supplier.email,
                    'warehouse_id': wh_ids and wh_ids[0].id,
                }
                claim = claim_obj.create(claim_vals)
            claims_used.append(claim.id)
            for line in supplier_lines[supplier.id]:
                new_line = line.copy({'claim_id': claim.id,
                                      'equivalent_product_id': False,
                                      'move_in_customer_id': False,
                                      'move_out_customer_id': False,
                                      'repair_id': False,
                                      'original_line_id': line.id})
                line.supplier_line_id = new_line
        # return {'type': 'ir.actions.act_window_close'}

        res = self.env.ref('crm_claim_rma.crm_case_categ_claim_supplier')
        action = res.read()[0]
        action['domain'] = "[('id','in', " + str(claims_used) + ")]"
        return action
        """return {
            'name': 'Claim',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': [res.id],
            'res_model': 'crm.claim',
            'context': "{}",
            'domain': "[('id', 'in', " + str(claims_used) + ")]",
            'type': 'ir.actions.act_window',
        }"""

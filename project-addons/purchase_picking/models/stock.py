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

from odoo import models, fields, api, _, exceptions
from datetime import datetime, timedelta


class StockContainer(models.Model):

    _name = 'stock.container'
    type = fields.Selection([
        ('air', 'Air'),
        ('sea', 'Sea'),
        ('road', 'Road'),
    ])
    dimensions = fields.Char(string="CBM/KG", help="Dimensions")
    container_type = fields.Char(string="Container type", help="Container type")
    cubic_meters = fields.Float(string="CBM", help="Cubic Meters")
    kilograms = fields.Float(string="KG", help="Kilograms")
    ready = fields.Date(string="Ready", help="Ready merchandise date")
    etd = fields.Date(string="ETD", help="Date of departure of transport")
    eta = fields.Date(string="ETA", help="Arrival date at port / destination")
    notes_purchases = fields.Char(string="Notes", help="Purchases notes")
    notes_warehouse = fields.Text(string="Warehouse notes", help="Warehouse notes")
    conf = fields.Boolean(string="Conf", help="Confirmed")
    telex = fields.Selection([
        ('asked', 'Asked'),
        ('claimed', 'Claimed'),
        ('received', 'Received')
    ])
    arrived = fields.Boolean(string="Arrived", help="Arrived", compute="_set_arrived", store=True)
    cost = fields.Float(sting="Cost")
    n_ref = fields.Integer(string="Nº ref", store=False, compute="_get_ref")
    forwarder = fields.Many2one('res.partner', domain="['&',('supplier','=',True),('forwarder','=',True)]",
                                string="FWDR")
    forwarder_comercial = fields.Char(related="forwarder.comercial", store=False, string="FWDR")
    incoterm = fields.Many2one('stock.incoterms', string='Incoterm', ondelete="restrict")
    destination_port = fields.Many2one('stock.container.port', string='NAV/PTO', ondelete="restrict")
    status = fields.Many2one('stock.container.status', string='Status', help='For more information click on the status', ondelete="restrict")
    customs_channel = fields.Selection([
        ('red', '🔴 - Red'),
        ('orange', '🟠 - Orange'),
        ('yellow', '🟡 - Yellow'),
        ('green', '🟢 - Green')
    ],string="Customs Channel")
    ctns = fields.Char(string="Ctns")
    departure = fields.Boolean(string="Departure", help="Transport departure")
    pickings_warehouse = fields.Char(string="Pickings", store=False, compute="_get_picking_ids")
    set_eta = fields.Boolean(string="set_eta", help="Set eta", default=0, compute="_set_eta", store=True)
    set_date_exp = fields.Boolean(string="set_date_expected", help="Set date expected", default=0, compute="_set_date_exp", store=True)
    incidences = fields.Boolean("Incidences")

    @api.onchange("type")
    def onchange_locations(self):
        for container in self:
            if container.type in ['air', 'road']:
                container.telex = 'received'

    @api.multi
    @api.depends('eta')
    def _set_eta(self):
        for container in self:
            if container.eta:
                container.set_eta = True

    @api.multi
    @api.depends('date_expected')
    def _set_date_exp(self):
        for container in self:
            if container.date_expected:
                container.set_date_exp = True

    @api.multi
    @api.depends('move_ids.state')
    def _set_arrived(self):
        for container in self:
            container.arrived = container.move_ids and all(move_state in ['done', 'cancel'] for move_state in
                                                           container.move_ids.mapped('state'))

    @api.multi
    def _set_date_expected(self):
        for container in self:
            if container.move_ids:
                date_expected = container.date_expected
                container.move_ids.write({'date_expected': date_expected})
                picking_ids = container.move_ids.mapped('picking_id')
                if picking_ids:
                    picking_ids.write({'scheduled_date': date_expected})
        return True

    @api.multi
    @api.depends('move_ids.picking_id.scheduled_date')
    def _get_date_expected(self):
        for container in self:
            if container.move_ids:
                max_date = max(container.move_ids.mapped('date_expected') or fields.Date.today())
                if max_date:
                    container.move_ids.write({'date_expected': max_date})
                    container.date_expected = max_date

    @api.multi
    def _get_picking_ids(self):
        for container in self:
            pickings = container.move_ids.mapped('picking_id')
            container.picking_ids = pickings
            pickings_warehouse_obj = pickings[:2]
            pickings_warehouse = ', '.join(pickings_warehouse_obj.mapped('name'))
            if len(pickings) > 2:
                pickings_warehouse += "..."
            container.pickings_warehouse = pickings_warehouse

    @api.multi
    def _get_ref(self):
        for container in self:
            res = []
            n_ref = 0
            for line in container.move_ids:
                if line.product_id.id not in res:
                    res.append(line.product_id.id)
                    n_ref += 1
            container.n_ref = n_ref

    @api.multi
    def _get_responsible(self):
        for container in self:
            responsible = ''
            if container.picking_id:
                responsible = container.picking_id.commercial
            elif container.origin:
                responsible = self.env['sale.order'].search([('name', '=', container.origin)]).user_id
            container.user_id = responsible

    @api.depends('conf', 'date_expected', 'eta')
    def _get_order_date(self):
        for container in self:
            if container.conf:
                container.date_to_order = container.date_expected
            else:
                container.date_to_order = container.eta

    name = fields.Char("Container Ref.", required=True)
    date_expected = fields.Date("Date expected", compute='_get_date_expected', inverse='_set_date_expected',
                                    store=True, readonly=False, required=False)
    move_ids = fields.One2many("stock.move", "container_id", "Moves",
                               readonly=True, copy=False, domain=[('state', '!=', 'cancel')])
    picking_ids = fields.One2many('stock.picking', "container_ids", compute='_get_picking_ids', string='Pickings', readonly=True)

    user_id = fields.Many2one(string='Responsible', compute='_get_responsible')
    company_id = fields.Many2one("res.company", "Company", required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('stock.container'))

    import_sheet_ids = fields.One2many(
        "import.sheet",
        "container_id",
        string="Import Sheets",
        required=True
    )

    date_to_order = fields.Date(compute='_get_order_date', store=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Container name must be unique')
    ]


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    usage = fields.Char(compute='_get_usage')
    shipping_identifier = fields.Char('Shipping identifier', size=64)
    temp = fields.Boolean("Temp.")
    container_ids = fields.Many2many('stock.container', string='Containers', compute='_get_containers')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not res.shipping_identifier and res.container_ids:
            res.shipping_identifier = ''.join(res.container_ids.mapped('name'))
        return res

    @api.multi
    def _get_usage(self):
        for pick in self:
            if not pick.location_id:
                pick.usage = pick.picking_type_id.default_location_src_id
            else:
                pick.usage = pick.location_id.usage

    @api.multi
    def action_cancel(self):
        for pick in self:
            if pick.temp:
                for move in pick.move_lines:
                    if move.state == "assigned":
                        move._do_unreserve()
                    move.state = "draft"
                    move.picking_id = False
                pick.state = "cancel"

        return super(StockPicking, self).action_cancel()

    @api.multi
    def _get_containers(self):
        for picking in self:
            res = []
            for move in picking.move_lines:
                if move.container_id:
                    res.append(move.container_id.id)
            picking.container_ids = res

    @api.onchange("location_id","location_dest_id")
    def onchange_locations(self):
        for picking in self:
            for move in picking.move_lines:
                move.location_id=picking.location_id
                move.location_dest_id = picking.location_dest_id


class StockMove(models.Model):

    _inherit = 'stock.move'

    partner_id = fields.Many2one('res.partner', 'Partner')
    container_id = fields.Many2one('stock.container', "Container")
    subtotal_price = fields.Float('Subtotal', compute='_calc_subtotal')
    partner_ref = fields.Char(related='purchase_line_id.order_id.partner_ref')
    virtual_stock_conservative = fields.Float(related="product_id.virtual_stock_conservative")
    ref_manufacturer = fields.Char(related="product_id.ref_manufacturer", String="Ref. Manufacturer")

    @api.multi
    def _calc_subtotal(self):
        for move in self:
            move.subtotal_price = move.price_unit * move.product_uom_qty

    @api.multi
    def write(self, vals):
        for move in self:
            if 'product_uom_qty' in vals \
                    and self.purchase_line_id \
                    and self.picking_id \
                    and 'origin' not in vals\
                    and not move._context.get('accept_ready_qty'):
                if move.product_uom_qty > vals['product_uom_qty'] > 0:
                    if not (move.location_id.name == "Vendor's deposit"
                            and move.location_dest_id.id == self.env.ref('stock.stock_location_stock').id):
                        move.copy({'picking_id': False, 'product_uom_qty': move.product_uom_qty - vals['product_uom_qty']})
                elif vals['product_uom_qty'] > move.product_uom_qty:
                    raise exceptions.Warning(_('Impossible to increase the quantity'))
                elif vals['product_uom_qty'] == 0:
                    raise exceptions.Warning(_('Impossible to decrease the quantity to 0'))
        res = super(StockMove, self).write(vals)
        for move in self:
            move.refresh()
            if move.picking_type_id.code == 'incoming':
                if vals.get('date_expected', False):
                    self.env['stock.reservation'].\
                        reassign_reservation_dates(move.product_id)
            if vals.get('container_id', False):
                container = self.env["stock.container"].\
                    browse(vals['container_id'])
                move.date_expected = container.date_expected
        return res

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        if (vals.get('picking_type_id', False) and
                res.picking_type_id.code == 'incoming'):
            if 'date_expected' in vals.keys():
                self.env['stock.reservation'].\
                    reassign_reservation_dates(res.product_id)
        if not res.partner_id and res.picking_id.partner_id == \
                self.env.ref('purchase_picking.partner_multisupplier'):
            raise exceptions.Warning(
                _('Partner error'), _('Set the partner in the created moves'))
        return res


class StockReservation(models.Model):
    _inherit = 'stock.reservation'

    @api.model
    def reassign_reservation_dates(self, product_id):
        product_uom = product_id.uom_id
        reservations = self.search(
            [('product_id', '=', product_id.id),
             ('state', 'in', ['confirmed', 'partially_available'])])
        moves = self.env['stock.move'].search(
            [('product_id', '=', product_id.id),
             ('state', '=', 'draft'),
             ('picking_type_id.code', '=', u'incoming')],
            order='date_expected')
        reservation_index = 0

        reservation_used = 0
        for move in moves:
            qty_used = 0
            product_uom_qty = move.product_uom._compute_quantity(move.product_uom_qty, product_uom)
            while qty_used < product_uom_qty and reservation_index < len(reservations):
                reservation = reservations[reservation_index]
                reservation_qty = reservation.product_uom_qty - reservation.reserved_availability
                reservation_qty = move.product_uom._compute_quantity(reservation_qty, product_uom)
                if reservation_qty - reservation_used <= product_uom_qty - qty_used:
                    reservation.date_planned = move.date_expected
                    reservation_index += 1
                else:
                    reservation_used += product_uom_qty - qty_used
                    break
                qty_used += reservation_qty - reservation_used
                reservation_used = 0
        while reservation_index < len(reservations):
            reservations[reservation_index].date_planned = False
            reservation_index += 1

    @api.multi
    def reassign(self):
        res = super(StockReservation, self).reassign()
        for reservation in self:
            reservation.reassign_reservation_dates(reservation.product_id)
        return res


class StockContainerDestinationPort(models.Model):
    _name = 'stock.container.port'
    _rec_name = 'port_code'
    _description = "destination port for containers (shipping company/port)"
    active = fields.Boolean('Active', default=True)
    port_code = fields.Char('Code', required=True)
    port_desc = fields.Text('Description', help="To give more information about the destination port")


class StockContainerStatus(models.Model):
    _name = 'stock.container.status'
    _description = "delivery Status"
    _rec_name = 'status_code'
    active = fields.Boolean('Active', default=True)
    status_name = fields.Char('Status name', required=True)
    status_code = fields.Char('Code', required=True)
    status_desc = fields.Text('Description', help="To give more information about the shipping status")


class StockIncoterms(models.Model):

    _inherit = "stock.incoterms"

    code = fields.Char('Code', size=8)

    @api.multi
    def name_get(self):
        result = []
        orig_name = dict(super(StockIncoterms, self).name_get())
        for line in self:
            name = orig_name[line.id]
            if self.env.context.get('incoterm_code', True):
                name = line.code
            result.append((line.id, name))
        return result


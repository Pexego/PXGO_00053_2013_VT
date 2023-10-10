from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests


class StockPickingVstock(models.Model):
    _name = 'stock.picking.vstock'

    '''Este modelo se ha creado para evitar escribir el albarán con los
    datos de vstock y que vstock vuelva a leerlo, ocasionando problemas.'''

    state_papeur = fields.Selection([('notified', 'Notified'), ('urgent', 'Urgent'), ('done', 'Done')],
                                    string="Notified")
    id_vstock = fields.Char()
    state_vstock = fields.Char()
    user_vstock = fields.Char()
    last_date_vstock = fields.Datetime(default=fields.Datetime.now)
    date_done_vstock = fields.Datetime()
    picking_id = fields.Many2one('stock.picking')

    @api.multi
    def create_rpc(self, vals):
        return self.create(vals)


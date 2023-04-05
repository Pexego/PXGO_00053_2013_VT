# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import datetime


class StockLandedCost(models.Model):

    _inherit = 'stock.landed.cost'
    _order = 'write_date desc'

    account_journal_id = fields.\
        Many2one(default=lambda self: self.env['account.journal'].
                 search([('code', '=', 'APUR')]))

    container_ids = fields.Many2many('stock.container', string='Containers',
                                     compute='_get_container', inverse='_set_pickings',
                                     search='_search_container')
    forwarder_invoice = fields.Char(string='Forwarder Invoice', required=True)

    import_sheet_id = fields.Many2one('import.sheet', string='Import sheet')

    @api.multi
    def _get_container(self):
        move_obj = self.env['stock.move']
        for cost in self:
            res = []
            for picking_id in cost.picking_ids:
                move_id = move_obj.search([('picking_id', '=', picking_id.id),
                                           ('container_id', '!=', False)],
                                          limit=1)
                res.append(move_id.container_id.id)

            cost.container_ids = res

    @api.multi
    def _set_pickings(self):
        for cost in self:
            if not cost.picking_ids:
                res = []
                for container in cost.container_ids:
                    for picking in container.picking_ids:
                        res.append(picking.id)
                cost.picking_ids = res

    @api.model
    def _search_container(self, operator, value):
        moves = self.env['stock.move'].search([('container_id.name', operator, value)])
        pickings = moves.mapped('picking_id.id')
        return[('picking_ids', 'in', pickings)]

    @api.multi
    def check_lines_hscode(self, vals):
        product = self.env['product.product'].browse(vals.get('product_id'))
        if product and not product.hs_code_id:
            raise UserError(_('Not all the products have HS Code: %s') % product.default_code)

    @api.multi
    def check_lines_weight(self, vals):
        product = self.env['product.product'].browse(vals.get('product_id'))
        if product and vals.get('weight', 0.0) == 0:
            raise UserError(_('Not all the products have weight: %s') % product.default_code)

    @staticmethod
    def check_if_all_lines_have_split_method(cost_lines):
        """
        Returns if all lines in cost_lines have a correct split_method.

        Parameters:
        ----------
        cost_lines: stock.landed.cost.lines
            Lines that are wanted to check its split_method

        Return:
        ------
        Bool
        """
        return len(cost_lines.filtered(lambda line: line.split_method == 'to_define')) == 0

    @api.multi
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        digits = dp.get_precision('Product Price')(self._cr)
        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost.picking_ids):

            cost_lines = cost.cost_lines
            if not self.check_if_all_lines_have_split_method(cost_lines):
                raise UserError(_("Can't calculate landed costs. There are lines with split method to define."))

            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            total_tariff = 0.0
            currency_change = 0.0

            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                self.check_lines_hscode(val_line_values)
                for cost_line in cost_lines:
                    if cost_line.split_method == 'by_weight':
                        self.check_lines_weight(val_line_values)
                    val_line_values.update({'cost_id': cost.id,
                                            'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].\
                        create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)
                total_tariff += val_line_values.get('tariff', 0.0)
                former_cost = val_line_values.get('former_cost', 0.0)
                total_cost += tools.float_round(former_cost,
                                                precision_digits=digits[1]) \
                    if digits else former_cost

                total_line += 1

            for line in cost_lines:
                value_split = 0.0
                if line.split_method == 'by_tariff':
                    currency_change = line.price_unit / total_tariff
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.\
                            cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        elif line.split_method == 'by_tariff' and total_tariff:
                            # per_unit = (line.price_unit / total_tariff)
                            value = valuation.tariff * currency_change
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = tools.\
                                float_round(value, precision_digits=digits[1],
                                            rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).\
                write({'additional_landed_cost': value})
        return True

    def get_valuation_lines(self):
        lines = []

        for move in self.mapped('picking_ids').mapped('move_lines'):
            if move.product_id.valuation != 'real_time' or \
                    move.product_id.cost_method != 'fifo':
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.value,
                'cost_purchase': (move.purchase_line_id.price_subtotal/move.purchase_line_id.product_qty) * move.product_qty,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty,
                'tariff': round((move.purchase_line_id.price_subtotal/move.purchase_line_id.product_qty) * move.product_qty *
                                (move.product_id.tariff/100), 2)
            }
            lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_('The selected picking does not contain any move '
                              'that would be impacted by landed costs. Landed '
                              'costs are only possible for products '
                              'configured in real time valuation with real '
                              'price costing method. Please make sure it is '
                              'the case, or you selected the correct picking'))
        return lines


class StockValuationAdjustmentLines(models.Model):

    _inherit = 'stock.valuation.adjustment.lines'

    @api.multi
    @api.depends('former_cost', 'quantity', 'additional_landed_cost', 'cost_purchase')
    def _get_new_move_cost(self):
        for line in self:
            line.new_unit_cost = (line.former_cost +
                                  line.additional_landed_cost) / \
                (line.quantity or 1.0)

    @api.multi
    @api.depends('cost_purchase', 'quantity')
    def _compute_cost_purchase_per_unit(self):
        for line in self:
            line.cost_purchase_per_unit = \
                line.cost_purchase / (line.quantity or 1.0)

    @api.multi
    def _get_cost_percentage_variance(self):
        for line in self:
            try:
                line.cost_percentage_variance = (
                                                    line.new_unit_cost - line.former_cost_per_unit
                                                ) * 100 / line.former_cost_per_unit
            except ZeroDivisionError:
                line.cost_percentage_variance = 0

    new_unit_cost = fields.Float('New standard price', store=True,
                                 compute="_get_new_move_cost")
    tariff = fields.Float("Tariff", digits=(16, 2))
    cost_purchase = fields.Float(
        'Purchase Price', digits=dp.get_precision('Product Price'))
    cost_purchase_per_unit = fields.Float(
        'Purchase Price (Per Unit)', compute='_compute_cost_purchase_per_unit',
        digits=0, store=True)
    cost_percentage_variance = fields.Float(
        'Variance %', compute='_get_cost_percentage_variance', digits=(16, 2)
    )


class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    split_method = fields.Selection(selection_add=[
        ('by_tariff', 'By tariff'),
        ('to_define', 'To define')
    ])

    @api.onchange('product_id')
    def onchange_product_id(self):
        super().onchange_product_id()
        if self.product_id:
            self.account_id = \
                self.product_id.property_stock_account_input.id or \
                self.product_id.categ_id.\
                property_stock_account_input_categ_id.id


class LandedCostCreator(models.TransientModel):
    """
    Models the creation of stock_landed_costs from import_sheet.
    Shows a list with all products with no weight
    """
    _name = 'landed.cost.creator.wizard'

    import_sheet_id = fields.Many2one('import.sheet', string='Import sheet')
    product_ids = fields.Many2many('product.product', string='Products')
    container_id = fields.Many2one(related='import_sheet_id.container_id')

    def _get_account_journal_for_landed_cost(self):
        """
        Returns the correct account journal to assign to landed cost

        Return:
        ------
        account.journal
        """
        # FIXME:
        # self.env['account.journal'].search([()])
        return 1

    def _get_product_for_landed_cost_line(self):
        """
        Returns the correct product to assign to landed cost lines

        Return:
        ------
        product.product
        """
        # FIXME:
        # self.env['product.product'].search([()])
        return 2724

    def _get_account_for_landed_cost_line(self):
        """
        Returns the correct account to assign to landed cost lines

        Return:
        ------
        account.account
        """
        # FIXME:
        # self.env['account.journal'].search([()])
        return 845

    def create_landed_cost(self):
        """
        Creates landed cost associated to import_sheet_id.
        This landed cost has two cost lines.
        """
        landed_cost = self.env['stock.landed.cost'].create({
            'date': datetime.date.today(),
            'picking_ids': [(6, 0, self.container_id.picking_ids.ids)],
            'container_ids': [(4, self.container_id.id)],
            'account_journal_id': self._get_account_journal_for_landed_cost(),
            'forwarder_invoice': self.import_sheet_id.forwarder_comercial,
            'import_sheet_id': self.import_sheet_id.id
        })
        self._create_cost_lines(landed_cost)
        return

    def _create_cost_lines(self, landed_cost):
        """
        Creates two stock.landed.cost.lines.
        The first by fee, the second by destination costs

        Parameters:
        ----------
        landed_cost: stock.landed.cost
            Landed cost where we are going to create lines
        """
        create_line = self.env['stock.landed.cost.lines'].create
        product_id = self._get_product_for_landed_cost_line()
        account_id = self._get_account_for_landed_cost_line()
        create_line({
            'cost_id': landed_cost.id,
            'product_id': product_id,
            'name': 'Arancel',
            'account_id': account_id,
            'split_method': 'by_tariff',
            'price_unit': self.import_sheet_id.calculate_fee_price()
        })
        create_line({
            'cost_id': landed_cost.id,
            'product_id': product_id,
            'name': 'Coste en destino',
            'account_id': account_id,
            'split_method': 'equal',
            'price_unit': self.import_sheet_id.calculate_destination_cost_price()
        })
        return

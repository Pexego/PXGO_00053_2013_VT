from odoo import models, fields, api, exceptions, _


class WizardReconcileRibaLine(models.TransientModel):

    _name = "wizard.reconcile.riba.line"

    select = fields.Boolean('Add')
    riba_line_id = fields.Many2one("riba.distinta.line", 'Riba Line')
    invoice_number = fields.Char('Invoice Number')
    invoice_date = fields.Char('Invoice Date')
    partner_id = fields.Many2one("res.partner")
    iban = fields.Char('Iban')
    amount = fields.Float('Amount')
    due_date = fields.Date('Due')
    wizard_id = fields.Many2one("wizard.reconcile.riba.statement.line")


class WizardReconcileRibaStatementLine(models.TransientModel):

    _name = "wizard.reconcile.riba.statement.line"

    @api.model
    def _get_riba_lines(self):
        wiz_lines = []
        context = self.env.context
        riba_id = self.env['riba.distinta'].browse(context['active_id'])
        for r_line in riba_id.line_ids.filtered(lambda rl: rl.state != 'paid'):
            new_line = {
                'select': True,
                'riba_line_id': r_line.id,
                'invoice_number': r_line.invoice_number,
                'invoice_date': r_line.invoice_date,
                'partner_id': r_line.partner_id,
                'iban': r_line.iban,
                'amount': r_line.amount,
                'due_date': r_line.due_date,
            }
            wiz_lines.append(new_line)
        return wiz_lines

    @api.multi
    @api.depends('bank_statement_line_id')
    def _get_active_amount(self):
        for wzd in self:
            wzd.amount_selected = sum(self.env['riba.distinta'].
                                      browse(self._context['active_ids']).line_ids.
                                      mapped('amount'))

            if self.statement_line_amount == 0.0:
                wzd.difference = 0.0
            else:
                wzd.difference = round(wzd.amount_selected, 2) - \
                                 round(wzd.statement_line_amount, 2)

    @api.multi
    @api.depends('riba_line_ids.select')
    def _get_select_amount(self):
        for wzd in self:
            wzd.amount_selected_riba = sum(self.riba_line_ids.filtered(lambda r: r.select).mapped("amount"))

    journal_id = fields.Many2one("account.journal", "Journal", required=True)
    bank_statement_id = fields.Many2one("account.bank.statement",
                                        "Bank statement", required=True)
    bank_statement_line_id = fields.Many2one("account.bank.statement.line",
                                             "Statement line", required=True)
    currency_id = fields.\
        Many2one('res.currency', string='Currency',
                 related="bank_statement_line_id.journal_currency_id")
    amount_selected = fields.Monetary("Total Riba Amount",
                                      compute="_get_active_amount")
    statement_line_amount = fields.\
        Monetary("Statement line amount", readonly=True,
                 related="bank_statement_line_id.amount",
                 currency_field="currency_id")
    difference = fields.Boolean(computed="_get_active_amount")

    riba_line_ids = fields.Many2many(
        'wizard.reconcile.riba.line', "wizard_id",
        string='Riba lines', default=_get_riba_lines)

    amount_selected_riba = fields.Monetary("Amount Selected", readonly=True, compute="_get_select_amount")

    @api.multi
    def action_reconcile(self):
        #TODO: comprobar que las facturas no estén pagadas o probar a conciliar a ver que pasa

        self.ensure_one()
        if round(self.amount_selected_riba, 2) < \
                round(self.statement_line_amount, 2):
            raise exceptions.UserError(_("Statement amount cannot be grater than riba amount"))

        riba_lines = self.env['riba.distinta.line'].browse(self.riba_line_ids.filtered(lambda l: l.select).mapped('riba_line_id').mapped('id'))
        move_ids = riba_lines.mapped('move_line_ids').mapped('move_line_id')
        counterpart_aml_dicts = []
        for aml in move_ids:
            counterpart_aml_dicts.append({
                'name': aml.name if aml.name != '/' else aml.move_id.name,
                'debit': aml.credit,
                'credit': aml.debit,
                'move_line': aml
            })
        self.bank_statement_line_id.process_reconciliation(
            counterpart_aml_dicts=counterpart_aml_dicts)

        riba_lines.write({'state': 'paid'})
        if all(line.state == 'paid' for line in self.riba_line_ids.mapped('riba_line_id')):
            riba = self.env['riba.distinta'].browse(self._context['active_ids'])
            riba.state = 'paid'


class RibaList(models.Model):

    _inherit = "riba.distinta"

    state = fields.Selection(selection_add=[("gen_file", "Generated File")])


class RibaListLine(models.Model):

    _inherit = "riba.distinta.line"

    @api.multi
    def pay_rib_line(self):
        for line in self:
            line.state = 'paid'

    @api.multi
    def rev_rib_line(self):
        for line in self:
            line.state = 'draft'


class RibaFileExport(models.TransientModel):

    _inherit = "riba.file.export"

    def act_getfile(self):
        res = super().act_getfile()
        active_ids = self.env.context.get('active_ids', [])
        order_obj = self.env['riba.distinta'].browse(active_ids)[0]
        order_obj.state = 'gen_file'
        return res
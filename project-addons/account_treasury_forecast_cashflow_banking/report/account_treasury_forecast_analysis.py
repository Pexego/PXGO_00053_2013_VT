##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import odoo.addons.decimal_precision as dp
from odoo import models, fields, tools, api


class ReportAccountTreasuryForecastAnalysis(models.Model):
    _inherit = 'report.account.treasury.forecast.analysis'
    _order = 'treasury_id asc, date asc, id_ref asc'

    id_ref = fields.Char(string="Id Reference")
    date = fields.Date(string="Date")
    concept = fields.Char(string="Concept")
    partner_name = fields.Char('Partner/Supplier')
    bank_id = fields.Many2one('res.partner.bank', string="Bank Account")
    accumulative_balance = fields.Float(string="Accumulated", digits=dp.get_precision('Account'))

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_account_treasury_forecast_analysis')
        self._cr.execute("""
               create or replace view report_account_treasury_forecast_analysis
                   as (
                       SELECT      row_number() over (order by analysis.treasury_id desc, analysis.date, analysis.id_ref) id,
                                   analysis.id analysis_id,
                                   analysis.treasury_id,
                                   analysis.id_ref,
                                   analysis.date,
                                   analysis.concept,
                                   analysis.partner_name,
                                   analysis.payment_mode_id,
                                   aj.bank_account_id bank_id,
                                   analysis.credit,
                                   analysis.debit,
                                   analysis.balance,
                                   analysis.type,
                                   sum(balance) OVER (PARTITION BY analysis.treasury_id
                                               ORDER BY analysis.treasury_id desc, analysis.date, analysis.id_ref) AS accumulative_balance
                               FROM (
                                   select  '0' as id,
                                       0 as id_ref,
                                       'Importe inicial' as concept,
                                       tf.id as treasury_id,
                                       LEAST(tf.start_date, tf.opened_start_date_customer, tf.opened_start_date_supplier) as date,
                                       null as credit,
                                       null as debit,
                                       start_amount as balance,
                                       null as payment_mode_id,
                                       null as type,
                                       null partner_name
                                   from    account_treasury_forecast tf
                                   where   tf.start_amount > 0 -- Incluir linea de importe inicial
                                   union
                                   select
                                       tfl.id || 'l' AS id,
                                       tfl.id as id_ref,
                                       tfl.name as concept,
                                       treasury_id,
                                       tfl.date as date,
                                       CASE WHEN tfl.line_type='receivable' THEN 0.0
                                       ELSE amount
                                       END as credit,
                                       CASE WHEN tfl.line_type='receivable' THEN amount
                                       ELSE 0.0
                                       END as debit,
                                       CASE WHEN tfl.line_type='receivable' THEN amount
                                       ELSE -amount
                                       END as balance,
                                       payment_mode_id,
                                       CASE WHEN tfl.line_type='receivable' THEN 'in'
                                       ELSE 'out'
                                       END as type,
                                       rp.display_name as partner_name
                                   from    account_treasury_forecast tf
                                       inner join account_treasury_forecast_line tfl on tf.id = tfl.treasury_id
                                                                                           and coalesce(tfl.paid, False) = False
                                       left join res_partner rp ON rp.id = tfl.partner_id
                                   union
                                   select
                                       tcf.id || 'c' AS id,
                                       tcf.id as id_ref,
                                       tcf.name as concept,
                                       treasury_id,
                                       tcf.date as date,
                                       CASE WHEN tcf.flow_type='in' THEN 0.0
                                       ELSE abs(amount)
                                       END as credit,
                                       CASE WHEN tcf.flow_type='in' THEN amount
                                       ELSE 0.0
                                       END as debit,
                                       amount as balance,
                                       payment_mode_id,
                                       flow_type as type,
                                       null as partner_id
                                   from    account_treasury_forecast tf
                                       inner join account_treasury_forecast_cashflow tcf on tf.id = tcf.treasury_id
                                   union
                                   select
                                       tfii.id || 'i' AS id,
                                       ai.id as id_ref,
                                       ai.number as concept,
                                       treasury_id,
                                       tfii.date_due as date,
                                       CASE WHEN ai.type='in_invoice' THEN ABS(tfii.total_amount)
                                       ELSE 0.0
                                       END as credit,
                                       CASE WHEN ai.type='in_invoice' THEN 0.0
                                       ELSE ABS(tfii.total_amount)
                                       END as debit,
                                       -tfii.total_amount as balance,
                                       tfii.payment_mode_id,
                                       CASE WHEN ai.type='in_invoice' THEN 'out'
                                       ELSE 'in'
                                       END as type,
                                       rp.display_name as partner_name
                                       from
                                       account_treasury_forecast tf
                                       inner join account_treasury_forecast_in_invoice_rel tfiir on tf.id = tfiir.treasury_id
                                       inner join account_treasury_forecast_invoice tfii on tfii.id = tfiir.in_invoice_id
                                       inner join account_invoice ai on ai.id = tfii.invoice_id
                                       left join res_partner rp ON rp.id = tfii.partner_id
                                   union
                                   select
                                       tfio.id || 'o' AS id,
                                       ai.id as id_ref,
                                       ai.number as concept,
                                       treasury_id,
                                       tfio.date_due as date,
                                       CASE WHEN ai.type='out_invoice' THEN 0.0
                                       ELSE ABS(tfio.total_amount)
                                       END as credit,
                                       CASE WHEN ai.type='out_invoice' THEN ABS(tfio.total_amount)
                                       ELSE 0.0
                                       END as debit,
                                       tfio.total_amount as balance,
                                       tfio.payment_mode_id,
                                       CASE WHEN ai.type='out_invoice' THEN 'in'
                                       ELSE 'out'
                                       END as type,
                                       rp.display_name as partner_name
                                   from    account_treasury_forecast tf
                                       inner join account_treasury_forecast_out_invoice_rel tfior on tf.id = tfior.treasury_id
                                       inner join account_treasury_forecast_invoice tfio on tfio.id = tfior.out_invoice_id
                                       inner join account_invoice ai on ai.id = tfio.invoice_id
                                       left join res_partner rp ON rp.id = tfio.partner_id
                                   union
                                   select  bm.id || 'v' as id,
                                       bm.id as id_ref,
                                       'Vencimiento bancario' as concept,
                                       atf.id as treasury_id,
                                       bm.date_due as date,
                                       null as credit,
                                       null as debit,
                                       -bm.amount as balance,
                                       null as payment_mode_id,
                                       'out' as type,
                                       rb.name partner_name
                                       from    bank_maturity bm -- Incluir próximos vencimientos
                                       INNER JOIN res_partner_bank rpb ON rpb.id = bm.bank_account
                                       LEFT JOIN res_bank rb ON rb.id = rpb.bank_id
                                       cross join  account_treasury_forecast atf
                                       WHERE   bm.date_due BETWEEN atf.start_date AND atf.end_date
                                               AND coalesce(bm.paid, False) = False AND coalesce(atf.not_bank_maturity, False) = False
                               ) analysis
                               LEFT JOIN account_payment_mode apm ON apm.id = analysis.payment_mode_id
                               LEFT JOIN account_journal aj ON aj.id = apm.fixed_journal_id
                               ORDER  BY analysis.treasury_id, analysis.date, analysis.id_ref
               )""")

# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, tools
import odoo.addons.decimal_precision as dp


class AccountInvoiceCyC(models.Model):

    _name = 'account.invoice.cyc'
    _auto = False

    MONTHS = [(1, 'January'), (2, 'February'), (3, 'March'),
              (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'),
              (11, 'November'), (12, 'December')]
    QUARTERS = [(1, 'Q1'), (2, 'Q2'), (3, 'Q3'), (4, 'Q4')]

    country_id = fields.Many2one('res.country', 'Country', readonly=True)
    credit_covered = fields.Float('Credit covered', readonly=True,
                                  digits=dp.get_precision('Account'))
    credit_not_covered = fields.Float(
        'Credit not covered', readonly=True,
        digits=dp.get_precision('Account'))
    not_credit = fields.Float('No credit', readonly=True,
                              digits=dp.get_precision('Account'))
    cash = fields.Float('Cash', readonly=True,
                        digits=dp.get_precision('Account'))
    invoice_year = fields.Char('Year', readonly=True)
    invoice_month = fields.Selection(MONTHS, string="Month", readonly=True)
    invoice_quarter = fields.Selection(QUARTERS, string="Quarter", readonly=True)
    amount_total = fields.Float('Total', readonly=True,
                                digits=dp.get_precision('Account'))
    invoice_state = fields.Selection([('open', 'Open'), ('paid', 'Paid')],
                                     string="Invoice state", readonly=True)
    user_id = fields.Many2one("res.users", "Comercial", readonly=True)
    area_id = fields.Many2one('res.partner.area', 'Area', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE VIEW account_invoice_cyc as (
select min(a.id) as id, a.country_id, sum(a.credit_covered) as credit_covered,
sum(a.credit_not_covered) as credit_not_covered, a.user_id, a.area_id,
sum(a.not_credit) as not_credit, sum(a.cash) as cash, a.invoice_year,
a.invoice_month, a.invoice_quarter, a.state as invoice_state, sum(a.credit_covered) +
sum(a.credit_not_covered)+ sum(a.not_credit) + sum(a.cash) as amount_total
from (
    select min(ai.id) as id, p.country_id,
    SUM(ai.amount_insurance) as credit_covered,
    sum(ai.amount_total - ai.amount_insurance) as credit_not_covered,
    0.0 as not_credit,
    0.0 as cash,
    CAST(extract(year from ai.date_invoice)::int as text) as invoice_year, p.area_id,
    extract(month from ai.date_invoice) as invoice_month, 
    extract(quarter from ai.date_invoice) as invoice_quarter, ai.state, p.user_id
    from account_invoice ai inner join res_partner p on p.id = ai.partner_id
    where ai.company_id = 1
        and ai.amount_insurance is not null
        and ai.type = 'out_invoice'
        and ai.state in ('open', 'paid')
    group by p.country_id, extract(year from ai.date_invoice)::int,
    extract(month from ai.date_invoice), extract(quarter from ai.date_invoice), ai.state, p.user_id, p.area_id
union
    select min(ai.id) as id, p.country_id,
    0.0 as credit_covered,
    0.0 as credit_not_covered,
    SUM(ai.amount_total) as not_credit,
    0.0 as cash,
    CAST(extract(year from ai.date_invoice)::int as text) as invoice_year, p.area_id,
    extract(month from ai.date_invoice) as invoice_month, 
    extract(quarter from ai.date_invoice) as invoice_quarter, ai.state, p.user_id
    from account_invoice ai inner join res_partner p on p.id = ai.partner_id
    left join account_payment_term apt on apt.id = ai.payment_term_id
    where ai.company_id = 1
        and ai.amount_insurance is null
        and (ai.payment_term_id is null or apt.name not in ('Prepaid','Immediate payment'))
        and ai.type = 'out_invoice'
        and ai.state in ('open', 'paid')
    group by p.country_id, extract(year from ai.date_invoice)::int,
    extract(month from ai.date_invoice), extract(quarter from ai.date_invoice), ai.state, p.user_id, p.area_id
union
    select min(ai.id) as id, p.country_id,
    0.0 as credit_covered,
    0.0 as credit_not_covered,
    -SUM(ai.amount_total) as not_credit,
    0.0 as cash,
    CAST(extract(year from ai.date_invoice)::int as text) as invoice_year, p.area_id,
    extract(month from ai.date_invoice) as invoice_month, 
    extract(quarter from ai.date_invoice) as invoice_quarter, ai.state, p.user_id
    from account_invoice ai inner join res_partner p on p.id = ai.partner_id
    left join account_payment_term apt on apt.id = ai.payment_term_id
    where ai.company_id = 1
        and ai.amount_insurance is null
        and apt.name not in ('Prepaid','Immediate payment')
        and ai.type = 'out_refund'
        and ai.state in ('open', 'paid')
        and p.insurance_credit_limit = 0
    group by p.country_id, extract(year from ai.date_invoice)::int,
    extract(month from ai.date_invoice), extract(quarter from ai.date_invoice), ai.state, p.user_id, p.area_id
union
    select min(ai.id) as id,
    p.country_id, 0.0 as credit_covered,
    0.0 as credit_not_covered,
    0.0 as not_credit,
    SUM(ai.amount_total) as cash,
    CAST(extract(year from ai.date_invoice)::int as text) as invoice_year, p.area_id,
    extract(month from ai.date_invoice) as invoice_month, 
    extract(quarter from ai.date_invoice) as invoice_quarter, ai.state, p.user_id
    from account_invoice ai inner join res_partner p on p.id = ai.partner_id
    left join account_payment_term apt on apt.id = ai.payment_term_id
    where ai.company_id = 1
        and ai.amount_insurance is null
        and (ai.payment_term_id is null or apt.name in ('Prepaid','Immediate payment'))
        and ai.type = 'out_invoice'
        and ai.state in ('open', 'paid')
    group by p.country_id, extract(year from ai.date_invoice)::int,
    extract(month from ai.date_invoice), extract(quarter from ai.date_invoice), ai.state, p.user_id, p.area_id
union
    select min(ai.id) as id,
    p.country_id, 0.0 as credit_covered,
    0.0 as credit_not_covered,
    0.0 as not_credit,
    -SUM(ai.amount_total) as cash,
    CAST(extract(year from ai.date_invoice)::int as text) as invoice_year, p.area_id,
    extract(month from ai.date_invoice) as invoice_month, 
    extract(quarter from ai.date_invoice) as invoice_quarter, ai.state, p.user_id
    from account_invoice ai inner join res_partner p on p.id = ai.partner_id
    left join account_payment_term apt on apt.id = ai.payment_term_id
    where ai.company_id = 1
        and ai.amount_insurance is null
        and (ai.payment_term_id is null or apt.name in ('Prepaid','Immediate payment'))
        and ai.type = 'out_refund'
        and ai.state in ('open', 'paid')
    group by p.country_id, extract(year from ai.date_invoice)::int,
    extract(month from ai.date_invoice), extract(quarter from ai.date_invoice), ai.state, p.user_id, p.area_id) a
group by a.country_id, a.invoice_month, a.invoice_year, a.invoice_quarter, a.state, a.user_id,
a.area_id)
""")

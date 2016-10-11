# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.account_followup.report.account_followup_print import report_rappel
from openerp.osv import osv

if not hasattr(report_rappel, 'old_lines_get_with_partner'):
    report_rappel.old_lines_get_with_partner = report_rappel._lines_get_with_partner

def _lines_get_with_partner(self, partner, company_id):
    res = self.old_lines_get_with_partner(partner, company_id)
    for dct in res:
        dct['line'] = [x for x in dct['line'] if not x['blocked']]
    return [x for x in res if x['line']]

report_rappel._lines_get_with_partner = _lines_get_with_partner

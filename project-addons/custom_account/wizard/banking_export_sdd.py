# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api, _
from openerp.exceptions import Warning


#TODO: Migrar
# ~ class BankingExportSddWizard(models.TransientModel):
    # ~ _inherit = 'banking.export.sdd.wizard'

    # ~ @api.multi
    # ~ def create_sepa(self):
        # ~ for payment_order in self.payment_order_ids:
            # ~ errors = ""
            # ~ for line in payment_order.bank_line_ids:
                # ~ if not line.mandate_id:
                    # ~ errors += _("\nMissing SEPA Direct Debit mandate on the "
                                # ~ "bank payment line with partner '%s' "
                                # ~ "(reference '%s').") % (line.partner_id.name, line.name)
                # ~ elif line.mandate_id.state != 'valid':
                    # ~ errors += _("\nThe SEPA Direct Debit mandate with reference '%s' "
                                # ~ "for partner '%s' has expired.") % (line.mandate_id.unique_mandate_reference,
                                                                    # ~ line.mandate_id.partner_id.name)
                # ~ elif line.mandate_id.type == 'oneoff':
                    # ~ if line.mandate_id.last_debit_date:
                        # ~ errors += _("\nThe mandate with reference '%s' for partner "
                                    # ~ "'%s' has type set to 'One-Off' and it has a "
                                    # ~ "last debit date set to '%s', so we can't use "
                                    # ~ "it.") % (line.mandate_id.unique_mandate_reference,
                                              # ~ line.mandate_id.partner_id.name,
                                              # ~ line.mandate_id.last_debit_date)
            # ~ if errors:
                # ~ raise Warning(errors)
        # ~ return super(BankingExportSddWizard, self).create_sepa()


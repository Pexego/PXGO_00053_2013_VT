##############################################################################
#
#    Copyright (C) 2018 Visiotech All Rights Reserved
#    $Anthonny Contreras Vargas <acontreras@visiotechsecurity.com>$
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

{
    'name': 'Crm Claim custom',
    'version': '11.0',
    'category': 'crm',
    'description': """Crm claim customizations:""",
    'author': 'Visiotech',
    'website': '',
    "depends": ['crm_claim_rma_custom', 'crm_rma_advance_location'],
    "data": ['views/crm_claim_view.xml', 'wizard/crm_update_line_wizard_view.xml'],
    "installable": True
}

# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp.osv import fields, osv
from openerp import tools


class crm_claim_cost_report(osv.osv):

    _inherit = "crm.claim.cost.report"

    _columns = {
        'priority': fields.selection([('1', 'High'), ('2', 'Critical')],
                                     'Priority', readonly=True),
        'comercial_id': fields.many2one("res.users", string="Comercial",
                                        readonly=True),
        'claim_date': fields.date('Claim Date', readonly=True),
        'subject': fields.selection([('return', 'Return'),
                                     ('rma', 'RMA')], string='Claim Subject',
                                    readonly=True),
    }

    def init(self, cr):

        """ Display Number of cases And Section Name
        @param cr: the current row, from the database cursor,
         """

        tools.drop_view_if_exists(cr, 'crm_claim_cost_report')
        cr.execute("""
            create or replace view crm_claim_cost_report as (
                select
                    min(c.id) as id,
                    c.date as claim_date,
                    c.date_closed as date_closed,
                    c.date_deadline as date_deadline,
                    c.user_id,
                    c.stage_id,
                    c.section_id,
                    c.comercial as comercial_id,
                    c.partner_id,
                    c.company_id,
                    c.categ_id,
                    c.claim_type,
                    c.name as subject,
                    c.priority as priority,
                    c.type_action as type_action,
                    c.create_date as create_date,
                    avg(extract('epoch' from (c.date_closed-c.create_date)))/(3600*24) as  delay_close,
                    (SELECT count(id) FROM mail_message WHERE model='crm.claim' AND res_id=c.id) AS email,
                    extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24) as  delay_expected,
                    c.rma_cost as nbr
                from
                    crm_claim c
                group by c.date,\
                        c.user_id,c.section_id, c.stage_id,c.claim_type,c.comercial,\
                        c.categ_id,c.partner_id,c.company_id,c.create_date,
                        c.priority,c.type_action,c.date_deadline,c.date_closed,c.id
            )""")

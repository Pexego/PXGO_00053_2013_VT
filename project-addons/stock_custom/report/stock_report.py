from openerp import tools
#from openerp.osv import fields, osv
from openerp import models, fields, tools


class stock_picking_report(models.Model):
    _name = 'stock.picking.report'
    _description = "Sales Picking Statistics"
    _auto = False
    _rec_name = 'date'

    _order = 'date desc'

    name = fields.Char('Picking Name', readonly=True)
    date = fields.Datetime('Date Order', readonly=True)
    date_done = fields.Datetime('Date Done', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_qty = fields.Float('# of Qty', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    commercial = fields.Many2one('res.users', 'Commercial', readonly=True)
    price_total = fields.Float('Total Price', readonly=True)
    categ_id = fields.Many2one('product.category','Category of Product', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    state = fields.Selection([
            ('cancel', 'Cancelled'),
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('exception', 'Exception'),
            ('done', 'Done')], 'Pciking Status', readonly=True)
    area_id = fields.Many2one('res.partner.area', 'Area', readonly=True)
    state_name = fields.Many2one('res.country.state', 'State Name', readonly=True)
    section_id = fields.Many2one('crm.case.section', 'Sales Team', readonly=True)

    def _select(self):
        select_str = """
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.price_subtotal) as price_total,
                    count(*) as nbr,
                    s.date as date,
                    s.date_done as date_done,
                    rp.id as partner_id,
                    s.name as name,
                    s.commercial as commercial,
                    l.state,
                    t.categ_id as categ_id,
                    rp.area_id as area_id,
                    rp.state_id as state_name,
                    rp.section_id as section_id
        """
        return select_str

    def _from(self):
        from_str = """
            stock_move l
                left join stock_picking s on (l.picking_id = s.id)
                    left join res_partner r on (r.id = s.partner_id)
                    left join res_partner rp on (rp.id = r.commercial_partner_id)
                    left join product_product p on (l.product_id = p.id)
                        left join product_template t on (p.product_tmpl_id = t.id)
                    left join stock_picking_type as pt on (pt.id = s.picking_type_id)
                left join stock_location sl on (sl.id = l.location_dest_id)
                left join product_uom u on (u.id = l.product_uom)
                left join product_uom u2 on (u2.id = t.uom_id)
        """

        return from_str

    def _where(self):
        where = """
            pt.code = 'outgoing' and sl.usage = 'customer'
        """
        return where

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    s.name,
                    t.uom_id,
                    t.categ_id,
                    s.date,
                    s.date_done,
                    r.parent_id,
                    s.commercial,
                    l.state,
                    rp.id,
                    rp.area_id,
                    rp.state_id,
                    rp.section_id
        """
        return group_by_str

    def init(self, cr):
        # self._table = sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            WHERE ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._where(), self._group_by()))

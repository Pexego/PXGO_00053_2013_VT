from openerp import tools
from openerp.osv import fields, osv
#from openerp import models, fields, tools

class stock_picking_report(osv.osv):
    _name = 'stock.picking.report'
    _description = "Sales Picking Statistics"
    _auto = False
    _rec_name = 'date'

    _columns = {
        'name': fields.char('Picking Name', readonly=True),
        'date': fields.datetime('Date Order', readonly=True),
        'date_done': fields.datetime('Date Done', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom_qty': fields.float('# of Qty', readonly=True),

        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True),
        'commercial': fields.many2one('res.users', 'Commercial', readonly=True),
        'price_total': fields.float('Total Price', readonly=True),
        'categ_id': fields.many2one('product.category','Category of Product', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),
        'state': fields.selection([
            ('cancel', 'Cancelled'),
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('exception', 'Exception'),
            ('done', 'Done')], 'Pciking Status', readonly=True)
    }
    _order = 'date desc'

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
                    r.parent_id as partner_id,
                    s.name as name,
                    s.commercial as commercial,
                    l.state,
                    t.categ_id as categ_id
        """
        return select_str

    def _from(self):
        from_str = """
            stock_move l
                left join stock_picking s on (l.picking_id = s.id)
                    left join res_partner r on (r.id = s.partner_id)
                    left join product_product p on (l.product_id = p.id)
                        left join product_template t on (p.product_tmpl_id = t.id)
                    left join stock_picking_type spt on (spt.id = s.picking_type_id)
                        left join ir_sequence i on (i.id = spt.sequence_id)
                        left join stock_location sl on (sl.id = spt.default_location_dest_id)
                left join product_uom u on (u.id = l.product_uom)
                left join product_uom u2 on (u2.id = t.uom_id)

        """

        return from_str

    def _where(self):
        where = """
            i.prefix = 'VT\\OUT\\' AND sl.name = 'Customers'
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
                    l.state
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

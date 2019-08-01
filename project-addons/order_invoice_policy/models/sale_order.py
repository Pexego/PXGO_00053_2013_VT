from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_invoice_policy = fields.Selection([
        ('by_product', 'Defined by Product'),
        ('prepaid', 'Before Delivery'),
    ],
        string='Invoicing Policy',
        required=True,
        readonly=True,
        states={'sale': [('readonly', False)],
                'done': [('readonly', False)]},
        default='by_product'
    )

    invoice_status_2 = fields.Selection([
        ('invoiced', 'Fully Invoiced'),
        ('to_invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice'),
        ('partially_invoiced', 'Partially invoiced')
        ], string='Invoice Status', compute='_get_invoice_status_2', store=True, readonly=True)

    @api.depends('state', 'order_line.invoice_status', 'force_invoiced')
    def _get_invoice_status_2(self):
        """
        Compute the invoice status (2) of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line with product (not services) is 'to invoice' or all lines are services,
          the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        """
        for order in self:
            if order.state not in ('sale', 'done'):
                invoice_status = 'no'
            elif order.force_invoiced:
                invoice_status = 'invoiced'
            elif any(line.invoice_status == 'to invoice'
                     for line in order.order_line.filtered(lambda p: p.product_id.type in ['product', 'consu'])) or \
                    all(line.invoice_status == 'to invoice' and line.product_id.type == 'service'
                        for line in order.order_line):
                invoice_status = 'to_invoice'
            elif all(line.invoice_status in ('invoiced', 'cancel', 'upselling') for line in order.order_line):
                invoice_status = 'invoiced'
            elif any(line.invoice_status == 'invoiced' for line in order.order_line):
                invoice_status = 'partially_invoiced'
            else:
                invoice_status = 'no'

            order.invoice_status_2 = invoice_status


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    invoice_status = fields.Selection(selection_add=[('cancel', 'Cancelled')])

    @api.depends('order_id.order_invoice_policy')
    def _get_to_invoice_qty(self):
        lines = self.filtered(lambda sol: sol.order_id.state in ['sale', 'done']
                                          and sol.order_id.order_invoice_policy == 'prepaid'
                                          and 'assigned' in sol.move_ids.mapped('state'))
        # Permitir facturar antes de entrega lo que esté reservado
        for line in lines:
            pack = self.env['mrp.bom']._bom_find(product=line.product_id)
            if pack and pack.type == 'phantom':
                # Calcular cantidad del pack a facturar
                moves_pack = lines.move_ids.filtered(lambda mv: 'assigned' in mv.state)
                quantities = line._get_bom_component_qty(pack)
                assign_components_qty = {}
                for move in moves_pack:
                    quantities_uom = self.env['product.uom'].browse(quantities[move.product_id.id]['uom'])
                    pack_qty = move.product_uom._compute_quantity(move.product_uom_qty, quantities_uom)
                    if move.location_dest_id.usage == "customer":
                        if not move.origin_returned_move_id or \
                                (move.origin_returned_move_id and move.to_refund):
                            if move.product_id.id not in assign_components_qty:
                                assign_components_qty[move.product_id.id] = 0.0
                            assign_components_qty[move.product_id.id] += pack_qty
                assign_qty = line.get_pack_quantity(assign_components_qty, quantities)
            else:
                assign_qty = sum(line.move_ids.filtered(lambda mv: mv.state == 'assigned').mapped('product_qty'))
            line.qty_to_invoice = assign_qty - (line.qty_invoiced - line.qty_delivered)
        super(SaleOrderLine, self - lines)._get_to_invoice_qty()

    @api.depends('move_ids.state')
    def _compute_invoice_status(self):
        """ Add new invoice status:
        - cancel: if all moves associated to a SO line are 'cancel', the invoice state of this line is 'cancel'
        """
        super(SaleOrderLine, self)._compute_invoice_status()
        for line in self:
            if line.order_id.state in ('sale', 'done') \
                    and line.product_id.type == 'product'\
                    and line.product_id.invoice_policy == 'delivery'\
                    and line.move_ids \
                    and all(move.state == 'cancel' for move in line.move_ids):
                line.invoice_status = 'cancel'

    def _get_invoice_qty(self):
        super()._get_invoice_qty()
        for line in self:
            pack = self.env['mrp.bom']._bom_find(product=line.product_id)
            if pack and pack.type == 'phantom':
                # Si es un pack, recalcular lo facturado sin redondear
                # (por si se entrega una parte de los pack de x unidades de un producto)
                qty_invoiced = 0.0
                for invoice_line in line.invoice_lines:
                    if invoice_line.invoice_id.state != 'cancel':
                        if invoice_line.invoice_id.type == 'out_invoice':
                            qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity,
                                                                                  line.product_uom,
                                                                                  round=False)
                        elif invoice_line.invoice_id.type == 'out_refund':
                            qty_invoiced -= invoice_line.uom_id._compute_quantity(invoice_line.quantity,
                                                                                  line.product_uom,
                                                                                  round=False)
                line.qty_invoiced = qty_invoiced


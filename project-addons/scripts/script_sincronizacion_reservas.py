for product in session.env['product.product'].search([('type', '!=', 'service')]):
    print("Producto {}".format(product.default_code))
    move_lines_data = session.env['stock.move.line'].read_group([('product_id', '=', product.id),('location_id.usage', '=', 'internal'),('product_uom_qty', '>', 0)], ['location_id', 'product_uom_qty'], ['location_id'])
    if not move_lines_data:
        quants = session.env['stock.quant'].search([('location_id.usage', '=', 'internal'),('product_id', '=', product.id),('reserved_quantity', '>', 0)])
        if quants:
            for quant in quants:
                quant.reserved_quantity = 0.0
            print("Sin reservas pero con quants reservados para el producto {}, se ponen a 0".format(product.default_code))
    for data in move_lines_data:
        quants = session.env['stock.quant'].search([('location_id', '=', data['location_id'][0]),('product_id', '=', product.id),('quantity', '>', 0)], order="in_date asc")
        if not quants:
            move_lines = session.env['stock.move.line'].search([('product_id', '=', product.id),('location_id', '=', data['location_id'][0]),('product_uom_qty', '>', 0)])
            moves = move_lines.mapped('move_id').filtered(lambda x: x.state in ('assigned', 'partially_available'))
            session.cr.execute("delete from stock_move_line where id in ({})".format(",".join([str(x) for x in move_lines.ids])))
            moves.write({'state': 'confirmed'})
            print("Se borran las reservas del producto {} por no tener stock en la ubicación {}".format(product.default_code, data['location_id'][1]))
        reserved_qty = 0
        for quant in quants:
            if data['product_uom_qty'] > reserved_qty:
                if quant.quantity >= (data['product_uom_qty'] - reserved_qty):
                    quant.reserved_quantity = (data['product_uom_qty'] - reserved_qty)
                    reserved_qty += (data['product_uom_qty'] - reserved_qty)
                else:
                    quant.reserved_quantity = quant.quantity
                    reserved_qty += quant.quantity
            else:
                quant.reserved_quantity = 0.0
        print("Reservado {} en {} del producto {}".format(reserved_qty, data['location_id'][1], product.default_code))
        if quants and reserved_qty < data['product_uom_qty']:
            move_lines = session.env['stock.move.line'].search([('product_id', '=', product.id),('location_id', '=', data['location_id'][0]),('product_uom_qty', '>', 0)])
            moves = move_lines.mapped('move_id').filtered(lambda x: x.state in ('assigned', 'partially_available'))
            session.cr.execute("delete from stock_move_line where id in ({})".format(",".join([str(x) for x in move_lines.ids])))
            moves.write({'state': 'confirmed'})
            for quant in quants:
                quant.reserved_quantity = 0.0
            print("Menos stock que reservas para el producto {} en la ubicación {}".format(product.default_code, data['location_id'][1]))

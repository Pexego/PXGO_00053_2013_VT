session.open(db="visiotech")
account_610 = session.env['account.account'].search([('code', '=', '61000000'),('company_id', '=', 1)]).id
account_300 = session.env['account.account'].search([('code', '=', '30000000'),('company_id', '=', 1)]).id
move = session.env['account.move'].with_context(check_move_validity=False).create({'journal_id': 5,'company_id': 1})
import xlrd
path = "/home/comunitea/Valor_Stock_28_6_2019.xlsx"
workbook = xlrd.open_workbook(path)
worksheet = workbook.sheet_by_index(0)
valor_no_imputado = 0.0
offset = 1
product_ids = []
move_lines_data = []
account_610_amount = 0.0
for i, row in enumerate(worksheet.get_rows()):
    if i < offset or not row[0].value.strip():
        continue
    product = session.env['product.product'].with_context(company_owned=True).search([('default_code', '=', row[0].value.strip())])
    if product:
        product_ids.append(product.id)
        if product.type == 'product' and product.valuation == 'real_time':
            move_lines = session.env['account.move.line'].search([('product_id', '=', product.id),('account_id', '=', account_300)])
            balance = round(sum(round(x, 2) for x in move_lines.mapped('balance')),2)
            if row[2].value < 0.0:
                final_balance = 0.0
            else:
                final_balance = row[2].value
            balance_diff = 0.0
            if (final_balance - balance) > 1 or (final_balance - balance) < -1:
                balance_diff = round(final_balance - balance, 2)
            if balance_diff:
                if balance_diff > 0:
                    field = 'debit'
                else:
                    field = 'credit'
                account_610_amount += balance_diff
                move_lines_data.append((0, 0, {field: abs(balance_diff), 'product_id': product.id, 'account_id': account_300, 'journal_id': 5, 'company_id': 1, 'name': product.name}))
            if product.qty_available > 0:
                apply_qty = 0.0
                product.standard_price = round(row[2].value / product.qty_available, 3)
                cost_unit = row[2].value / product.qty_available
                moves = session.env['stock.move'].search([('product_id', '=', product.id),('remaining_qty', '>', 0.0),('company_id', '=', 1)], order="id desc")
                for move_obj in moves:
                    if move_obj.remaining_qty + apply_qty <= product.qty_available:
                        remaining_qty = move_obj.remaining_qty
                        apply_qty += remaining_qty
                    elif apply_qty < product.qty_available and move_obj.remaining_qty + apply_qty > product.qty_available:
                        remaining_qty = product.qty_available - apply_qty
                        apply_qty += remaining_qty
                    else:
                        remaining_qty = 0
                    move_obj.write({'value': cost_unit * move_obj.product_uom_qty, 'remaining_value': cost_unit * remaining_qty, 'price_unit': cost_unit, 'remaining_qty': remaining_qty})
            else:
                moves = session.env['stock.move'].search([('product_id', '=', product.id),('remaining_qty', '>', 0.0),('company_id', '=', 1)], order="id desc")
                for move_obj in moves:
                    move_obj.write({'remaining_value': 0.0, 'remaining_qty': 0.0})
        else:
            print("El producto {} no es almacenable o no es valorizable en tiempo real, por lo que su valor contable debería de ser 0, se descarta el valor {}".format(row[0].value,row[2].value))
            valor_no_imputado += row[2].value
            move_lines = session.env['account.move.line'].search([('product_id', '=', product.id),('account_id', '=', account_300)])
            balance = round(sum(round(x, 2) for x in move_lines.mapped('balance')), 2)
            if balance:
                print("Para el producto {} hay un valor contable de {} que ponemos a 0".format(row[0].value, balance))
                if balance > 0:
                    field = 'credit'
                else:
                    field = 'debit'
                account_610_amount += -balance
                move_lines_data.append((0, 0, {field: abs(balance), 'product_id': product.id, 'account_id': account_300, 'journal_id': 5, 'company_id': 1, 'name': product.name}))
            moves = session.env['stock.move'].search([('product_id', '=', product.id),('remaining_qty', '>', 0.0),('company_id', '=', 1)], order="id desc")
            for move_obj in moves:
                move_obj.write({'remaining_value': 0.0, 'remaining_qty': 0.0})
    else:
        print("El producto {} no existe, se descarta el valor {}".format(row[0].value,row[2].value))
        valor_no_imputado += row[2].value

move_data = session.env['account.move.line'].read_group([('product_id', 'not in', product_ids),('product_id', '!=', False),('account_id', '=', account_300)], ['product_id','balance'], ['product_id'])
for data in move_data:
    if data['balance']:
        if data['balance'] > 0:
            field = 'credit'
        else:
            field = 'debit'
        account_610_amount += -round(data['balance'], 2)
        product = session.env['product.product'].browse(data['product_id'][0])
        move_lines_data.append((0, 0, {field: abs(round(data['balance'],2)), 'product_id': product.id, 'account_id': account_300, 'journal_id': 5, 'company_id': 1, 'name': product.name}))

if account_610_amount > 0:
    contrafield = 'credit'
else:
    contrafield = 'debit'

move_lines_data.append((0, 0, {contrafield: abs(round(account_610_amount, 2)), 'account_id': account_610, 'journal_id': 5, 'company_id': 1, 'name': "Contrapartida"}))
move.write({'line_ids': move_lines_data})
print("El valor no imputado del excel fue {}".format(valor_no_imputado))
session.cr.commit()
exit()

session.open(db="visiotech_migration")
account_610 = session.env['account.account'].search([('code', '=', '61000000'),('company_id', '=', 1)]).id
account_300 = session.env['account.account'].search([('code', '=', '30000000'),('company_id', '=', 1)]).id
move = session.env['account.move'].with_context(check_move_validity=False).create({'date': '2019-05-07','journal_id': 5,'company_id': 1})
import xlrd
path = "/home/comunitea/Importacion_stock_prueba_07_5_2019.xlsx"
workbook = xlrd.open_workbook(path)
worksheet = workbook.sheet_by_index(0)
valor_no_imputado = 0.0
offset = 1
product_ids = []
move_lines_data = []
account_610_amount = 0.0
for i, row in enumerate(worksheet.get_rows()):
    if i < offset or not row[1].value.strip():
        continue
    product = session.env['product.product'].with_context(to_date='2019-05-07',company_owned=True).search([('default_code', '=', row[1].value.strip())])
    if product:
        product_ids.append(product.id)
        if product.type == 'product' and product.valuation == 'real_time':
            move_lines = session.env['account.move.line'].search([('product_id', '=', product.id),('account_id', '=', account_300),('date', '<=', '2019-05-07')])
            balance = round(sum(round(x, 2) for x in move_lines.mapped('balance')),2)
            if row[3].value < 0.0:
                final_balance = 0.0
            else:
                final_balance = row[3].value
            balance_diff = 0.0
            if (final_balance - balance) > 1 or (final_balance - balance) < -1:
                balance_diff = round(final_balance - balance, 2)
            if balance_diff:
                if balance_diff > 0:
                    field = 'debit'
                else:
                    field = 'credit'
                account_610_amount += balance_diff
                move_lines_data.append((0, 0, {field: abs(balance_diff), 'product_id': product.id, 'account_id': account_300, 'journal_id': 5, 'company_id': 1, 'date': '2019-05-07', 'name': product.name}))
            if product.qty_available:
                product.standard_price = round(row[3].value / product.qty_available, 3)
                cost_unit = row[3].value / product.qty_available
                moves = session.env['stock.move'].search([('product_id', '=', product.id),('remaining_value', '>', 0.0),('company_id', '=', 1)])
                for move_obj in moves:
                    move_obj.write({'value': cost_unit * move_obj.product_uom_qty, 'remaining_value': cost_unit * move_obj.remaining_qty, 'price_unit': cost_unit})
        else:
            print("El producto {} no es almacenable o no es valorizable en tiempo real, por lo que su valor contable debería de ser 0, se descarta el valor {}".format(row[1].value,row[3].value))
            valor_no_imputado += row[3].value
            move_lines = session.env['account.move.line'].search([('product_id', '=', product.id),('account_id', '=', account_300),('date', '<=', '2019-05-07')])
            balance = round(sum(round(x, 2) for x in move_lines.mapped('balance')), 2)
            if balance:
                print("Para el producto {} hay un valor contable de {} que ponemos a 0".format(row[1].value, balance))
                if balance > 0:
                    field = 'credit'
                else:
                    field = 'debit'
                account_610_amount += -balance
                move_lines_data.append((0, 0, {field: abs(balance), 'product_id': product.id, 'account_id': account_300, 'journal_id': 5, 'company_id': 1, 'date': '2019-05-07', 'name': product.name}))
    else:
        print("El producto {} no existe, se descarta el valor {}".format(row[1].value,row[3].value))
        valor_no_imputado += row[3].value

move_data = session.env['account.move.line'].read_group([('product_id', 'not in', product_ids),('product_id', '!=', False),('account_id', '=', account_300),('date', '<=', '2019-05-07')], ['product_id','balance'], ['product_id'])
for data in move_data:
    if data['balance']:
        if data['balance'] > 0:
            field = 'credit'
        else:
            field = 'debit'
        account_610_amount += -round(data['balance'], 2)
        product = session.env['product.product'].browse(data['product_id'][0])
        move_lines_data.append((0, 0, {field: abs(round(data['balance'],2)), 'product_id': product.id, 'account_id': account_300, 'journal_id': 5, 'company_id': 1, 'date': '2019-05-07', 'name': product.name}))

if account_610_amount > 0:
    contrafield = 'credit'
else:
    contrafield = 'debit'

move_lines_data.append((0, 0, {contrafield: abs(round(account_610_amount, 2)), 'account_id': account_610, 'journal_id': 5, 'company_id': 1, 'date': '2019-05-07', 'name': "Contrapartida"}))
move.write({'line_ids': move_lines_data})
print("El valor no imputado del excel fue {}".format(valor_no_imputado))
session.cr.commit()
exit()

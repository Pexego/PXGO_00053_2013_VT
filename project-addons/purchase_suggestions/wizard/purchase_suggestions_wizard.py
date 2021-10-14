from odoo import models, fields, api, _
from datetime import datetime, timedelta
from pandas.core.algorithms import quantile
from numpy import mean
from dateutil.relativedelta import relativedelta


def calculate_distances(quantiles_by_product):
    dist_by_product = {}
    # Por cada elemento de data calculamos la distancia entre cada cuartil y las metemos en el diccioanrio:
    for product, quantiles in quantiles_by_product.items():
        # EL cálculo de las distancias sería:
        #   D1= Valor del Q1 - Valor del Q0
        #   D2= Valor del Q2 - Valor del Q1
        #   D3= Valor del Q3 - Valor del Q2
        #   D4= Valor del Q4 - Valor del Q3
        # La tabla tendría el siguiente aspecto a partir de los siguientes cuartiles:
        # TABLA DE cUARTILES:
        # --------------------
        #                   min      c0      c1      c2      c3      c4      max
        #                --------   ----    ----    ----    ----    -----   ------
        # AC-CARTEL-IT    -31.50     0.0     0.0     6.0     21.0    52.50   52.50
        #
        #
        # Tabla de Distancias
        # ---------------------
        #                        D1        D2       D3         D4
        #                       ----      ---      ---        -----
        # AC-CARTEL-IT            0         6       15         31.5
        dist_by_product[product] = {}
        for y in range(0, 4):
            dist_name = 'd' + str((y + 1))
            q_origin = 'q' + str(y)
            q_dest = 'q' + str((y + 1))
            dist_by_product[product][dist_name] = quantiles[q_dest] - quantiles[q_origin]
    return dist_by_product


def uds(quantiles_by_product, distances_by_product, mean_by_product):
    #Función que calcula las uds de producto dependiendo de los datos calculados anteriormente
    units_by_product = {}
    for product, distances in distances_by_product.items():
        mean = mean_by_product[product]
        quantiles = quantiles_by_product[product]
        q1, q2, q3 = quantiles['q1'], quantiles['q2'], quantiles['q3']
        d1, d2, d3, d4 = distances['d1'], distances['d2'], distances['d3'], distances['d4']
        if mean < q1:
            if d2 <= d3 * 0.7 or (d1 <= d3 * 0.7 and d1 <= d2 * 0.7):
                units_by_product[product] = q1 + d2 * 0.5
            else:
                units_by_product[product] = q2
        elif q1 <= mean < q2:
            if d3 <= d2 * 0.7:
                units_by_product[product] = q2 + d3 * 0.25
            else:
                units_by_product[product] = q2
        elif q2 <= mean < q3:
            if d4 <= d3 * 0.7:
                units_by_product[product] = q3
            else:
                units_by_product[product] = mean
        elif q3 <= mean:
            if d4 <= d3 * 0.7 and mean <= q3 + d4 * 0.5:
                units_by_product[product] = mean
            elif d4 <= d3 * 0.7 and mean > q3 + d4 * 0.5:
                units_by_product[product] = q3 + d4 * 0.5
            else:
                units_by_product[product] = q3
    return units_by_product


def recurrent_products(data, level, month_mode=False):
    recurrent = []
    # Se recorren los elementos pasados en el data (pueden ser o los productos de las ventas por semanas o de los meses)
    for prod, sales in data.items():
        # Sacamos la primera venta
        first_sale = sales["sorted_keys"][0]
        date_now = datetime.now()
        #Calculamos el número de semanas o meses desde la primera venta a la actualidad
        if month_mode:
            first_sale_object = datetime.strptime(first_sale, "%B %Y")
            total_num = (date_now.year - first_sale_object.year) * 12 + (date_now.month - first_sale_object.month)
        else:
            first_sale_object = datetime.strptime(first_sale + '-1', "W%W %Y-%u")
            total_num = (date_now.year - first_sale_object.year) * 53 + (
                    int(date_now.strftime("%V")) - int(first_sale_object.strftime("%V")))
        if total_num > 1:
            # Si hay alguna semana/mes desde la primera venta que es 0, se cuentan las semanas que pasan guardando el número en c
            # y sí el número de semanas/meses que no se ha vendido nada desde la primera venta / el número total de semanas o meses desde
            # la primera venta es menor o igual a la cota que se le ha pasado por cabecera, añadimos el producto
            num_with_sales = len(sales["sorted_keys"])
            if total_num != num_with_sales:
                c = total_num - num_with_sales
                if c / total_num <= level:
                    recurrent.append(prod)
            else:
                # Si no hay ninguna semana en la que no se haya vendido el producto desde la primera venta añadimos el producto
                recurrent.append(prod)
    return recurrent


def remove_products(sales_dict, recurrent_products):
    for product in recurrent_products:
        if sales_dict.get(product, False):
            del sales_dict[product]


def _get_sales(sales, product, month_mode):
    sales_product = sales[product]
    first_sale = sales_product["sorted_keys"][0]
    date_now = datetime.now()
    if month_mode:
        first_sale_object = datetime.strptime(first_sale, "%B %Y")
        total_num = (date_now.year - first_sale_object.year) * 12 + (date_now.month - first_sale_object.month)
    else:
        first_sale_object = datetime.strptime(first_sale + '-1', "W%V %G-%u")
        total_num = (date_now.year - first_sale_object.year) * 53 + (
                int(date_now.strftime("%V")) - int(first_sale_object.strftime("%V")))
    sales_qty = []
    for inc in range(0, total_num + 1):
        if month_mode:
            date_formatted = (first_sale_object + relativedelta(months=inc)).strftime("%B %Y")
        else:
            date_formatted = (first_sale_object + timedelta(weeks=inc)).strftime("W%V %G").replace('W0', 'W')
        if date_formatted in sales_product["sorted_keys"]:
            sales_qty.append(sales_product[date_formatted])
        else:
            sales_qty.append(0)
    sales_product['sales'] = sales_qty
    return sales_qty


def mean_data(data, products, num):
    #Función que calcula la media de las últimas num ventas de cada producto
    mean_by_product = {}
    for product in products:
        mean_by_product[product] = mean(data[product]['sales'][-num:])
    return mean_by_product


def calculate_quantiles(data, ref, month_mode=False):
    quantiles_by_product = {}
    # Nos recorremos las referencias que se le hayan pasado en la variable 'ref'
    for product in ref:
        # Si tiene alguna venta calculamos sus cuariles
        if data.get(product, False) and len(data.get(product).get('sorted_keys')) > 0:
            #Calculamos las ventas por semana/mes desde la primera venta
            sales_qty = _get_sales(data, product, month_mode)
            #Calculamos los cuartiles
            q1 = quantile(sales_qty, 0.25)
            q3 = quantile(sales_qty, 0.75)
            min = q1 - (q3 - q1) * 1.5
            max = q3 + (q3 - q1) * 1.5
            q0, q2, q4 = quantile(sales_qty, [0, 0.5, 1])
            if q4 > max:
                q4 = q3 + (q3 - q1) * 1.5
            elif q0 < min:
                q0 = q1 - (q3 - q1) * 1.5
            quantiles_by_product[product] = {'min': min, 'q0': q0, 'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4,
                                             'max': max}
    return quantiles_by_product


class PurchaseSuggestionsQuantile(models.TransientModel):
    _name = 'purchase.suggestions.statistics'

    product_id = fields.Many2one("product.product")
    suggestion_id = fields.Many2one('purchase.suggestions')
    min = fields.Float()
    q0 = fields.Float()
    q1 = fields.Float()
    q2 = fields.Float()
    q3 = fields.Float()
    q4 = fields.Float()
    max = fields.Float()
    d1 = fields.Float()
    d2 = fields.Float()
    d3 = fields.Float()
    d4 = fields.Float()
    mean = fields.Float()
    calculated_by = fields.Selection(
        selection=[('month', 'Month'),
                   ('week', 'Week')])


class PurchaseSuggestionsLine(models.TransientModel):
    _name = 'purchase.suggestions.line'
    product_id = fields.Many2one('product.product', "Product")
    suggestion_id = fields.Many2one('purchase.suggestions')
    qty = fields.Float("Quantity")
    calculated_by = fields.Selection(
        selection=[('month', 'Month'),
                   ('week', 'Week')])

    def _compute_qty_to_purchase(self):
        # Si las uds calculadas provienen del cálculo por semanas, la cantidad a comprar será 8 * uds + reservas - stock real
        # Si proviene de meses, la cantidad será uds + reservas - stock_real
        for line in self:
            if line.calculated_by == 'week':
                qty = line.qty * 8
            else:
                qty = line.qty
            line.qty_to_purchase = qty + line.product_id.reservation_count - line.product_id.qty_available

    qty_to_purchase = fields.Float(
        help="If the quantity has been calculated by weeks, this field will be equal to 8 * qty + reserves - real stock,"
             " if it has been calculated by months will be equal to qty + reserves - real stock",
        compute="_compute_qty_to_purchase")


class PurchaseSuggestions(models.TransientModel):
    _name = 'purchase.suggestions'
    month_level = fields.Float()
    week_level = fields.Float()
    date_from = fields.Datetime()
    line_weeks_ids = fields.One2many('purchase.suggestions.line', 'suggestion_id',domain=[('calculated_by','=','week')])
    statistic_weeks_ids = fields.One2many('purchase.suggestions.statistics', 'suggestion_id',domain=[('calculated_by','=','week')])
    line_month_ids = fields.One2many('purchase.suggestions.line', 'suggestion_id',domain=[('calculated_by','=','month')])
    statistic_month_ids = fields.One2many('purchase.suggestions.statistics', 'suggestion_id',domain=[('calculated_by','=','month')])


    def create_order(self):
        #Función que creará el PO con los productos que haya en line_ids y las cantidades que haya en qty_to_purchase
        pass


class PurchaseSuggestionsWizard(models.TransientModel):
    _name = 'purchase.suggestions.wizard'

    month_level = fields.Float(default=0.5)
    week_level = fields.Float(default=0.3)
    date_from = fields.Datetime(required=True)

    @api.multi
    def calculate(self):
        domain = [('state', 'in', ['sale', 'done']), ('create_date', '>=', self.date_from)]
        fields = ['product_id', 'product_uom_qty', 'create_date']
        #Sacamos las ventas agrupadas por semana y producto
        sales_by_week = self.env['sale.order.line'].read_group(
            domain=domain,
            fields=fields,
            groupby=['product_id', 'create_date:week'], lazy=False)
        # Sacamos las ventas agrupadas por mes y producto
        sales_by_month = self.env['sale.order.line'].with_context(lang='en_US').read_group(
            domain=domain,
            fields=fields,
            groupby=['product_id', 'create_date:month'], lazy=False)

        #Generamos un diccionario con el producto como clave y como valores un diccionario con la semana como clave y
        #las ventas que se han realizado en esa semana como valor
        # Ej: {4410:{'W12 2020': 25.0,'W17 2021': 21.0,'W37 2020': 55.0}
        sales_by_week_dicc = {}
        for elem in sales_by_week:
            product = elem.get('product_id')
            if sales_by_week_dicc.get(product[0], False):
                sales_by_week_dicc[product[0]].update({elem['create_date:week']: elem['product_uom_qty']})
            else:
                sales_by_week_dicc[product[0]] = {elem['create_date:week']: elem['product_uom_qty']}
        # Generamos un diccionario con el producto como clave y como valores un diccionario con el mes como clave y
        # las ventas que se han realizado en ese mes como valor
        # Ej: {4410:{'September 2020': 25.0,'April 2021': 21.0,'June 2020': 55.0}
        sales_by_month_dicc = {}
        for elem in sales_by_month:
            product = elem.get('product_id')
            if sales_by_month_dicc.get(product[0], False):
                sales_by_month_dicc[product[0]].update({elem['create_date:month']: elem['product_uom_qty']})
            else:
                sales_by_month_dicc[product[0]] = {elem['create_date:month']: elem['product_uom_qty']}

        #Buscamos y nos recorremos todos los packs/kits
        packs = self.env['mrp.bom'].search([])
        despacks = self.env['mrp.bom']
        for p in packs:
            #Sacamos el producto relacioando con el pack/kit
            product_pack = p.product_tmpl_id.product_variant_ids
            #Sacamos sus ventas por semana y mes de los diccioanrios correspondientes
            sales_pack_week = sales_by_week_dicc.get(product_pack.id, False)
            sales_pack_month = sales_by_month_dicc.get(product_pack.id, False)
            #Si el pack se encuentra en el diccionario por semanas asumiremos que también está en el de meses
            if sales_pack_week:
                #Nos recorremos cada elemento que compone el pack / kit y si el producto que lo compone está en el
                #diccionario de ventas semanales , añadimos a las ventas del producto que lo compone las ventas del
                #pack por las uds de ese producto que lleva el pack. Hacemos lo mismo con los meses
                for line in p.bom_line_ids:
                    product = line.product_id
                    qty = line.product_qty
                    sales_product = sales_by_week_dicc.get(product.id, False)
                    if sales_product:
                        for w, qty_w_p in sales_pack_week.items():
                            if sales_product.get(w, False):
                                sales_product[w] += qty_w_p * qty
                            else:
                                sales_product.update({w: sales_pack_week[w]})
                    sales_product = sales_by_month_dicc.get(product.id, False)
                    if sales_product:
                        for w, qty_w_p in sales_pack_month.items():
                            if sales_product.get(w, False):
                                sales_product[w] += qty_w_p * qty
                            else:
                                sales_product.update({w: sales_pack_month[w]})
                despacks += p
                #Eliminamos del diccionario de semanas y meses los packs/kits que hemos desglosado
                del sales_by_week_dicc[product_pack.id]
                del sales_by_month_dicc[product_pack.id]

        #Con los productos que tenemos con reemplazo, añadimos a las ventas semanales y mensuales del producto que lo reemplaza,
        # las ventas del producto reemplazo
        products_with_replacement = self.env['product.product'].search([('replacement_id', '!=', False)])
        for product in products_with_replacement:
            if sales_by_week_dicc.get(product.id, False):
                replacement_product = product.replacement_id
                sales_product_week = sales_by_week_dicc.get(product.id, False)
                sales_product_month = sales_by_month_dicc.get(product.id, False)
                if sales_by_week_dicc.get(replacement_product.id, False):
                    sales_replacement_week = sales_by_week_dicc.get(replacement_product.id, False)
                    for w, qty_w_p in sales_product_week.items():
                        if sales_replacement_week.get(w, False):
                            sales_replacement_week[w] += qty_w_p
                        else:
                            sales_replacement_week.update({w: sales_product_week[w]})
                    sales_replacement_month = sales_by_month_dicc.get(replacement_product.id, False)
                    for w, qty_w_p in sales_product_month.items():
                        if sales_replacement_month.get(w, False):
                            sales_replacement_month[w] += qty_w_p
                        else:
                            sales_replacement_month.update({w: sales_product_month[w]})
        #Ordenamos las fechas en las que se ha vendido algo para poder tratarlas más facilmente
        for k, v in sales_by_week_dicc.items():
            # formateamos el string que tenemos como fecha para poder ordenarlas de menor a mayor
            # (Ej : W21 2020-1, el -1 indica el primer día de esa semana. EN el caso de los meses el formato es April 2020)
            sales_by_week_dicc[k]['sorted_keys'] = sorted(sales_by_week_dicc[k],
                                                          key=lambda e: datetime.strptime(e + '-1', "W%V %G-%u"))

            sales_by_month_dicc[k]['sorted_keys'] = sorted(sales_by_month_dicc[k],
                                                           key=lambda e: datetime.strptime(e, "%B %Y"))
        #Sacamos los productos recurrentes con la cota que nos hayan pasado en el wizard y a partir de ahí calculamos
        # sus cuartiles, distancias, medias y unidades, y creamos los datos que vamos a mostrar
        recurrent_products_by_week = recurrent_products(sales_by_week_dicc, self.week_level)
        remove_products(sales_by_month_dicc, recurrent_products_by_week)
        quantiles_week = calculate_quantiles(sales_by_week_dicc, recurrent_products_by_week)
        distances_week = calculate_distances(quantiles_week)
        mean_weeks = mean_data(sales_by_week_dicc, recurrent_products_by_week, 9)
        uds_week = uds(quantiles_week, distances_week, mean_weeks)
        suggestion_id = self.env['purchase.suggestions'].create(
            {'month_level': self.month_level, 'week_level': self.week_level, 'date_from': self.date_from})
        self.create_suggestions(quantiles_week,distances_week,mean_weeks,uds_week,suggestion_id,'week')

        #Hacemos lo mismo pero con los meses
        recurrent_products_by_month = recurrent_products(sales_by_month_dicc, self.month_level, month_mode=True)
        quantiles_month = calculate_quantiles(sales_by_month_dicc, recurrent_products_by_month, month_mode=True)
        distances_month = calculate_distances(quantiles_month)
        mean_month = mean_data(sales_by_month_dicc, recurrent_products_by_month, 3)
        uds_month = uds(quantiles_month, distances_month, mean_month)
        self.create_suggestions(quantiles_month, distances_month, mean_month, uds_month, suggestion_id, 'month')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Suggestions'),
            'res_model': 'purchase.suggestions',
            'res_id': suggestion_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'main'
        }

    def create_suggestions(self,quantiles_by_product,distances_by_product,mean_by_product,uds_by_product,suggestion_id,calculated_by):
        #Creamos los datos a mostrar a partirde los datos calculados
        for product in quantiles_by_product.keys():
            quantiles = quantiles_by_product[product]
            distances = distances_by_product[product]
            mean = mean_by_product[product]
            uds = uds_by_product[product]
            self.env['purchase.suggestions.statistics'].create(
                {'min': quantiles['min'], 'q0': quantiles['q0'], 'q1': quantiles['q1'], 'q2': quantiles['q2'],
                 'q3': quantiles['q3'], 'q4': quantiles['q4'], 'max': quantiles['max'], 'd1': distances['d1'],
                 'd2': distances['d2'], 'd3': distances['d3'], 'd4': distances['d4'], 'mean': mean,
                 'suggestion_id': suggestion_id.id, 'calculated_by': calculated_by, 'product_id': product
                 })
            self.env['purchase.suggestions.line'].create(
                {'suggestion_id': suggestion_id.id, 'calculated_by': calculated_by, 'product_id': product, 'qty': uds})
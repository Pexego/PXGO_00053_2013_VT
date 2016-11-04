/*
 * Cada linea tendrá 2 reservas, 1 reserva en firme y otra temporal,
 * los cambios desde js se harán en la reserva temporal, si se descarta se eliminará la temporal
 * y si se guarda se eliminará la firme y se convertirá la temporal en firme
 * La reserva en firme
 * Casos posibles:
 *  Se crea una linea nueva: Se crea la temporal y si se guarda se pasa a firme
 *  Se modifica una linea, se modifica la temporal y si se guarda se convierte
 *  Se elimina una linea, se elimina la temporal, al guardar si no hay temporal se bora tambien la firme
 */
openerp.reserve_without_save_sale = function(instance) {
    instance.web.FormView.include({
        on_button_cancel: function(event){
            console.log('se cancela')
            return this._super.apply(this, arguments);
        }
    });
    instance.web.BufferedDataSet.include({
        create: function(data, options) {
            if (this._model.name == 'sale.order.line' && this.parent_view.datarecord.state == 'reserve') {
                console.log('entra en create editado')
                var dat = {
                    'product_id': data.product_id,
                    'qty': data.product_uom_qty,
                    'uom': data.product_uom,
                    'price_unit': data.price_unit,
                    'name': options.readonly_fields.name
                }
                if (this.parent_view.datarecord.warehouse_id instanceof Array) {
                    dat['warehouse'] = this.parent_view.datarecord.warehouse_id[0]
                } else {
                    dat['warehouse'] = this.parent_view.datarecord.warehouse_id
                }
                //Se crea un id unico para la reserva a crear.
                var date = new Date();
                var components = [
                    date.getYear(),
                    date.getMonth(),
                    date.getDate(),
                    date.getHours(),
                    date.getMinutes(),
                    date.getSeconds(),
                    date.getMilliseconds()
                ];

                var id = components.join("");
                dat['unique_js_id'] = id
                data['temp_unique_js_id'] = id
                var line_obj = this
                /*var wh_model = new instance.web.Model("stock.warehouse");
                console.log(dat['warehouse']);
                wh_model.query(['lot_stock_id']).filter([['id', '=', dat['warehouse']]]).all().then(function(wh){
                    console.log(wh);
                    dat['location_id'] = wh[0].lot_stock_id[0];
                    var model = new instance.web.Model("stock.reservation");
                    model.call("create",[dat], {context:new instance.web.CompoundContext()})
                    .then(function() {

                    });
                });*/
                $.ajax({
                    url: '/reservations/create/',
                    type: 'POST',
                    data: dat,
                    dataType: 'json',
                    timeout: 5000,
                })



            }

            return this._super.apply(this, arguments);
        },
        write: function(id, data, options) {
            if (this._model.name == 'sale.order.line' && this.parent_view.datarecord.state == 'reserve') {
                console.log(this.get('auxiliar_reserv_id'))
                var _this = this;
                this.cache.forEach(function(line) {
                    if (line.id == id) {
                        if(line['values']['temp_unique_js_id'] == ""){
                            var dat = {
                                'product_id': line['values']['product_id'][0],
                                'qty': line['values']['product_uom_qty'],
                                'uom': line['values']['product_uom'][0],
                                'price_unit': line['values']['price_unit'],
                                'name': line['values']['name']
                            }
                            if (_this.parent_view.datarecord.warehouse_id instanceof Array) {
                                dat['warehouse'] = _this.parent_view.datarecord.warehouse_id[0]
                            } else {
                                dat['warehouse'] = _this.parent_view.datarecord.warehouse_id
                            }
                            var date = new Date();
                            var components = [
                                date.getYear(),
                                date.getMonth(),
                                date.getDate(),
                                date.getHours(),
                                date.getMinutes(),
                                date.getSeconds(),
                                date.getMilliseconds()
                            ];

                            var js_id = components.join("");
                            dat['unique_js_id'] = js_id
                            data['temp_unique_js_id'] = js_id
                            line['values']['temp_unique_js_id'] = js_id
                            var line_obj = this
                            /*se buscan los cambios en las lineas antes de la
                             * llamada ajax para evitar que se sobreescriba.*/
                             var data_ser = {}
                            changed = line['values']

                            if(data.product_uom_qty &&  data.product_uom_qty != changed['product_uom_qty']){
                                dat['qty'] = data.product_uom_qty
                                dat['unique_js_id'] = changed['temp_unique_js_id']
                            }


                            if(data.product_id && data.product_id != changed['product_id']){
                                dat['product_id'] = data.product_id
                                data_ser['name'] = data['name']
                                data_ser['old_unique_js_id'] = changed['temp_unique_js_id']
                                var date = new Date();
                                var components_ = [
                                    date.getYear(),
                                    date.getMonth(),
                                    date.getDate(),
                                    date.getHours(),
                                    date.getMinutes(),
                                    date.getSeconds(),
                                    date.getMilliseconds()
                                ];

                                var new_id = components_.join("");
                                data_ser['unique_js_id'] = new_id
                                data['temp_unique_js_id'] = new_id
                            }
                            $.ajax({
                                url: '/reservations/create/',
                                type: 'POST',
                                data: dat,
                                dataType: 'json',
                                timeout: 5000,
                                success: function(response_server){
                                    $.ajax({
                                        url: '/reservations/write/',
                                        type: 'POST',
                                        data: data_ser,
                                        dataType: 'json',
                                        timeout: 5000,
                                    });
                                }
                            });
                        }
                        else{
                            var dat = {}
                            changed = line['values']

                            if(data.product_uom_qty &&  data.product_uom_qty != changed['product_uom_qty']){
                                dat['qty'] = data.product_uom_qty
                                dat['unique_js_id'] = changed['temp_unique_js_id']
                            }


                            if(data.product_id && data.product_id != changed['product_id']){
                                dat['product_id'] = data.product_id
                                dat['name'] = data['name']
                                dat['old_unique_js_id'] = changed['temp_unique_js_id']
                                var date = new Date();
                                var components = [
                                    date.getYear(),
                                    date.getMonth(),
                                    date.getDate(),
                                    date.getHours(),
                                    date.getMinutes(),
                                    date.getSeconds(),
                                    date.getMilliseconds()
                                ];

                                var new_id = components.join("");
                                dat['unique_js_id'] = new_id
                                data['temp_unique_js_id'] = new_id
                            }

                            $.ajax({
                                url: '/reservations/write/',
                                type: 'POST',
                                data: dat,
                                dataType: 'json',
                                timeout: 5000,
                            });
                        }
                    }
                });
            }
            return this._super.apply(this, arguments);
        },
        unlink: function(ids, callback, error_callback) {
            console.log('entra en unlink editado')
            if (this._model.name == 'sale.order.line' && this.parent_view.datarecord.state == 'reserve') {
                this.cache.forEach(function(line) {
                    if ($.inArray(line.id, ids) > -1) {
                        var to_delete_reserve = ""
                        if(line['values']['temp_unique_js_id'] != ""){
                            to_delete_reserve = line['values']['temp_unique_js_id']
                        }
                        if(line['values']['unique_js_id'] != ""){
                            to_delete_reserve = line['values']['unique_js_id']
                        }
                        if (to_delete_reserve != "") {
                            $.ajax({
                                url: '/reservations/unlink/',
                                type: 'POST',
                                data: {
                                    'unique_js_id': to_delete_reserve
                                },
                                dataType: 'json',
                                timeout: 5000,
                            });
                        }
                    }
                });
            }
            return this._super.apply(this, arguments);
        },
    });
};

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
odoo.define('reserve_without_save_sale', function(require) {
    "use strict";

    var relational_fields = require('web.relational_fields')

    relational_fields.FieldOne2Many.include({

        __get_line_vals: function(element, recordData) {
            return {
                'product_id': element.data.product_id.data.id,
                'qty': element.data.product_uom_qty,
                'uom': element.data.product_uom.data.id,
                'price_unit': element.data.price_unit,
                'name': element.data.name,
                'warehouse': recordData.warehouse_id.data.id,
                'order_id': recordData.id,
                'csrf_token': require('web.core').csrf_token
            }
        },

        __get_reserve_unique_id:  function() {
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
            return components.join("");
        },

        _saveLine: function(recordID) {
            /*
                Siempre que se abandona la linea se llama a _onSaveline,
                Tanto si se crea/edita como si no se hace nada.
                Desde la función no hay manera de saber que ha lanzado el evento.
            */
            var self = this
            var res = this._super.apply(this, arguments)
            if (self.model == 'sale.order'  && self.name == 'order_line' && self.recordData.state == 'reserve') {
                self.recordData.order_line.data.forEach(function(element){
                    if (element.id == recordID) {
                        if (element.data.product_id === false || element.data.product_uom === false){
                            return;
                        }
                        // Si no tiene reserva temporal la creamos siempre
                        if(element.data.temp_unique_js_id == ""){
                            var dat = self.__get_line_vals(element, self.recordData);
                            //Se crea un id unico para la reserva a crear.
                            var id = self.__get_reserve_unique_id();
                            dat['unique_js_id'] = id;
                            self._setValue({
                                operation: 'UPDATE',
                                id: element.id,
                                data: {'temp_unique_js_id': dat['unique_js_id']},
                            });
                            $.ajax({
                                url: '/reservations/create/',
                                type: 'POST',
                                data: dat,
                                dataType: 'json',
                                timeout: 5000,
                            });
                        }
                        else{
                            var data = self.__get_line_vals(element, self.recordData)
                            data['unique_js_id'] = element.data.temp_unique_js_id
                            // Generamos el id en javascript por si es necesario crear reserva nueva.
                            data['new_js_unique_id'] = self.__get_reserve_unique_id()
                            $.ajax({
                                url: '/reservations/write/',
                                type: 'POST',
                                data: data,
                                dataType: 'json',
                                timeout: 5000,
                                success: function(response){
                                    if(response != "" && response != true){
                                        self._setValue({
                                            operation: 'UPDATE',
                                            id: element.id,
                                            data: {'temp_unique_js_id': response['unique_js_id']},
                                        });
                                    }
                                }
                            });
                        }

                        return;
                    }
                });
            }
            return res
        },

        _onDeleteRecord: function(ev) {
            if (this.model == 'sale.order'  && this.name == 'order_line' && this.recordData.state == 'reserve') {
                this.recordData.order_line.data.forEach(function(element){
                    if (element.id == ev.data.id) {
                        var to_delete_reserve = ""
                        if(element.data.temp_unique_js_id != ""){
                            to_delete_reserve = element.data.temp_unique_js_id
                        }
                        if(element.data.unique_js_id != ""){
                            to_delete_reserve = element.data.unique_js_id
                        }
                        if (to_delete_reserve != "") {
                            $.ajax({
                                url: '/reservations/unlink/',
                                type: 'POST',
                                data: {
                                    'csrf_token': require('web.core').csrf_token,
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
});

odoo.define('reserve_without_save_sale_custom_it', function (require) {
    "use strict";

    var relational_fields = require('web.relational_fields');

    relational_fields.FieldOne2Many.include({

        __get_line_vals: function (element, recordData) {
            var res = this._super(element, recordData);
            if (element.data.route_id) {
                res['route_id'] = element.data.route_id.data.id;
            }
            return res
        }
    });
})


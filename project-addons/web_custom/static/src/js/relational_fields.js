odoo.define('web_custom.relational_fields', function (require) {
    "use strict";

    const session = require('web.session');
    const relational_fields = require('web.relational_fields');
    const FormFieldMany2ManyTags = relational_fields.FormFieldMany2ManyTags;

    FormFieldMany2ManyTags.include({
        /**
         * @override to add a group
         * @param {MouseEvent} event
         */
        _onOpenColorPicker: function (event) {
            let _super = this._super.bind(this);
            session.user_has_group('web_custom.group_select_tag_color').then(function (has_group) {
                if (has_group) {
                    _super(event);
                }
            });


        }

    })
})

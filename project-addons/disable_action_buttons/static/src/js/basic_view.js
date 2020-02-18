odoo.define('disable_action_buttons.BasicView', function (require) {
"use strict";

var session = require('web.session');
var BasicView = require('web.BasicView');
BasicView.include({
        init: function(viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            session.user_has_group('disable_action_buttons.group_archive_button').then(function(has_group) {
                if(!has_group) {
                    self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                };
            });
        },
    });
});
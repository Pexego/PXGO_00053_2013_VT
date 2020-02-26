odoo.define('disable_action_buttons.sidebar', function (require) {
"use strict";


var core = require('web.core');
var Sidebar = require('web.Sidebar');
var QWeb = core.qweb;

Sidebar.include({

    _redraw: function () {
        var self=this;
        this.$el.html(QWeb.render('Sidebar', {widget: this}));
        self.getSession().user_has_group('stock_custom.group_comercial_ext').then(function(has_group) {
            var cont=0;
            self.$('.o_dropdown').each(function () {
                if (!$(this).find('li').length || (has_group && cont==self.$('.o_dropdown').length-1)) {
                    $(this).hide();
                }
                cont++;
            });
            self.$("[title]").tooltip({
                delay: { show: 500, hide: 0}
            });
        });
    },


});

});

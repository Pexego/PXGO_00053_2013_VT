odoo.define('disable_action_buttons.sidebar', function (require) {
"use strict";


var core = require('web.core');
var Sidebar = require('web.Sidebar');
var QWeb = core.qweb;

Sidebar.include({

    _redraw: function () {
        var self=this;
        this._super.apply(this, arguments);
        self.getSession().user_has_group('stock_custom.group_comercial_ext').then(function(has_group) {
            var cont=0;
            self.$('.o_dropdown').each(function () {
                if (!$(this).find('li').length || (has_group && cont==self.$('.o_dropdown').length-1)) {
                    $(this).hide();
                }
                cont++;
            });
            if (has_group && self.getParent().renderer.viewType === 'list'){
                self.getSession().user_has_group('web_export_view.group_disallow_export_view_data_excel').then(function(has_group_xml){
                    if (!has_group_xml){
                        self.$el.find('.o_dropdown')
                                .first().append(QWeb.render(
                                    'WebExportTreeViewXls', {widget: self}));
                            self.$el.find('.export_treeview_xls').on('click',
                                self.on_sidebar_export_treeview_xls);
                    }
                });
            }
        });
    },


});

});

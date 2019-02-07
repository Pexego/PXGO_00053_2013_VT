openerp.web_disable_export_group = function(instance) {
"use strict";

    var _t = instance.web._t;
    var Model = instance.web.Model;
    var session = new instance.web.Session();

    instance.web.Sidebar.include({
        add_items: function(section_code, items) {
            var self = this;
            var _super = this._super;
            if (session.is_superuser) {
                _super.apply(this, arguments);
            } else {
                var model_res_users = new Model("res.users");
                model_res_users.call("has_group", ["web_disable_export_group.group_export_data"]).done(function(can_export) {
                    if (!can_export) {
                        var export_label = _t("Export");
                        var delete_label = _t("Delete");
                        var share_label = _t("Share");
                        var embed_label = _t("Embed");
                        var new_items = items;
                        if (section_code === "other") {
                            new_items = [];
                            for (var i = 0; i < items.length; i++) {
                                console.log("items[i]: ", items[i]);
                                if ((items[i]["label"] !== export_label) && (items[i]["label"] !== delete_label)
                                    && (items[i]["label"] !== share_label) && (items[i]["label"] !== embed_label)){
                                    new_items.push(items[i]);
                                }
                            }
                        }
                        if (new_items.length > 0) {
                            _super.call(self, section_code, new_items);
                        }
                    } else {
                        _super.call(self, section_code, items);
                    }
                });
            }
        }
    });
};

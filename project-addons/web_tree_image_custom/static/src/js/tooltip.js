odoo.define('web_tree_image_custom.web_tree_image', function(require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

	ListRenderer.include({
		_onHoverRecord_img: function (event) {
			var img_src = $(event.currentTarget).children('.img-responsive').attr('src')
	    	$(event.currentTarget).tooltip({
	    		title: "<img src="+img_src+" class='tooltip_image'/>",
	    		delay: 0,
	    	});
		}
	});

})



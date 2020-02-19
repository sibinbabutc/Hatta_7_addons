
openerp.hatta_crm = function(session) {
    var _t = session.web._t;
    var has_action_id = false;
    /* Extend the Sidebar to add Share and Embed links in the 'More' menu */
    session.web.Sidebar = session.web.Sidebar.extend({

        on_click_share_link: function(item) {
            alert("Function Disabled !!!!")
        },
    });
//    session.web.FormView = session.web.FormView.extend({
//    	on_button_duplicate: function() {
//    		alert("Option Unavailable")
//    	},
//    	on_button_delete: function() {
//    		alert("Option Unavailable")
//    	}
//    });
};


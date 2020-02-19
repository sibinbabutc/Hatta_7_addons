openerp.hatta_purchase = function (instance) {
    instance.web.ActionManager = instance.web.ActionManager.extend({
    	ir_actions_act_close_wizard_and_reload_view: function (action, options) {
        	if (!this.dialog) {
                options.on_close();
            }
            this.dialog_stop();
            this.inner_widget.views[this.inner_widget.active_view].controller.reload();
            return $.when();
        },
    });
    instance.mail.ThreadMessage = instance.mail.ThreadMessage.extend({
    	bind_events: function () {
    		this._super.apply(this, arguments);
    		this.$('.oe_forward').on('click', this.on_message_forward);
    	},
    	
    	on_message_forward:function (event) {
            event.stopPropagation();
            console.log(this)
            var self = this
            context = {
            	'default_model': self.model,
            	'default_res_id': self.res_id,
            	'default_use_template': false,
            	'default_composition_mode': 'comment',
            	'forward_message_id': self.id
            }
            var action = {
                    type: 'ir.actions.act_window',
                    res_model: 'mail.compose.message',
                    view_mode: 'form',
                    view_type: 'form',
                    views: [[false, 'form']],
                    target: 'new',
                    context: context,
                };
            this.do_action(action);
            return false;
        },
    });
}


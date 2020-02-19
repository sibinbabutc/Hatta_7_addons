openerp.hatta_crm = function(instance, m) {
var _t = instance.web._t,
    QWeb = instance.web.qweb;
    
    instance.web.WebClient.include({
        bind_hashchange: function() {
            var self = this;
            $(document.body).keydown(function (evt) {
                if (evt.keyCode === 116){
                	evt.preventDefault();
                }
            })
            this._super.apply(this, arguments);
        },
    });
};
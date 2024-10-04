odoo.define('bsd_payroll.action_url', function (require) {
    "use strict";

    var ActionManager = require('web.ActionManager');

    ActionManager.include({
        _executeURLAction: function (action, options) {
            if (action.type === 'ir.actions.act_url') {
                window.open(action.url, action.target || '_blank');  // Use '_blank' as the default target
                return $.Deferred().reject();
            }
            return this._super(action, options);
        },
    });
});



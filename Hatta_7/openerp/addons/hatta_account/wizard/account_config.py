# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

from openerp.tools.safe_eval import safe_eval

class account_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'
    _columns = {
                'pdc_rec_account': fields.many2one('account.account', 'PDC Receipt Account'),
                'pdc_issue_account': fields.many2one('account.account', 'PDC Issue Account'),
                'pdc_journal_id': fields.many2one('account.journal', 'PDC Journal'),
                'courier_account_id': fields.many2one('account.account', 'Courier Charges Account'),
                'duty_account_id': fields.many2one('account.account', 'Duty Account')
                }
    
    def get_default_courier_account_id(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'courier_account_id': safe_eval(icp.get_param(cr, uid,
                                                              'hatta_account.courier_account_id', 'False'))}
    
    def get_default_duty_account_id(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'duty_account_id': safe_eval(icp.get_param(cr, uid,
                                                           'hatta_account.duty_account_id', 'False'))}
    
    
    
    def get_default_pdc_rec_account(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'pdc_rec_account': safe_eval(icp.get_param(cr, uid,
                                                            'hatta_account.pdc_rec_account', 'False'))}
    
    def get_default_pdc_issue_account(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'pdc_issue_account': safe_eval(icp.get_param(cr, uid,
                                                            'hatta_account.pdc_issue_account', 'False'))}
    
    def get_default_pdc_journal_id(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'pdc_journal_id': safe_eval(icp.get_param(cr, uid,
                                                            'hatta_account.pdc_journal_id', 'False'))}
    
    
    def set_default_courier_account_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.courier_account_id:
            icp.set_param(cr, uid, 'hatta_account.courier_account_id',
                          config.courier_account_id.id or False)
    
    def set_default_duty_account_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.duty_account_id:
            icp.set_param(cr, uid, 'hatta_account.duty_account_id',
                        config.duty_account_id.id or False)
    
    
    def set_default_pdc_rec_account(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.pdc_rec_account:
            icp.set_param(cr, uid, 'hatta_account.pdc_rec_account',
                          config.pdc_rec_account.id or False)
    
    def set_default_pdc_issue_account(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.pdc_issue_account:
            icp.set_param(cr, uid, 'hatta_account.pdc_issue_account',
                        config.pdc_issue_account.id or False)
    
    def set_default_pdc_journal_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.pdc_journal_id:
            icp.set_param(cr, uid, 'hatta_account.pdc_journal_id',
                        config.pdc_journal_id.id or False)
    
account_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

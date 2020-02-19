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
                'discount_in_account': fields.many2one('account.account', 'Discount Received Account'),
                'discount_out_account': fields.many2one('account.account', 'Discount Allowed Account')
                }
    
    def get_default_discount_in_account(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'discount_in_account': safe_eval(icp.get_param(cr, uid,
                                                            'hatta_direct_discount.discount_in_account', 'False'))}
    
    def get_default_discount_out_account(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'discount_out_account': safe_eval(icp.get_param(cr, uid,
                                                            'hatta_direct_discount.discount_out_account', 'False'))}

    def set_default_discount_in_account(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.discount_in_account:
            icp.set_param(cr, uid, 'hatta_direct_discount.discount_in_account',
                          config.discount_in_account.id or False)
    
    def set_default_discount_out_account(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.discount_out_account:
            icp.set_param(cr, uid, 'hatta_direct_discount.discount_out_account',
                        config.discount_out_account.id or False)
    
account_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

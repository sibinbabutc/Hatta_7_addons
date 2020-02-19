# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 ZestyBeanz Technologies Pvt. Ltd.
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

from openerp.osv import fields, osv

import openerp.addons.decimal_precision as dp

class res_users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'sale_approve_limit': fields.float('Sale Approval Limit',
                                           digits_compute=dp.get_precision('Account')),
        'manager_id': fields.many2one('res.users', 'Manager')
        }
    
    _defaults = {
         'sale_approve_limit': 5000
         }
    
res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

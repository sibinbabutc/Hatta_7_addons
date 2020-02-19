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

from osv import osv, fields

class local_purchase_order(osv.osv):
    _name = 'local.purchase.order'
    _description = 'Local Purchase Order Model'
    
    _columns = {
            'purchase_id' : fields.many2one('purchase.order', 'Purchase Order', domain="[('transaction_type_id.local_purchase', '=', True)]"),
            'quantity' : fields.float('Quantity', digits=(2,2)),
            'invoice_line_id' : fields.many2one('account.invoice.line', 'Invoice Line')
                }
    
local_purchase_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
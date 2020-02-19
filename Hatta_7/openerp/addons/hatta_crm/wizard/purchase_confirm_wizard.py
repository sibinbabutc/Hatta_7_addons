# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

import openerp.addons.decimal_precision as dp
from openerp import netsvc

class sale_confirm_wizard(osv.osv):
    _name = 'purchase.confirm.wizard'
    _description = 'Purchase Confirmation Wizard'
    
    def default_get(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        active_id = context.get('active_id', False)
        if active_id:
            res['purchase_id'] = active_id
        res['name'] = "<b>All the lines in the RFQ is not selected. Net product cost will be recomputed. Do you want to continue?</b>"
        return res
    
    _columns = {
                'name': fields.text('Warning'),
                'purchase_id': fields.many2one('purchase.order', 'Sale Order')
                }
    
    def confirm_purchase(self, cr, uid, ids, context=None):
        purchase_pool= self.pool.get('purchase.order')
        line_pool = self.pool.get('purchase.order.line')
        wf_service = netsvc.LocalService("workflow")
        data = self.read(cr, uid, ids, context={})[0]
        purchase_id = data.get('purchase_id', (False))[0]
        if purchase_id:
            purchase_obj = purchase_pool.browse(cr, uid, purchase_id, context=context)
            line_ids = [x.id for x in purchase_obj.order_line if x.select_line == False]
            line_pool.unlink(cr, uid, line_ids, context=context)
        purchase_pool.recompute_cost_price(cr, uid, [purchase_id], context=context)
        wf_service.trg_validate(uid, 'purchase.order', purchase_id, 'purchase_confirm', cr)
        return True
    
sale_confirm_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

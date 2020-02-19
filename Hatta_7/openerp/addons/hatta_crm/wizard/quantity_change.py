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

class quantity_change(osv.osv_memory):
    _name = 'quantity.change'
    _description = 'Quantity Change'
    
    def default_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        pol_pool = self.pool.get('purchase.order.line')
        res = super(quantity_change, self).default_get(cr, uid, ids, context=context)
        if context.get('active_id', False) and \
                    context.get('active_model', '') in ['purchase.order.line']:
            pol_id = context.get('active_id', False)
            if pol_id:
                pol_obj = pol_pool.browse(cr, uid, pol_id, context=context)
                res['qty'] = pol_obj.product_qty or 0.00
                res['pol_id'] = pol_id
        return res
    
    _columns = {
                'qty': fields.float('Quantity',
                                    digits_compute= dp.get_precision('Product Unit of Measure')),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Order Line Ref')
                }
    
    def change_qty(self, cr, uid, ids, context=None):
        purchase_line_pool = self.pool.get('purchase.order.line')
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context={})[0]
        pol_id = data.get('pol_id', (False))[0]
        qty = data.get('qty', 0.00)
        purchase_line_pool.write(cr, uid, pol_id, {'product_qty': qty}, context=context)
        purchase_line_pool.distribute_cost(cr, uid, [pol_id], context=context)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
quantity_change()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class stock_partial_picking(osv.osv):
    _inherit = 'stock.partial.picking'
    
    def _get_line_amount(self, cr, uid, line, qty, product, context=None):
        res = super(stock_partial_picking, self)._get_line_amount(cr, uid, line, qty, product, context=context)
        discount = line.discount or 0.00
        res -= discount
        return res
    
    def _get_purchase_amount(self, cr, uid, purchase_line_ids,  qty_dict, product_dict, context=None):
        amount_total = super(stock_partial_picking, self)._get_purchase_amount(cr, uid, purchase_line_ids,  qty_dict, product_dict, context=context)
        purchase_line_obj = self.pool.get('purchase.order.line')
        picking_pool = self.pool.get('stock.picking')
        active_id = context.get('active_id', False)
        picking_obj = picking_pool.browse(cr, uid, active_id, context=context)
        order = picking_obj.purchase_id
        for charge in order.charge_ids:
            if charge.pay_to_cust:
                amount_total += charge.amount_fc or 0.00
        for line in purchase_line_obj.browse(cr, uid, purchase_line_ids, context=context):
            if line.select_line:
                for charge in line.charge_ids:
                    if charge.pay_to_cust:
                        amount_total += charge.amount_fc or 0.00
        amount_total -= order.discount
        amount_total -= order.rounding
        return amount_total
    
stock_partial_picking()   

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
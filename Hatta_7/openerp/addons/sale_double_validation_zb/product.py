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

class product_product(osv.osv):
    _inherit = 'product.product'
    
    def _get_booked_qty(self, cr, uid, ids, name, args, context=None):
        res = {}
        sale_order_line_pool = self.pool.get('sale.order.line')
        uom_pool = self.pool.get('product.uom')
        for product_obj in self.browse(cr, uid, ids, context=context):
            sale_order_line_ids = sale_order_line_pool.search(cr, uid,
                                                              [('order_id.state', '=', 'wait_for_approval'),
                                                               ('product_id', '=', product_obj.id)],
                                                              context=context)
            product_uom_id = product_obj.uom_id.id
            qty = 0.00
            for sale_line_obj in sale_order_line_pool.browse(cr, uid, sale_order_line_ids, context=context):
                tmp_qty = sale_line_obj.product_uom_qty or 0.00
                sale_line_uom_id = sale_line_obj.product_uom.id
                if sale_line_uom_id != product_uom_id:
                    tmp_qty = uom_pool._compute_qty(cr, uid, sale_line_uom_id, tmp_qty, product_uom_id)
                qty += tmp_qty
            res[product_obj.id] = qty
        return res
    
    
    _columns = {
        'qty_booked': fields.function(_get_booked_qty, type="float", digits_compute=dp.get_precision('Account'), string="Quantity Booked"),
        }
    
    
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
                              invoice_vals, context=None):
        res = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id,
                                                               invoice_vals, context=context)
        if move_line.purchase_line_id:
            res['total_discount'] = move_line.purchase_line_id.discount or 0.00
            if move_line.purchase_line_id.account_id:
                res['account_id'] = move_line.purchase_line_id.account_id.id or False
        return res
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        purchase_pool = self.pool.get('purchase.order')
        invoice_pool = self.pool.get('account.invoice')
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id, group,
                                                               type, context=context)
        for picking_obj in self.browse(cr, uid, ids, context=context):
            if picking_obj.purchase_id and not picking_obj.purchase_id.discount_applied:
                invoice_id = res.get(picking_obj.id, False)
                if invoice_id:
                    purchase_obj = picking_obj.purchase_id
                    discount_total = purchase_obj.discount + purchase_obj.rounding
                    invoice_pool.write(cr, uid, invoice_id, {'discount': discount_total}, context=context)
#                     invoice_line_vals = purchase_pool.get_discount_rounding_line(cr, uid, purchase_obj,
#                                                                                  invoice_id, context=context)
#                     if invoice_line_vals:
#                         invoice_line_id = invoice_line_pool.create(cr, uid, invoice_line_vals, context=context)
        return res
    
    _columns = {
        'shipping_ids' : fields.many2many('shipping.quotation', 'shipping_incoming_rel',
                                'shipping_id', 'incoming_id', string="Shipping Quotations")
                }
    

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _columns = {
        'shipping_ids' : fields.many2many('shipping.quotation', 'shipping_incoming_rel',
                                'shipping_id', 'incoming_id', string="Shipping Quotations")
                }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class pol_select_qty_adjust(osv.osv):
    _name = 'pol.select.qty.adjust'
    _description = 'POL Select Qty Adjust'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        purchase_order_line_pool = self.pool.get('purchase.order.line')
        claim_product_pool = self.pool.get('crm.product.lines')
        res = super(pol_select_qty_adjust, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            pol_obj = purchase_order_line_pool.browse(cr, uid, active_id, context=context)
            enq_obj = pol_obj.order_id and pol_obj.order_id.lead_id or False
            res['name'] = "<h3><b>Selection for the product %s in customer enquiry number %s is already made. Do you want to continue ?</b></h3>"%(pol_obj.product_id.name, enq_obj.reference)
            res['pol_id'] = pol_obj.id
            if enq_obj:
                same_pol_ids = purchase_order_line_pool.search(cr, uid, [('order_id.lead_id', '=', enq_obj.id),
                                                                         ('product_id', '=', pol_obj.product_id.id),
                                                                         ('state', '!=', 'cancel'),
                                                                         ('select_line', '=', True)], context=context)
                enq_product_qty = 0.00
                enq_product_ids = claim_product_pool.search(cr, uid, [('product_id', '=', pol_obj.product_id.id),
                                                                          ('lead_id', '=', enq_obj.id)], context=context)
                for enq_product_obj in claim_product_pool.browse(cr, uid, enq_product_ids, context=context):
                    enq_product_qty += enq_product_obj.product_uom_qty or 0.00
                res['enq_qty'] = enq_product_qty
                lines = []
                for same_pol_obj in purchase_order_line_pool.browse(cr, uid, same_pol_ids,
                                                                    context=context):
                    lines.append((0, 0, {
                                         'order_ref': same_pol_obj.order_id.id,
                                         'product_id': same_pol_obj.product_id.id,
                                         'supplier_id': same_pol_obj.partner_id.id,
                                         'customer_id': same_pol_obj.enq_customer_id and \
                                                                same_pol_obj.enq_customer_id.id,
                                         'lead_id': enq_obj.id,
                                         'product_qty': same_pol_obj.product_qty or 0.00,
                                         'currency_id': same_pol_obj.currency_id.id,
                                         'price_unit_fc': same_pol_obj.price_unit or 0.00,
                                         'price_unit_lc': same_pol_obj.unit_price_lc or 0.00,
                                         'pol_id': same_pol_obj.id,
                                         'state': same_pol_obj.state
                                         }))
                res['product_ids'] = lines
                    
        return res
    
    _columns = {
                'name': fields.text('Warning'),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Order Line'),
                'enq_qty': fields.float('Enquiry Quantity',
                                        digits_compute=dp.get_precision('Product Unit of Measure')),
                'product_ids': fields.one2many('pol.select.qty.adjust.line', 'wizard_id', 'Product Lines')
                }
    
    def change_qty(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        pol_pool = self.pool.get('purchase.order.line')
        pol_id = False
        for wizard_obj in self.browse(cr, uid, ids, context=context):
            for line in wizard_obj.product_ids:
                pol_obj = line.pol_id or False
                if pol_obj:
                    if pol_obj.product_qty != line.product_qty:
                        pol_obj.write({'product_qty': line.product_qty})
                        pol_pool.distribute_cost(cr, uid, [pol_obj.id], context=context)
            pol_id = wizard_obj.pol_id and wizard_obj.pol_id.id or False
        ctx = context.copy()
        ctx['overide'] = True
        if pol_id:
            pol_pool.select_po_line(cr, uid, [pol_id], context=ctx)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
pol_select_qty_adjust()

class pol_select_qty_adjust_line(osv.osv):
    _name = 'pol.select.qty.adjust.line'
    _description = 'POL Select Qty Adjust Lines'
    _columns = {
                'order_ref': fields.many2one('purchase.order', 'Order Reference'),
                'product_id': fields.many2one('product.product', 'Product'),
                'supplier_id': fields.many2one('res.partner', 'Supplier'),
                'customer_id': fields.many2one('res.partner', 'Customer'),
                'lead_id': fields.many2one('crm.lead', 'Customer Enq'),
                'product_qty': fields.float('Quantity',
                                            digits_compute=dp.get_precision('Product Unit of Measure')),
                'currency_id': fields.many2one('res.currency', 'Currency'),
                'price_unit_fc': fields.float('Price Unit FC',
                                              digits_compute=dp.get_precision('Account')),
                'price_unit_lc': fields.float('Price Unit LC',
                                              digits_compute=dp.get_precision('Account')),
                'subtotal_lc': fields.float('Subtotal LC',
                                            digits_compute=dp.get_precision('Account')),
                'pol_id': fields.many2one('purchase.order.line', 'Related POL'),
                'wizard_id': fields.many2one('pol.select.qty.adjust', 'Wizard'),
                'state': fields.selection([('draft', 'Draft'), ('bid', 'Bid'),
                                           ('confirmed', 'Confirmed'),
                                           ('cancel', 'Cancelled')], "State")
                }
pol_select_qty_adjust_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

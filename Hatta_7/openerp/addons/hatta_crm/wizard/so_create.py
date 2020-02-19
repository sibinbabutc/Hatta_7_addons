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

from tools.translate import _

class crm_make_sale(osv.osv_memory):
    _inherit = 'crm.make.sale'
    
    def get_selected_landing_cost(self, cr, uid, purchase_ids, context=None):
        res = {}
        purchase_pool = self.pool.get('purchase.order')
        uom_pool = self.pool.get('product.uom')
        for purchase_obj in purchase_pool.browse(cr, uid, purchase_ids, context=context):
            total_equipment_cost_lc = purchase_obj.total_equipment_cost_lc or 0.00
            total_expense_lc = purchase_obj.total_expenses or 0.00
            net_qty = 0.00
            for line in purchase_obj.order_line:
                if line.select_line:
                    product_uom = line.product_id and line.product_id.uom_id and \
                                     line.product_id.uom_id.id or False
                    line_uom_id = line.product_uom and line.product_uom.id or False
                    qty = line.product_qty or 0.00
                    if product_uom and line_uom_id and product_uom != line_uom_id:
                        qty = uom_pool._compute_qty(cr, uid, line_uom_id, qty, product_uom)
                    net_qty += qty
            net_expense = total_equipment_cost_lc + total_expense_lc
            if net_qty != 0.00:
                unit_expense = net_expense / net_qty
            else:
                unit_expense = net_expanse
            res[purchase_obj.id] = unit_expense
        return res
    
    def default_get(self, cr, uid, default=None, context=None):
        if context is None:
            context = {}
        lead_pool = self.pool.get('crm.lead')
        purchase_line_pool = self.pool.get('purchase.order.line')
        purchase_pool = self.pool.get('purchase.order')
        uom_pool = self.pool.get('product.uom')
        sale_pool = self.pool.get('sale.order')
        warning = ""
        res = super(crm_make_sale, self).default_get(cr, uid, default, context=context)
        lead_ids = context.get('active_ids', [])
        sale_ids = sale_pool.search(cr, uid, [('lead_id', 'in', lead_ids),
                                              ('state', '!=', 'cancel')],
                                    context=context)
        if sale_ids:
            warning += "<b>Customer Sale Quotation for this enquiry already exists.</b></br>"
        purchase_line_data = {}
        lines = []
        for lead_obj in lead_pool.browse(cr, uid, lead_ids, context=context):
            warn_selling = False
            cost_center_id = lead_obj.analytic_account_id and lead_obj.analytic_account_id.id or False
            res['payment_term_id'] = lead_obj.payment_term_id and lead_obj.payment_term_id.id or \
                                            False
            res['customer_po_no'] = lead_obj.customer_rfq or ''
            for lead_line in lead_obj.product_lines:
                purchase_line_obj = lead_line.selected_pol_id or False
                warn = False
                cust_sel = False
                got = False
                for pol_line in lead_line.pol_ids:
                    if pol_line.select_line:
                        if got:
                            warn = True
                        got = True
                    if pol_line.cust_selected:
                        cust_sel = True
                if warn and not cust_sel:
                    warning += "<b>Sale price for some of the product need to be calculated based on customer selection.</b>"
                if purchase_line_obj:
                    qty = purchase_line_obj.product_qty or 1.00
                    uom = purchase_line_obj.product_uom and purchase_line_obj.product_uom.id or \
                                            False
                    line_uom = lead_line.uom_id and lead_line.uom_id.id or False
                    if uom != line_uom:
                        qty = uom_pool._compute_qty(cr, uid, uom, qty, line_uom)
                    coeff = 1.00
                    if uom != line_uom:
                        coeff = uom_pool._compute_qty(cr, uid, uom, 1.00, line_uom)
                    selling_price = lead_line.price_unit or 0.00
                    factor = purchase_line_obj.order_id and purchase_line_obj.order_id.factor or 1.00
                    if selling_price <= 0.00:
                        warn_selling = True
                    vals = {
                            'sequence_no': lead_line.sequence_no,
                            'product_id': lead_line.product_id.id,
                            'qty': qty,
                            'uom_id': line_uom,
                            'cost_price_fc': purchase_line_obj.price_unit * coeff,
                            'total_cost_fc': purchase_line_obj.price_unit * coeff * qty,
                            'cost_price_lc': purchase_line_obj.unit_price_lc * coeff,
                            'total_cost_lc': purchase_line_obj.unit_price_lc * coeff * qty,
                            'factor': factor,
                            'selling_price_lc': selling_price,
                            'total_selling_price_lc': selling_price * qty,
                            'line_id': lead_line.id or False
                            }
                    lines.append((0, 0, vals))
            if warn_selling:
                warning += "<b>Sale price for some of the enquiry lines are <= 0.00</b></br>"
        if warning:
            warning += "<b> Do you want to continue?</b>"
        res['warning'] = warning
        res['line_ids'] = lines
        return res
    
    _columns = {
                'line_ids': fields.one2many('so.create.line', 'wizard_id', 'So Lines'),
                'warning': fields.text('Warning'),
                'delivery_date': fields.date('Delivery Date'),
                'payment_term_id': fields.many2one('account.payment.term', 'Payment Term'),
                'customer_po_no': fields.char('Customer PO Number', size=128)
                }
    
crm_make_sale()

class so_create_line(osv.osv_memory):
    _name = 'so.create.line'
    _description = 'SO create line'
    _columns = {
                'sequence_no': fields.char('Sequence', size=64, select=True),
                'product_id': fields.many2one('product.product', 'Product'),
                'qty': fields.float('Quantity'),
                'uom_id': fields.many2one('product.uom', 'UOM'),
                'cost_price_fc': fields.float('Cost Price FC'),
                'total_cost_fc': fields.float('Total Cost FC'),
                'cost_price_lc': fields.float('Cost Price LC'),
                'total_cost_lc': fields.float('Total Cost LC'),
                'factor': fields.float('Factor', digits=(16, 8)),
                'selling_price_lc': fields.float('Selling Price LC'),
                'total_selling_price_lc': fields.float('Total Selling Price LC'),
                'wizard_id': fields.many2one('crm.make.sale', 'Wizard Ref'),
                'line_id': fields.many2one('crm.product.lines', 'Line Ref')
                }
so_create_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

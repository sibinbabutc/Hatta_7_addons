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
from datetime import datetime
import time
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id]['amount_total'] -= sale_obj.discount
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'job_assigned': fields.boolean('Job Assigned'),
                'discount': fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'discount'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums', help="The amount without tax.", track_visibility='always'),
                'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'discount'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums', help="The tax amount."),
                'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'discount'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums', help="The total amount."),
                'cancel_note': fields.text(string="Cancellation Note"),
                }
    
    def _check_job_id(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            sale_ids = self.search(cr, uid, [('job_id','=',order.job_id.id)], context=context)
            date = '2016-07-05 14:09:25'
            if order.create_date > date and sale_ids and len(sale_ids) > 1:
                 return False
        return True
      
    _constraints = [
        (_check_job_id, 'Job No should be Unique for Sale Order', ['job_id']),
    ]
     
    def create(self, cr, uid, vals, context=None):
        res = super(sale_order, self).create(cr, uid, vals, context=context)
        job_pool = self.pool.get('job.account')
        sale_obj = self.browse(cr, uid, res, context=context)
        if not sale_obj.cost_center_id:
            osv.except_osv(_("Error !!!"),
                           _("Please define a cost center"))
        job_vals = {
                    'name': "?",
                    'partner_id': sale_obj.partner_id and sale_obj.partner_id.id or False,
                    'lead_id': sale_obj.lead_id and sale_obj.lead_id.id or False
                    }
        job_id = job_pool.create(cr, uid, job_vals, context=context)
        sale_obj.write({'job_id': job_id})
        return res
    
    def action_button_confirm(self, cr, uid, ids, context=None):
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.job_id and sale_obj.job_id.name == "?":
                raise osv.except_osv(_("Error !!!"),
                                     _("Please provide a job number ..."))
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        return res
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        transaction_type_pool = self.pool.get('transaction.type')
        obj_sequence = self.pool.get('ir.sequence')
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        sale_currency = order.currency_id
        company_currency = user_obj.company_id.currency_id
        exchange_rate = currency_pool._get_conversion_rate(cr, uid, sale_currency, company_currency,
                                                           context=context)
        if order:
            res['sale_id'] = order.id
            res['job_id'] = order.job_id and order.job_id.id or False
            res['parent_partner_id'] = order.partner_id.id or False
            res['exchange_rate'] = exchange_rate
            res['discount'] = order.discount or 0.00
            if order.cost_center_id:
                invoice_number = ''
                if order.unposted:
                    for invoice in order.invoice_ids:
                        if invoice.unposted and invoice.state == 'cancel':
                            invoice_number = invoice.internal_number or ''
                            res['internal_number'] = invoice_number
                            invoice.write({'internal_number': invoice_number + "Cancelled" + str(time.strftime('%d/%m/%Y %H:%M:%S')),
                                           'unposted': False})
                transaction_type_ids = transaction_type_pool.search(cr, uid,
                                                                    [('cost_center_id', '=', order.cost_center_id.id),
                                                                     ('model_id.model', '=', 'account.invoice'),
                                                                     ('refund', '=', False)],
                                                                    context=context)
                if transaction_type_ids:
                    res['transaction_type_id'] = transaction_type_ids[0]
                    res['cost_center_id'] = order.cost_center_id.id
                    tran_obj = transaction_type_pool.browse(cr, uid, transaction_type_ids[0], context=context)
                    if tran_obj.sequence_id and not invoice_number:
                        inv_number = obj_sequence.next_by_id(cr, uid,
                                                             tran_obj.sequence_id.id,
                                                             context=context)
                        res['internal_number'] = inv_number
        return res
    
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = (line.price_unit * line.product_uom_qty) - line.discount
            res[line.id] = price
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=False, context=context)
        res.update({'discount' : line.discount})
        return res
    
    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        product_uom_pool = self.pool.get('product.uom')
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = False
            if this.create_man_invoice:
                res[this.id] = False
                continue
            sale_line_uom_id = this.product_uom.id
            sale_line_qty = this.product_uom_qty or 0.00
            line_invoice_qty = 0.00
            for invoice_line in this.invoice_lines:
                if invoice_line.invoice_id.state != 'draft':
                    invoice_qty = invoice_line.quantity or 0.00
                    invoice_uom_id = invoice_line.uos_id.id
                    if sale_line_uom_id != invoice_uom_id:
                        invoice_qty = product_uom_pool._compute_qty(cr, uid, invoice_uom_id, invoice_qty, sale_line_uom_id)
                    line_invoice_qty += invoice_qty
            if line_invoice_qty >= sale_line_qty:
                res[this.id] = True
        return res
    
    def _order_lines_from_invoice(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute("""SELECT DISTINCT sol.id FROM sale_order_invoice_rel rel JOIN
                                                  sale_order_line sol ON (sol.order_id = rel.order_id)
                                    WHERE rel.invoice_id = ANY(%s)""", (list(ids),))
        return [i[0] for i in cr.fetchall()]
    
    _columns = {
                'create_man_invoice': fields.boolean('Create Another Invoice'),
                'invoiced': fields.function(_fnct_line_invoiced, string='Invoiced', type='boolean',
                                store={
                                    'account.invoice': (_order_lines_from_invoice, ['state'], 10),
                                    'sale.order.line': (lambda self,cr,uid,ids,ctx=None: ids, ['invoice_lines', 'create_man_invoice'], 10)}),
                'discount': fields.float('Discount', digits_compute= dp.get_precision('Discount')),
                'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
                }
sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

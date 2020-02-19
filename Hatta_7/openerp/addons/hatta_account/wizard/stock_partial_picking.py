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

from lxml import etree
from openerp.osv.orm import setup_modifiers
from openerp import netsvc
from datetime import datetime
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp
import time

class stock_partial_picking(osv.osv):
    _inherit = 'stock.partial.picking'
    
    def default_get(self, cr, uid, field_names, context=None):
        if context is None:
            context = {}
        picking_pool = self.pool.get('stock.picking')
        res = super(stock_partial_picking, self).default_get(cr, uid, field_names, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            picking_obj = picking_pool.browse(cr, uid, active_id, context=context)
            if picking_obj.purchase_id:
                exchange_rate = picking_obj.purchase_id.exchange_rate or 0.00
                res['exchange_rate'] = exchange_rate
                res['exahange_value'] = picking_obj.purchase_id.amount_total * exchange_rate
                res['purchase_amount'] = picking_obj.purchase_id.amount_total
                res['supplier_invoice_date'] = picking_obj.purchase_id.supplier_invoice_date
        return res
    
    def onchange_invoice_date(self, cr, uid, ids, date_invoice, context=None):
        res = {}
        invoice_pool = self.pool.get('account.invoice')
        if date_invoice:
            date_obj = datetime.strptime(date_invoice,'%Y-%m-%d')
            first_day = date_obj + relativedelta(days=(date_obj.day * -1) + 1)
            last_day = first_day + relativedelta(day=1, months=+1, seconds=-1)
            print first_day, last_day
            old_po_ids = invoice_pool.search(cr, uid, [('date_invoice', '>=', first_day),
                                                       ('date_invoice', '<=', last_day),
                                                       ('type', '=', 'in_invoice'),
                                                       ('state', 'not in', ['draft', 'cancel'])],
                                        context=context)
            po_len = len(old_po_ids)
            len_part = po_len + 1
            month_part = date_obj.month
            if len_part < 10:
                len_part = "0" + str(len_part)
            if month_part < 10:
                month_part = "0" + str(month_part)
            po_name = "P" + str(len_part) + str(month_part) + str(date_obj.strftime("%y"))
            res['value'] = {
                            'po_num': po_name
                            }
        return res
    
    def onchange_ex_value(self, cr, uid, ids, exahange_value, purchase_amount):
        res = {'value': {}}
        if purchase_amount != 0.00:
            res['value']['exchange_rate'] = float(exahange_value) / float(purchase_amount)
        return res
    
    def _get_line_amount(self, cr, uid, line, qty, product, context=None):
        res = 0
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, qty, product, line.order_id.partner_id)
        cur = line.order_id.pricelist_id.currency_id
        res = cur_obj.round(cr, uid, cur, taxes['total'])
        return res
    
    def _get_purchase_amount(self, cr, uid, purchase_line_ids,  qty_dict, product_dict, context=None):
        amount = 0
        picking_pool = self.pool.get('stock.picking')
        cur_obj = self.pool.get('res.currency')
        purchase_line_obj = self.pool.get('purchase.order.line')
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        if context is None:
            context = {}
        active_id = context.get('active_id', False)
        picking_obj = picking_pool.browse(cr, uid, active_id, context=context)
        order = picking_obj.purchase_id
        amount_untaxed = 0.0
        amount_tax = 0.0
        amount_total = 0.0
        val = 0.0
        val1 = 0.0
        cur = order.pricelist_id.currency_id
        for line in purchase_line_obj.browse(cr, uid, purchase_line_ids, context=context):
            qty = qty_dict[line.id]
            product_id = self.pool.get('product.product').browse(cr, uid, product_dict[line.id], context=context)
            val1 += self._get_line_amount(cr, uid, line, qty, product_id, context=context)
            for c in tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, qty, product_id, order.partner_id)['taxes']:
                 val += c.get('amount', 0.0)
        amount_tax = cur_obj.round(cr, uid, cur, val)
        amount_untaxed = cur_obj.round(cr, uid, cur, val1)
        amount_total = amount_untaxed + amount_tax
        return amount_total
    
    def onchange_move_ids(self, cr, uid, ids, move_ids, context=None):
        res = {'value': {}}
        move_pool = self.pool.get('stock.move')
#         picking_pool = self.pool.get('stock.picking')
        purchase_amount = 0
        purchase_line_ids = []
        qty_dict = {}
        product_dict = {}
        qty = 0
        for move in move_ids:
            if move and move[2]:
                if move[2]['move_id']:
                    move_obj = move_pool.browse(cr, uid, move[2]['move_id'], context=context)
                    if move_obj.purchase_line_id:
                        qty = move[2]['quantity']
                        qty_dict.update({move_obj.purchase_line_id.id: qty})
                        product_dict.update({move_obj.purchase_line_id.id: move[2]['product_id']})
                        purchase_line_ids.append(move_obj.purchase_line_id.id)
        purchase_amount += self._get_purchase_amount(cr, uid, purchase_line_ids, qty_dict, product_dict, context=context)
        res['value']['exahange_value'] = purchase_amount
        res['value']['purchase_amount'] = purchase_amount
        if purchase_amount != 0.00:
            res['value']['exchange_rate'] = float(purchase_amount) / float(purchase_amount)
        return res
    
    _columns = {
                'date_invoice': fields.date('Accounting Date'),
                'po_num': fields.char('PO Booking Number', size=128),
                'exchange_rate': fields.float('Exchange Rate', digits=(16, 9)),
                'exahange_value': fields.float('Purchase Value', digits_compute=dp.get_precision('Account')),
                'purchase_amount': fields.float('Purchase Amount', digits_compute=dp.get_precision('Account')),
                'origin': fields.char('Supplier Invoice Number', size=128),
                'supplier_invoice_date': fields.date('Supplier Invoice Date')
                }
    
    _defaults = {
                 'date_invoice': lambda*a: time.strftime('%Y-%m-%d')
                 }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None,
                        toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(stock_partial_picking, self).fields_view_get(cr, uid, view_id, view_type,
                                                                 context=context, toolbar=toolbar,
                                                                 submenu=submenu)
        if view_type == 'form':
            type = context.get('default_type', False)
            doc = etree.XML(res['arch'])
            if type == 'out':
                for node in doc.xpath("//field[@name='date_invoice']"):
                    node.set('invisible', "True")
                    setup_modifiers(node, res['fields']['date_invoice'])
                for node in doc.xpath("//field[@name='po_num']"):
                    node.set('invisible', "True")
                    node.set('required', "False")
                    setup_modifiers(node, res['fields']['po_num'])
                for node in doc.xpath("//field[@name='exchange_rate']"):
                    node.set('invisible', "True")
                    node.set('required', "False")
                    setup_modifiers(node, res['fields']['exchange_rate'])
                for node in doc.xpath("//field[@name='exahange_value']"):
                    node.set('invisible', "True")
                    node.set('required', "False")
                    setup_modifiers(node, res['fields']['exahange_value'])
                for node in doc.xpath("//field[@name='origin']"):
                    node.set('invisible', "True")
                    node.set('required', "False")
                    setup_modifiers(node, res['fields']['origin'])
            if type == 'in':
                for node in doc.xpath("//button[@name='do_partial']"):
                    node.set('confirm', "Please Confirm Accounting Month !!!")
            res['arch'] = etree.tostring(doc)
        return res
    
    def do_partial(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice_shipping_pool = self.pool.get('stock.invoice.onshipping')
        invoice_pool = self.pool.get('account.invoice')
        picking_pool = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService('workflow')
        partial = self.browse(cr, uid, ids[0], context=context)
        data = self.read(cr, uid, ids, context={})[0]
        date_invoice = partial.date_invoice
        supplier_invoice_number = partial.origin
        supplier_invoice_date = partial.supplier_invoice_date
        po_num = partial.po_num or ''
        res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        picking = picking_pool.browse(cr, uid, partial.picking_id.id, context=context)
        if partial.picking_id.state != 'done' and partial.picking_id.backorder_id:
            picking = partial.picking_id.backorder_id
        else:
            picking = partial.picking_id
        if picking.type == 'in':
            picking.write({'invoice_date': date_invoice})
        else:
           picking.write({'invoice_date': time.strftime('%Y-%m-%d')})
        if picking.invoice_state == '2binvoiced' and picking.type == 'in':
            ctx = context.copy()
            ctx.update({'active_ids': [picking.id]})
            invoice_def_value = invoice_shipping_pool.default_get(cr, uid, ['journal_id', 'group',
                                                                            'invoice_date'],
                                                                  context=ctx)
            invoice_def_value.update({'invoice_date': date_invoice})
            invoice_pick_id = invoice_shipping_pool.create(cr, uid, invoice_def_value, context=ctx)
            invoice_data = invoice_shipping_pool.create_invoice(cr, uid, [invoice_pick_id],
                                                                context=ctx)
            invoice_id = invoice_data.get(picking.id, False)
            if invoice_id:
                invoice_pool.write(cr, uid, invoice_id, {'internal_number': po_num, 'exchange_rate': data.get('exchange_rate', 1.0000), 
                                                         'supplier_invoice_number': supplier_invoice_number,
                                                         'supplier_invoice_date': supplier_invoice_date})
                wf_service.trg_validate(uid, 'account.invoice', \
                                        invoice_id, 'invoice_open', cr)
        return res
    
stock_partial_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

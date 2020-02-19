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

from osv import fields,osv

import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from datetime import datetime
from openerp import netsvc
import time

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def _check_pick_exist(self, cr, uid, ids, name, args, context=None):
        res = {}
        for sale_obj in self.browse(cr, uid, ids, context=context):
            res[sale_obj.id] = False
            for picking in sale_obj.picking_ids:
                if picking.state != 'cancel':
                    res[sale_obj.id] = True
        return res
    
    _columns = {
                'lead_id': fields.many2one('crm.lead', 'Enquiry'),
                'id': fields.integer('ID'),
                'date_delivery': fields.date('Delivery Date'),
                'delivery_terms': fields.char('Delivery Term', size=128),
                'date_confirm': fields.datetime('Run Date', readonly=True,
                                                select=True, help="Date on which sales order is confirmed."),
                'unposted': fields.boolean('Unposted ?'),
                'direct_po_id': fields.many2one('purchase.order', 'Purchase Order'),
                'overwrite_po_check': fields.boolean('Override PO Check'),
                'picking_exist': fields.function(_check_pick_exist, type="boolean",
                                                 string="Picking Exists")
                }
    
    def view_direct_purchase_orders(self, cr, uid, ids, context=None):
        po_pool = self.pool.get('purchase.order')
        po_ids = po_pool.search(cr, uid, [('direct_sale_id', 'in', ids)])
        if not po_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("No Po Found"))
        return {
                'name': 'Request For Quotations',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', po_ids)],
                'context': context,
                }
    
    def onchange_transaction_type(self, cr, uid, ids, transaction_type_id, context=None):
        res = {'value': {}}
        transaction_pool = self.pool.get('transaction.type')
        if transaction_type_id:
            tran_obj = transaction_pool.browse(cr, uid, transaction_type_id, context=context)
            res['value']['cost_center_id'] = tran_obj.cost_center_id and tran_obj.cost_center_id.id or False
        return res
    
    def create_po(self, cr, uid, ids, supplier_list, context=None):
        po_pool = self.pool.get('purchase.order')
        transaction_type_pool = self.pool.get('transaction.type')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_curr_id = user_obj.company_id.currency_id.id
        purchase_ids = []
        for sale_obj in self.browse(cr, uid, ids, context=context):
            analytic_account_id = sale_obj.cost_center_id and \
                                        sale_obj.cost_center_id.id or False
            transaction_type_id = False
            if analytic_account_id:
                transaction_type_ids = transaction_type_pool.search(cr, 1, [('cost_center_id', '=', analytic_account_id),
                                                                              ('model_id.model', '=', 'purchase.order')])
                if transaction_type_ids:
                    transaction_type_id = transaction_type_ids[0]
            if not transaction_type_id:
                raise osv.except_osv(_("Error !!!"),
                                     _("Please configure transaction type."))
            if sale_obj.direct_po_id:
                raise osv.except_osv(_("Error !!!"),
                                     _("A purchase order already exists !!!"))
            lines = []
            for line in sale_obj.order_line:
                certificate_ids = [(4, x.id) for x in line.certificate_ids]
                product_obj = line.product_id
                line_vals = {
                             'product_id': line.product_id and line.product_id.id or False,
                             'product_qty': line.product_uom_qty or 0.00,
                             'account_id': product_obj.property_account_expense and \
                                                product_obj.property_account_expense.id or \
                                                product_obj.categ_id and \
                                                product_obj.categ_id.property_account_expense_categ and \
                                                product_obj.categ_id.property_account_expense_categ.id or False,
                             'product_uom': line.product_uom and line.product_uom.id or False,
                             'name': line.name or '',
                             'price_unit': 0.00,
                             'date_planned': time.strftime("%Y-%m-%d"),
                             'certificate_ids': certificate_ids,
                             'sequence_no': line.sequence_no,
                             'select_line': True
                             }
                lines.append((0, 0, line_vals))
            for supplier_id in supplier_list:
                purchase_vals = {
                                 'partner_id': supplier_id,
                                 'direct_sale_id': sale_obj.id,
                                 'transaction_type_id': transaction_type_id,
                                 'analytic_account_id': analytic_account_id,
                                 'foreign_currency': company_curr_id
                                 }
                default_value = po_pool.default_get(cr, uid, ['warehouse_id'])
                purchase_vals.update(default_value)
                sale_order_onchange_data = po_pool.onchange_partner_id(cr, uid, ids, supplier_id)
                purchase_vals.update(sale_order_onchange_data.get('value', {}))
                purchase_vals.update({'order_line': lines})
                pricelist_id = purchase_vals.get('pricelist_id', False)
                print pricelist_id,"---->pricelist_id"
                if pricelist_id:
                    pricelist_onchange_data = po_pool.onchange_pricelist(cr, uid, ids,
                                                                         pricelist_id, context=context)
                    purchase_vals.update(pricelist_onchange_data.get('value', {}))
                currency_id = purchase_vals.get('currency_id', False)
                print currency_id
                if currency_id:
                    curr_onchange_data = po_pool.onchange_currency(cr, uid, ids, company_curr_id, currency_id)
                    purchase_vals.update(curr_onchange_data.get('value', {}))
                warehouse_id = purchase_vals.get('warehouse_id', False)
                if warehouse_id:
                    ware_onchange_data = po_pool.onchange_warehouse_id(cr, uid, ids, warehouse_id)
                    purchase_vals.update(ware_onchange_data.get('value', {}))
                print purchase_vals,"llllllllllllllllllllllllll\n\n\n"
                purchase_id = po_pool.create(cr, uid, purchase_vals, context=context)
                sale_obj.write({'direct_po_id': purchase_id})
                purchase_ids.append(purchase_id)
        return {
                'name': 'Request For Quotations',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', purchase_ids)],
                'context': context,
                }
    
    def create(self, cr, uid, vals, context=None):
        tran_pool = self.pool.get('transaction.type')
        obj_sequence = self.pool.get('ir.sequence')
        if vals.get('transaction_type_id', False):
            tran_obj = tran_pool.browse(cr, uid, vals['transaction_type_id'], context=context)
            if tran_obj.sequence_id:
                vals['name'] = obj_sequence.next_by_id(cr, uid, tran_obj.sequence_id.id, context=context)
        res = super(sale_order, self).create(cr, uid, vals, context=context)
        return res
    
    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        res = super(sale_order, self)._get_date_planned(cr, uid, order, line, start_date,
                                                        context=context)
        if order.date_delivery:
            return order.date_delivery
        return res
    
    def button_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for sale_obj in self.browse(cr, uid, ids, context=context):
            for picking in sale_obj.picking_ids:
                if picking.state not in ['draft', 'cancel']:
                    raise osv.except_osv(_("Error !!!"),
                                         _("Please unpost delivery before proceeding !!!"))
            for invoice in sale_obj.invoice_ids:
                if invoice.state not in ['draft', 'cancel']:
                    raise osv.except_osv(_("Error !!!"),
                                         _("Please unpost invoice before proceeding !!!"))
            if sale_obj.state == 'done':
                wf_service.trg_validate(uid, 'sale.order', \
                                        sale_obj.id, 'done_cancel', cr)
            elif sale_obj.state in ['invoice_except', 'manual']:
                wf_service.trg_validate(uid, 'sale.order', \
                                        sale_obj.id, 'invoice_cancel', cr)
            for line in sale_obj.order_line:
                line.write({'state': 'draft'})
        self.action_cancel_draft(cr, uid, ids)
        self.write(cr, uid, ids, {'unposted': True})
        return True
    
    def action_button_confirm_ini(self, cr, uid, ids, context=None):
        sale_line_pool = self.pool.get('sale.order.line')
        uom_pool = self.pool.get('product.uom')
        uom_obj = self.pool.get('product.uom')
        obj_model = self.pool.get('ir.model.data')
        purchase_pool = self.pool.get('purchase.order')
        show_warning = False
        purchase_product_qty_data = {}
        curr_sale_qty_data = {}
        for sale_obj in self.browse(cr, uid, ids, context = context):
            if sale_obj.lead_id:
                purchase_ids = purchase_pool.search(cr, uid, [('lead_id', '=', sale_obj.lead_id.id),
                                                              ('state', 'not in', ['draft', 'cancel', 'sent', 'bid'])],
                                                    context=context)
            else:
                purchase_ids = purchase_pool.search(cr, uid, [('direct_sale_id', '=', sale_obj.id),
                                                              ('state', 'not in', ['draft', 'cancel', 'sent', 'bid'])],
                                                    context=context)
            for purchase_obj in purchase_pool.browse(cr, uid, purchase_ids, context=context):
                for line in purchase_obj.order_line:
                    po_qty = line.product_qty
                    product_base_uom = line.product_id and line.product_id.uom_id and \
                                            line.product_id.uom_id.id or False
                    line_uom = line.product_uom and line.product_uom.id or False
                    factor = 1.00
                    if product_base_uom and line_uom and product_base_uom != line_uom:
                        factor = uom_pool._compute_qty(cr, uid, line_uom, po_qty, product_base_uom)
                    if not purchase_product_qty_data.get(line.product_id.id, False):
                        purchase_product_qty_data[line.product_id.id] = 0.00
                    purchase_product_qty_data[line.product_id.id] += po_qty * factor
            for line in sale_obj.order_line:
                sale_qty = line.product_uom_qty
                sale_uom_id = line.product_uom and line.product_uom.id or False
                product_uom_id = line.product_id and line.product_id.uom_id.id or False
                factor = 1.00
                if sale_uom_id and product_uom_id and sale_uom_id != product_uom_id:
                    factor = uom_pool._compute_qty(cr, uid, sale_uom_id, sale_qty, product_uom_id)
                if not curr_sale_qty_data.get(line.product_id.id, False):
                    curr_sale_qty_data[line.product_id.id] = 0.00
                curr_sale_qty_data[line.product_id.id] += sale_qty * factor
            if not sale_obj.overwrite_po_check:
                for sale_product in curr_sale_qty_data:
                    sale_qty = curr_sale_qty_data[sale_product]
                    purchase_qty = purchase_product_qty_data.get(sale_product, 0.00)
                    if purchase_qty < sale_qty:
                        raise osv.except_osv(_("Error!!!"),
                                             _("Please create po for all the product in sale order before proceeding !!!"))
            if sale_obj.lead_id:
                lead_obj = sale_obj.lead_id or False
                sale_qty_dict = {}
                enq_qty_dict = {}
                for line in lead_obj.product_lines:
                    line_uom_id = line.uom_id.id
                    product_uom_id = line.product_id.uom_id.id or False
                    line_qty = line.product_uom_qty or 0.00
                    if line_uom_id != product_uom_id:
                        line_qty = uom_pool._compute_qty(cr, uid, line_uom_id, line_qty,
                                                         product_uom_id)
                    if enq_qty_dict.get(line.product_id.id, False):
                        enq_qty_dict[line.product_id.id] += line_qty
                    else:
                        enq_qty_dict[line.product_id.id] = line_qty
                sale_line_ids = sale_line_pool.search(cr, uid, [('order_id.lead_id', '=', sale_obj.lead_id.id),
                                                                ('order_id.state', 'not in', ['draft', 'cancel'])],
                                                      context=context)
                for sale_line_obj in sale_line_pool.browse(cr, uid, sale_line_ids, context=context):
                    if sale_line_obj.product_id:
                        line_uom_id = sale_line_obj.product_uom.id
                        product_uom_id = sale_line_obj.product_id.uom_id.id
                        line_qty = sale_line_obj.product_uom_qty or 0.00
                        if line_uom_id != product_uom_id:
                            line_qty = uom_obj._compute_qty(cr, uid, line_uom_id, line_qty, product_uom_id)
                        if sale_qty_dict.get(sale_line_obj.product_id.id, False):
                            sale_qty_dict[sale_line_obj.product_id.id] += line_qty
                        else:
                            sale_qty_dict[sale_line_obj.product_id.id] = line_qty
                for sale_line_obj in sale_obj.order_line:
                    if sale_line_obj.product_id:
                        line_uom_id = sale_line_obj.product_uom.id
                        product_uom_id = sale_line_obj.product_id.uom_id.id
                        line_qty = sale_line_obj.product_uom_qty or 0.00
                        if line_uom_id != product_uom_id:
                            line_qty = uom_obj._compute_qty(cr, uid, line_uom_id, line_qty, product_uom_id)
                        if sale_qty_dict.get(sale_line_obj.product_id.id, False):
                            sale_qty_dict[sale_line_obj.product_id.id] += line_qty
                        else:
                            sale_qty_dict[sale_line_obj.product_id.id] = line_qty
                for product_id in enq_qty_dict:
                    enq_qty = enq_qty_dict[product_id]
                    sale_qty = sale_qty_dict.get(product_id, 0.00)
                    if sale_qty < enq_qty:
                        show_warning = True
                        pass
        if show_warning:
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),
                                                      ('name','=','sale_confirmation_wizard_form')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            context['active_model'] = self._name
            context['active_ids'] = ids
            context['active_id'] = ids[0]
            return {
                    'name': _('Confirm Sale'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.confirm.wizard',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': context,
                    }
        else:
            res = self.action_button_confirm(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'date_confirm': datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                   context=context)
        return res
    
    def action_ship_create(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
        for sale_obj in self.browse(cr, uid, ids, context=context):
            for picking in sale_obj.picking_ids:
                if picking.state == 'confirmed':
                    picking.action_assign()
        return res
    
    
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        res = super(sale_order, self)._prepare_order_line_move(cr, uid, order, line, picking_id,
                                                               date_planned, context=context)
        res['sequence_no'] = line.sequence_no or ''
        print res
        return res
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        transaction_type_pool = self.pool.get('transaction.type')
        obj_sequence = self.pool.get('ir.sequence')
        pick_name = ''
        res = {
               'origin': order.name,
               'date': self.date_to_datetime(cr, uid, order.date_order, context),
               'type': 'out',
               'state': 'auto',
               'move_type': order.picking_policy,
               'sale_id': order.id,
               'partner_id': order.partner_shipping_id.id,
               'note': order.note,
               'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
               'company_id': order.company_id.id,
               'shop_id': order.shop_id and order.shop_id.id or False,
               'client_order_ref': order.client_order_ref or ''
               }
        if order.cost_center_id:
            cost_center_id = order.cost_center_id.id
            transaction_type_ids = transaction_type_pool.search(cr, uid, [('model_id.model', '=', 'stock.picking.out'),
                                                                          '|', ('cost_center_id', '=', cost_center_id),
                                                                          ('cost_center_id', '=', False),
                                                                          ('refund', '=', False)])
            if transaction_type_ids:
                transaction_type_id = transaction_type_ids[0]
                tran_obj = transaction_type_pool.browse(cr, uid, transaction_type_id, context=context)
                res['transaction_type_id'] = transaction_type_id
#                 if tran_obj.sequence_id and not pick_name:
#                     pick_name = obj_sequence.next_by_id(cr, uid,
#                                                         tran_obj.sequence_id.id,
#                                                         context=context)
            else:
                raise osv.except_osv(_("Error !!!"),
                                     _("Please configure transaction type"))
            res['cost_center_id'] = cost_center_id
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        res['unpost_name'] = pick_name
        res['job_id'] = order.job_id and order.job_id.id or False
        res['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return res
    
    
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
                'sequence_no': fields.char('Sequence', size=64, select=True),
                'type': fields.selection([('make_to_stock', 'from stock'), ('make_to_order', 'on order'), ('opportunity', 'opportunity')], 'Procurement Method', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                         help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced."),
                'date_order': fields.related('order_id', 'date_order', type="date", string="Order Date"),
                'certificate_ids': fields.many2many('product.certificate', 'cert_sale_rel', 'sale_line_id', 'certificate_id',
                                                    'Certificate(s)'),
                'crm_line_id': fields.many2one('crm.product.lines', 'CRM Line Ref.'),
                'job_id': fields.related('order_id', 'job_id', type='many2one',
                                         relation="job.account", string="Job No.", store=True),
                'pol_remark': fields.text('Purchase Remark')
                }
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line,
                                                                            account_id,
                                                                            context=context)
        res['sequence_no'] = line.sequence_no or ''
        return res
    
sale_order_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

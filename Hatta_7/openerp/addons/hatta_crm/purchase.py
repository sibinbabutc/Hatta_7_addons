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

from osv import fields, osv

from tools.translate import _
from openerp.tools import float_compare
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from datetime import date, timedelta
from lxml import etree
import time

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
    def onchange_date_order(self, cr, uid, ids, date_order, context=None):
        res = {'value': {}}
        period_pool = self.pool.get('account.period')
        if date_order:
            period_ids = period_pool.find(cr, uid, date_order, context=context)
            res['value']['period_id'] = period_ids and period_ids[0] or False
        return res
    
    def check_amount_total(self, cr, uid, amount_total, context=None):
        if not amount_total:
            raise osv.except_osv(_('Error!'), _('You cannot confirm the Purchase order since it has no total amount'))
        return True
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        sale_pool = self.pool.get('sale.order')
        sale_line_pool = self.pool.get('sale.order.line')
        po_line_pool = self.pool.get('purchase.order.line')
        uom_pool = self.pool.get('product.uom')
        for po_obj in self.browse(cr, uid, ids, context=context):
            self.check_amount_total(cr, uid, po_obj.amount_total, context=context)
            enq_obj = po_obj.lead_id or False
            po_qty_dict = {}
            sale_qty_dict = {}
            if enq_obj:
                sale_line_ids = sale_line_pool.search(cr, uid, [('order_id.lead_id', '=', enq_obj.id),
                                                                ('order_id.state', 'not in', ['draft', 'cancel'])],
                                                      context=context)
                for sale_line_obj in sale_line_pool.browse(cr, uid, sale_line_ids, context=context):
                    if sale_line_obj.product_id:
                        product_uom_id = sale_line_obj.product_id.uom_id.id or False
                        sale_line_uom = sale_line_obj.product_uom.id or False
                        sale_line_qty = sale_line_obj.product_uom_qty or 0.00
                        if product_uom_id != sale_line_uom:
                            sale_line_qty = uom_pool._compute_qty(cr, uid, sale_line_uom, sale_line_qty,
                                                                  product_uom_id)
                        if sale_qty_dict.get(sale_line_obj.product_id.id, False):
                            sale_qty_dict[sale_line_obj.product_id.id] += sale_line_qty
                        else:
                            sale_qty_dict[sale_line_obj.product_id.id] = sale_line_qty
                recompute = False
                for line in po_obj.order_line:
                    if line.cust_selected:
                        product_uom_id = line.product_id.uom_id.id or False
                        line_uom_id = line.product_uom and line.product_uom.id or product_uom_id
                        line_qty = line.product_qty or 0.00
                        if product_uom_id != line_uom_id:
                            line_qty = uom_pool._compute_qty(cr, uid, line_uom_id, line_qty, product_uom_id)
                        if po_qty_dict.get(line.product_id.id, False):
                            po_qty_dict[line.product_id.id] += line_qty
                        else:
                            po_qty_dict[line.product_id.id] = line_qty
                    else:
                        rem_amount_charge = po_obj.rem_line_charge or 0.00
                        if not line.select_line:
#                             rem_amount_charge += line.price_subtotal or 0.00
#                             po_obj.write({'rem_line_charge': rem_amount_charge})
                            po_line_pool.write(cr, uid, [line.id], {'select_line': False}, context=context)
                            po_line_pool.unlink(cr, uid, [line.id], context=context)
                            recompute = True
                if recompute:
                    self.recompute_cost_price(cr, uid, [po_obj.id], context=context)
                po_line_ids = po_line_pool.search(cr, uid, [('order_id.lead_id', '=', enq_obj.id),
                                                            ('state', 'in', ['confirmed', 'done'])],
                                                  context=context)
                for line in self.browse(cr, uid, po_line_ids, context=context):
                    if po_qty_dict.get(line.product_id.id, False):
                        product_uom_id = line.product_id.uom_id.id or False
                        line_uom_id = line.product_uom and line.product_uom.id or product_uom_id
                        line_qty = line.product_qty or 0.00
                        if product_uom_id != line_uom_id:
                            line_qty = uom_pool._compute_qty(cr, uid, line_uom_id, line_qty, product_uom_id)
                        po_qty_dict[line.product_id.id] += line_qty
                for purchase in po_qty_dict:
                    qty = po_qty_dict[purchase]
                    sale_qty = sale_qty_dict.get(purchase, 0.00)
                    if sale_qty < qty and not po_obj.over_sale_qty_check:
                        raise osv.except_osv(_('Error!'), _('You cannot confirm the Purchase order as the sale order in the customer enquiry is not confirmed'))
        res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        return res
    
    def purchase_confirm(self, cr, uid, ids, context=None):
        obj_model = self.pool.get('ir.model.data')
        unselect_line_ids = []
        for purchase_obj in self.browse(cr, uid, ids, context=context):
            if not purchase_obj.payment_term_id:
                raise osv.except_osv(_("Error !"),
                                     _("Payment Term not defined !!!!"))
            unselect_line_ids.extend([x.id for x in purchase_obj.order_line if x.select_line == False])
            lead_id = purchase_obj.lead_id and purchase_obj.lead_id.id or False
        if unselect_line_ids:
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),
                                                      ('name','=','purchase_confirmation_wizard_form')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            context['active_model'] = self._name
            context['active_ids'] = ids
            context['active_id'] = ids[0]
            return {
                    'name': _('Confirm Purchase Order'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'purchase.confirm.wizard',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': context,
                    }
        else:
            wf_service = netsvc.LocalService("workflow")
            for id in ids:
                wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_confirm', cr)
        return True
    
    def unvalidate_po(self, cr, uid, ids, context=None):
        for po_obj in self.browse(cr, uid, ids, context=context):
            rfq_no = po_obj.unused_seq
            po_no = po_obj.name
            vals = {'state': 'bid', 'name': po_no, 'unused_seq': po_no, 'edit_po': True}
            if po_obj.direct_purchase:
                vals['state'] = 'draft'
                for line in po_obj.order_line:
                    line.write({'state': 'draft'})
            po_obj.write(vals)
        return True
    
    def view_sale_quotation(self, cr, uid, ids, context=None):
        sale_ids = []
        sale_order_pool = self.pool.get('sale.order')
        for po_obj in self.browse(cr, uid, ids, context=context):
            enq_id = po_obj.lead_id and po_obj.lead_id.id or False
            if enq_id:
                sale_ids = sale_order_pool.search(cr, uid, [('lead_id', '=', enq_id)], context=context)
        return {
                'name': 'Sale Quotations',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', sale_ids)],
                'context': {}
                }
    
    def view_options(self, cr, uid, ids, context=None):
        purchase_ids = self.search(cr, uid, [('parent_po_id', 'in', ids)], context=context)
        return {
                'name': 'Purchase Options',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', purchase_ids)],
                'context': {}
                }
    
    def distribute_cost(self, cr, uid, ids, context=None):
        purchase_line_pool = self.pool.get('purchase.order.line')
        for purchase_obj in self.browse(cr, uid, ids, context=context):
            pol_ids = [x.id for x in purchase_obj.order_line]
            purchase_line_pool.write(cr, uid, pol_ids, {'cost_distributed': True},
                                     context=context)
        self.recompute_cost_price(cr, uid, ids, context=context)
        return True
    
    def cancel_distribution(self, cr, uid, ids, context=None):
        pol_ids = []
        pol_pool = self.pool.get('purchase.order.line')
        for po_obj in self.browse(cr, uid, ids, context=context):
            pol_ids.extend([x.id for x in po_obj.order_line])
        return pol_pool.cancel_distribution(cr, uid, pol_ids, context=context)
    
    def _get_bid_status(self, cr, uid, ids, name, args, context=None):
        res = {}
        for purchase_obj in self.browse(cr, uid, ids, context=context):
            res[purchase_obj.id] = True
            for line in purchase_obj.order_line:
                if line.state not in ['bid', 'cancel']:
                    res[purchase_obj.id] = False
        return res
    
    def confirm_bid(self, cr, uid, ids, context=None):
        pol_ids = []
        pol_pool = self.pool.get('purchase.order.line')
        for purchase_obj in self.browse(cr, uid, ids, context=context):
            pol_ids.extend([x.id for x in purchase_obj.order_line])
        return pol_pool.confirm_bid(cr, uid, pol_ids, context=context)
    
    def get_option_number(self, cr, uid, po_obj, context=None):
        OPTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                   'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        if po_obj.has_options and not po_obj.parent_po_id:
            return OPTIONS[0]
        count = 1
        parent_po_id = po_obj.parent_po_id and po_obj.parent_po_id.id or False
        if not parent_po_id:
            return ''
        po_ids = self.search(cr, uid, [('parent_po_id', '=', parent_po_id)],
                             context=context)
        index = po_ids.index(po_obj.id)
        if index + 1 <= len(OPTIONS):
            return OPTIONS[index + 1]
        return ''
    
    def _get_sheet_name(self, cr, uid, po_boj, filter_select=[True, False], context=None):
        curr_id = False
        curr_obj = False
        line_string_list = []
        line_string = ""
        temp_list = []
        seq_data = {}
        seq_list = []
        for line in po_boj.order_line:
            if line.sequence_no and line.select_line in filter_select:
                ref_id = line.id
                if line.lead_product_id:
                    ref_id = line.lead_product_id.id
                seq_list.append(ref_id)
                seq_data[ref_id] = line.sequence_no
        id = False
        for id in seq_list:
            if not curr_id:
                curr_id = id
                temp_list.append(seq_data.get(id, ''))
            else:
                if id != curr_id + 1:
                    temp_list = self.sort(temp_list)
                    if len(temp_list) > 1:
                        line_string = str(temp_list[0]) + " - "  + str(temp_list[-1])
                        line_string_list.append(line_string)
                    elif len(temp_list) == 1:
                        line_string = str(temp_list[0])
                        line_string_list.append(line_string)
                    temp_list = [seq_data.get(id, '')]
                    curr_id = id
                else:
                    temp_list.append(seq_data.get(id, ''))
                    curr_id = id
        if id:
            temp_list.append(seq_data.get(id, ''))
        temp_list = self.sort(temp_list)
        if len(temp_list) > 1:
            line_string = str(temp_list[0]) + " - " + str(temp_list[-1])
            line_string_list.append(line_string)
        elif len(temp_list) == 1:
            line_string = str(temp_list[0])
            line_string_list.append(line_string)
        return ','.join(line_string_list)
    
    def sort(self, data):
        new_data = []
        for i in data:
            if i not in new_data:
                new_data.append(i)
        return new_data
    
    def _get_complete_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for purchase_obj in self.browse(cr, uid, ids, context=context):
#             num = []
            text = self._get_sheet_name(cr, uid, purchase_obj, context=context)
#             for line in purchase_obj.order_line:
#                 if line.sequence_no:
#                     num.append(str(line.sequence_no))
#             if num:
#                 if len(num) > 1:
#                     text = "(Item %s - Item %s)"%(str(num[0]), str(num[-1]))
#                 else:
#                     text = "(Item %s)"%(str(num[0]))
            if text:
                text = "(Item %s)"%(str(text))
            else:
                text = ""
            enq_number = purchase_obj.lead_id and purchase_obj.lead_id.reference or False
            if not enq_number:
                enq_number = purchase_obj.name or ''
            option_name = ''
            option_name = self.get_option_number(cr, uid, purchase_obj, context)
            rfq_name = enq_number + text
            if option_name:
                rfq_name += "(OPTION %s)"%(str(option_name))
            res[purchase_obj.id] = rfq_name
        return res
    
    def _get_distribution_status(self, cr, uid, ids, name, args, context=None):
        res = {}
        for po_obj in self.browse(cr, uid, ids, context=context):
            status = False
            for line in po_obj.order_line:
                if line.select_line:
                    status= True
            res[po_obj.id] = status
        return res
    
    STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('bid', 'Cost Received'),
        ('sent', 'RFQ Sent'),
        ('validated', 'Validated'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Purchase Order'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]
    
    def _get_freight_charge(self, cr, uid, ids, name, args, context=None):
        charge_type_pool = self.pool.get('charge.type')
        res = {}
        charge_type_ids = charge_type_pool.search(cr, uid, [('charge_type', '=', 'freight')],
                                                  context=context)
        for po_obj in self.browse(cr, uid, ids, context=context):
            amount_lc = 0.00
            amount_fc = 0.00
            for line in po_obj.order_line:
                if line.select_line:
                    for cost in line.charge_ids:
                        if cost.charge_id and cost.charge_id.id in charge_type_ids:
                            amount_lc += cost.amount_lc
                            amount_fc += cost.amount_fc
            for cost in po_obj.charge_ids:
                if cost.charge_id and cost.charge_id.id in charge_type_ids:
                    amount_lc += cost.amount_lc
                    amount_fc += cost.amount_fc
            res[po_obj.id] = {
                              'freight_charges': amount_fc,
                              'freight_charges_lc': amount_lc,
                              }
        return res
    
    def _get_fob_charge(self, cr, uid, ids, name, args, context=None):
        charge_type_pool = self.pool.get('charge.type')
        res = {}
        charge_type_ids = charge_type_pool.search(cr, uid, [('charge_type', '=', 'fob')],
                                                  context=context)
        for po_obj in self.browse(cr, uid, ids, context=context):
            amount_lc = 0.00
            amount_fc = 0.00
            for line in po_obj.order_line:
                if line.select_line:
                    for cost in line.charge_ids:
                        if cost.charge_id and cost.charge_id.id in charge_type_ids:
                            amount_lc += cost.amount_lc
                            amount_fc += cost.amount_fc
            for cost in po_obj.charge_ids:
                if cost.charge_id and cost.charge_id.id in charge_type_ids:
                    amount_lc += cost.amount_lc
                    amount_fc += cost.amount_fc
            res[po_obj.id] = {
                              'fob_charges': amount_fc,
                              'fob_charges_lc': amount_lc,
                              }
        return res
    
    def _get_comm_charge(self, cr, uid, ids, name, args, context=None):
        charge_type_pool = self.pool.get('charge.type')
        res = {}
        charge_type_ids = charge_type_pool.search(cr, uid, [('charge_type', '=', 'comm')],
                                                  context=context)
        print charge_type_ids
        for po_obj in self.browse(cr, uid, ids, context=context):
            amount_lc = 0.00
            amount_fc = 0.00
            for line in po_obj.order_line:
                if line.select_line:
                    for cost in line.charge_ids:
                        if cost.charge_id and cost.charge_id.id in charge_type_ids:
                            amount_lc += cost.amount_lc
                            amount_fc += cost.amount_fc
            for cost in po_obj.charge_ids:
                if cost.charge_id and cost.charge_id.id in charge_type_ids:
                    amount_lc += cost.amount_lc
                    amount_fc += cost.amount_fc
            res[po_obj.id] = {
                              'comm_fc': amount_fc,
                              'comm_lc': amount_lc,
                              }
        return res
    
    def _get_other_charge(self, cr, uid, ids, name, args, context=None):
        charge_type_pool = self.pool.get('charge.type')
        res = {}
        charge_type_ids = charge_type_pool.search(cr, uid, [('charge_type', '=', 'other')],
                                                  context=context)
        for po_obj in self.browse(cr, uid, ids, context=context):
            amount_lc = 0.00
            amount_fc = 0.00
            for line in po_obj.order_line:
                if line.select_line:
                    for cost in line.charge_ids:
                        if cost.charge_id and cost.charge_id.id in charge_type_ids:
                            amount_lc += cost.amount_lc
                            amount_fc += cost.amount_fc
            for cost in po_obj.charge_ids:
                if cost.charge_id and cost.charge_id.id in charge_type_ids:
                    amount_lc += cost.amount_lc
                    amount_fc += cost.amount_fc
            res[po_obj.id] = {
                              'other_charges': amount_fc,
                              'other_charges_lc': amount_lc,
                              }
        return res
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = super(purchase_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        for po_obj in self.browse(cr, uid, ids, context=context):
            amount = 0.00
            for charge in po_obj.charge_ids:
                if charge.pay_to_cust:
                    amount += charge.amount_fc or 0.00
            for line in po_obj.order_line:
                if line.select_line:
                    for charge in line.charge_ids:
                        if charge.pay_to_cust:
                            amount += charge.amount_fc or 0.00
            amount -= po_obj.discount
            amount -= po_obj.rounding
            res[po_obj.id]['amount_total'] += amount
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    def _get_cost_order(self, cr, uid, ids, context=None):
        po_ids = []
        for cost_obj in self.browse(cr, uid, ids, context=context):
            print cost_obj
            if cost_obj.po_id:
                po_ids.append(cost_obj.po_id.id)
        return po_ids
    
    def _total_product_cost(self, cr, uid, ids, field_name, arg, context=None):
        res = super(purchase_order, self)._total_product_cost(cr, uid, ids, field_name, arg, context=context)
        for po_obj in self.browse(cr, uid, ids, context=context):
            amount_option = 0.00
            amount_option_lc = 0.00
            if po_obj.parent_po_id:
                option_exchange_rate = po_obj.exchange_rate or 1.00000
                exist_line_ids = []
                for line in po_obj.order_line:
                    if line.parent_pol_id:
                        exist_line_ids.append(line.parent_pol_id.id)
                for option_line in po_obj.parent_po_id.order_line:
                    if option_line.id not in exist_line_ids and option_line.select_line:
                        amount_option += option_line.price_subtotal
                amount_option_lc = amount_option * option_exchange_rate
                res[po_obj.id]['total_products_cost'] += amount_option
                res[po_obj.id]['total_products_cost_lc'] += amount_option_lc
        return res
    
    def onchange_transaction_type(self, cr, uid, ids, transaction_type_id, context=None):
        res = {'value': {}}
        transaction_type_pool = self.pool.get('transaction.type')
        if transaction_type_id:
            transaction_type_obj = transaction_type_pool.browse(cr, uid, transaction_type_id,
                                                                context=context)
            res['value']['analytic_account_id'] = transaction_type_obj.cost_center_id and \
                                                        transaction_type_obj.cost_center_id.id or False
            res['value']['liquid_damage_note'] = transaction_type_obj.cost_center_id and \
                                                        transaction_type_obj.cost_center_id.liquid_damage_note and  transaction_type_obj.cost_center_id.liquid_damage_not or False
        return res
    
    def _get_job_no(self, cr, uid, ids, name, arge, context=None):
        res = {}
        for po in self.browse(cr, uid, ids, context=context):
            job_id = False
            if po.manual_job_id:
                res[po.id] = po.manual_job_id.id
                continue
            if po.lead_id:
                job_id = po.lead_id and po.lead_id.sale_id and po.lead_id.sale_id.job_id and \
                                po.lead_id.sale_id.job_id.id or False
            elif po.direct_sale_id:
                job_id = po.direct_sale_id.job_id and po.direct_sale_id.job_id.id or False
            res[po.id] = job_id
        return res
    
    def _get_sale(self, cr, uid, ids, context=None):
        sale_pool = self.pool.get('sale.order')
        purchase_pool = self.pool.get('purchase.order')
        for sale_obj in self.browse(cr, uid, ids, context=context):
            purchase_ids = purchase_pool.search(cr, uid, [('direct_sale_id', 'in', ids)])
            if sale_obj.lead_id:
                lead_po_ids = purchase_pool.search(cr, uid, [('lead_id', '=', sale_obj.lead_id.id)])
                purchase_ids.extend(lead_po_ids)
        return purchase_ids
    
    def _net_pay_supp_fc(self, cr, uid, ids, names, agrs, context=None):
        res = {}
        for po in self.browse(cr, uid, ids, context=context):
            amount_fc = po.total_amount_fc - po.comm_fc
            amount_lc = po.total_amount_lc - po.comm_lc
            res[po.id] = {
                          'net_pay_supp_fc': amount_fc - po.discount,
                          'net_pay_supp_lc': amount_lc - po.discount * po.exchange_rate
                          }
        return res
    
    _columns = {
                'complete_name': fields.function(_get_complete_name, type="char",
                                                 size=128, string="Name"),
                'bid_complete': fields.function(_get_bid_status, type="boolean",
                                                string="Bidding Complete"),
                'sale_calculated': fields.boolean('Sale Price Calculated'),
                'display_end_user_name': fields.boolean('Display End user?'),
                'display_inquiry_name': fields.boolean('Display Inquiry user?'),
                'cost_distributed': fields.boolean('Cost Distributed'),
                'can_distribute': fields.function(_get_distribution_status, type="boolean",
                                                  string="Can Distribute Cost ?"),
                'partner_name': fields.related('partner_id', 'name', type='char',
                                               size=128, string="Supplier Name"),
                'state': fields.selection(STATE_SELECTION, 'Status', readonly=True,
                                          help="The status of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' status. Then the order has to be confirmed by the user, the status switch to 'Confirmed'. Then the supplier must confirm the order to change the status to 'Approved'. When the purchase order is paid and received, the status becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the status becomes in exception.", select=True),
                'manual_job_id': fields.many2one('job.account', 'Job Account'),
                'job_id': fields.function(_get_job_no, type="many2one", relation='job.account',
                                          string='Job No',
                                          store={
                                                 'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['lead_id', 'direct_sale_id'], 20),
                                                 'sale.order': (_get_sale, ['job_id'], 11)
                                                 }),
#                 'job_id': fields.related('lead_id', 'sale_id', 'job_id', type="many2one",
#                                          relation='job.account', string="Job No.",
#                                          store=True),
                'quote_send_by': fields.char('Quote Send By', size=128),
                'direct_delivery': fields.boolean('Direct Delivery ?'),
                'line_of_order': fields.integer("Line of Order"),
                'charge_ids': fields.one2many('pol.landing.cost', 'po_id', 'Other Charges'),
#                 'freight_charges': fields.float('Freight Charges FC', digits_compute= dp.get_precision('Account')),
                'freight_charges': fields.function(_get_freight_charge, type="float",
                                                   digits_compute= dp.get_precision('Account'),
                                                   string='Freight Charge', multi="freight"),
                'freight_charges_lc': fields.function(_get_freight_charge, type="float",
                                                      digits_compute= dp.get_precision('Account'),
                                                      string='Freight Charge LC', multi="freight"),
                'fob_charges': fields.function(_get_fob_charge, type="float",
                                               string='Fob Charges FC',
                                               digits_compute= dp.get_precision('Account'),
                                               multi="fob"),
                'fob_charges_lc': fields.function(_get_fob_charge, type="float",
                                                  string='Fob Charges LC',
                                                  digits_compute= dp.get_precision('Account'),
                                                  multi="fob"),
                'other_charges': fields.function(_get_other_charge,
                                                 string='Other Charges FC',
                                                 digits_compute= dp.get_precision('Account'),
                                                 multi="other"),
                'other_charges_lc': fields.function(_get_other_charge,
                                                    string='Other Charges LC',
                                                    digits_compute= dp.get_precision('Account'),
                                                    multi="other"),
                'comm_fc': fields.function(_get_comm_charge,
                                                 string='Agency Commission FC',
                                                 digits_compute= dp.get_precision('Account'),
                                                 multi="commi"),
                'comm_lc': fields.function(_get_comm_charge,
                                                    string='Agency Commission LC',
                                                    digits_compute= dp.get_precision('Account'),
                                                    multi="commi"),
#                 'supplier_shipping': fields.boolean('Supplier Shipping'),
                'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
                    store={
                        'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['charge_ids', 'discount', 'rounding'], 20),
                        'pol.landing.cost': (_get_cost_order, None, 11),
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums", help="The amount without tax", track_visibility='always'),
                'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
                    store={
                        'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['charge_ids', 'discount', 'rounding'], 20),
                        'pol.landing.cost': (_get_cost_order, None, 11),
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums", help="The tax amount"),
                'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
                    store={
                        'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['charge_ids', 'discount', 'rounding'], 20),
                        'pol.landing.cost': (_get_cost_order, None, 11),
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums",help="The total amount"),
                'delivery_term': fields.char('Delivery Term', size=128),
                'quote_date': fields.date('Quote Date'),
                'direct_del_address': fields.text('Delivery Address'),
                'analytic_account_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'parent_po_id': fields.many2one('purchase.order', 'Parent Purchase Order'),
                'has_options': fields.boolean('Has Options'),
                'total_products_cost': fields.function(_total_product_cost, digits_compute=dp.get_precision('Account'), string='Product Cost FC',type="float", multi="cost"),
                'total_products_cost_lc': fields.function(_total_product_cost,
                                                          digits_compute=dp.get_precision('Account'),
                                                          string='Product Cost LC',type="float",
                                                          multi="cost"),
                'direct_purchase': fields.boolean('Direct Purchase'),
                'period_id': fields.many2one('account.period', 'Period'),
                'incoterm_id': fields.many2one('stock.incoterms', 'Incoterms'),
                'unused_seq': fields.char('Unused Sequence'),
                'rfq_name': fields.char('RFQ'),
                'direct_sale_id': fields.many2one('sale.order', 'Direct Purchase'),
                'net_pay_supp_fc': fields.function(_net_pay_supp_fc, digits_compute=dp.get_precision('Account'), string='Net Payable To Supplier',type="float", multi="comm"),
                'net_pay_supp_lc': fields.function(_net_pay_supp_fc, digits_compute=dp.get_precision('Account'), string='Net Payable To Supplier',type="float", multi="comm"),
                'lpo_no': fields.char('LPO No.', size=128),
                'display_del_address': fields.boolean('Display Delivery Address'),
                'edit_po': fields.boolean('Edit PO'),
                'del_term_place': fields.char('Delivery Term Place', size=128),
                'over_sale_qty_check': fields.boolean('Override Sale Qty Check'),
#                 'supplier_invoice_date': fields.date('Supplier Invoice Date'),
                }
    _order = 'lead_id desc'
    _defaults = {
                 'display_del_address': True
                 }
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        transaction_type_pool = self.pool.get('transaction.type')
        res = super(purchase_order, self)._prepare_order_picking(cr, uid, order, context=context)
        if order.analytic_account_id:
            cost_center_id = order.analytic_account_id.id
            transaction_type_ids = transaction_type_pool.search(cr, uid, [('model_id.model', '=', 'stock.picking.in'),
                                                                          '|', ('cost_center_id', '=', cost_center_id),
                                                                          ('cost_center_id', '=', False),
                                                                          ('refund', '=', False)])
            if not transaction_type_ids:
                raise osv.except_osv(_("Error !!!"),
                                     _("Please configure transaction type"))
            res['cost_center_id'] = cost_center_id
            res['transaction_type_id'] = transaction_type_ids[0]
        return res
    
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context)
        if order_line.sequence_no:
            res.update({'sequence_no': order_line.sequence_no})
        return res
    
    def set_send(self, cr, uid, ids, context=None):
        for po_obj in self.browse(cr, uid, ids, context=context):
            for line in po_obj.order_line:
                if line.state == 'bid':
                    line.write({'state': 'draft'})
        return self.write(cr, uid, ids, {'state': 'sent'}, context=context)
    
    def wkf_send_rfq(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        res = super(purchase_order, self).wkf_send_rfq(cr, uid, ids, context=context)
        po_obj = self.browse(cr, uid, ids[0], context=context)
        if po_obj.state not in ['draft', 'sent', 'bid']:
            template_id = ir_model_data.get_object_reference(cr, uid, 'hatta_crm',
                                                             'email_template_edi_purchase_conf')
            if template_id:
                res['context'].update({'default_template_id': template_id[1]})
        return res
    
    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None,
                        toolbar=False, submenu=False):
        res = super(purchase_order, self).fields_view_get(cr, user, view_id, view_type,
                                                          context=context, toolbar=toolbar,
                                                          submenu=submenu)
        if view_type == 'tree':
            d = date.today() + timedelta(days=2)
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//tree")
            for node in nodes:
                node.set('colors', "grey:state=='cancel';blue:state in ('wait','confirmed');red:state in ('except_invoice','except_picking');red:supplier_closing_date<=current_date and state in ('draft', 'sent');orange:supplier_closing_date<='%s' and state in ('draft', 'sent')"%(str(d)))
            res['arch'] = etree.tostring(doc)
        return res
    
    def cancel_purchase(self, cr, uid, ids, context=None):
        for po_obj in self.browse(cr, uid, ids, context=context):
            for line in po_obj.order_line:
                line.write({'state': 'draft'})
        return True
    
    def cancel_sale_calc(self, cr, uid, ids, context=None):
        for po_obj in self.browse(cr, uid, ids, context=context):
            for line in po_obj.order_line:
                line.write({'sale_calculated': False, 'sale_price': 0.00})
            po_obj.write({'sale_calculated': False})
        return True
    
purchase_order()

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        product_pool = self.pool.get('product.product')
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id,
                                                                   product_id, qty, uom_id, partner_id,
                                                                   date_order, fiscal_position_id,
                                                                   date_planned, name, price_unit,
                                                                   context=context)
        if product_id:
            product_obj = product_pool.browse(cr, uid, product_id, context=context)
            certificate_ids = [(4, x.id) for x in product_obj.certificate_ids]
            res['value']['certificate_ids'] = certificate_ids
            res['value']['manufacturer_id'] = product_obj.manufacturer_id and \
                                                    product_obj.manufacturer_id.id or \
                                                    False
            res['value']['account_id'] = product_obj.property_account_expense and \
                                                product_obj.property_account_expense.id or \
                                                product_obj.categ_id and \
                                                product_obj.categ_id.property_account_expense_categ and \
                                                product_obj.categ_id.property_account_expense_categ.id or False
        if res['value'].get('name', False):
            del res['value']['name']
        return res
    
    def get_seq_float(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0.00
            if line.sequence_no:
                try:
                    res[line.id] = float(line.sequence_no)
                except:
                    pass
        return res
    
    _columns = {
                'sequence_no': fields.char('Sequence', size=64, select=True),
                'seq_float': fields.function(get_seq_float, type='float', store=True),
                'enq_customer_id': fields.related('order_id', 'lead_id', 'partner_id', type="many2one",
                                                  relation="res.partner", string="Customer", store=True),
                'customer_enq': fields.related('order_id', 'lead_id', type="many2one",
                                               relation="crm.lead", string="Customer Enq", store=True),
                'date_order': fields.related('order_id', 'date_order', string='Order Date',
                                             readonly=True, type="date", store=True),
                'select_line': fields.boolean('Select'),
                'cost_distributed': fields.boolean('Cost Distributed'),
                'remark': fields.text('Remarks', pad_content_field='remark'),
                'certificate_ids': fields.many2many('product.certificate', 'pol_cert_rel',
                                                    'pol_id', 'cert_id', 'Certificate(s)'),
                'state': fields.selection([('draft', 'Draft'), ('bid', 'Bid'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', required=True, readonly=True,
                                  help=' * The \'Draft\' status is set automatically when purchase order in draft status. \
                                       \n* The \'Confirmed\' status is set automatically as confirm when purchase order in confirm status. \
                                       \n* The \'Done\' status is set automatically when purchase order is set as done. \
                                       \n* The \'Cancelled\' status is set automatically when user cancel purchase order.'),
                'lead_product_id': fields.many2one('crm.product.lines', 'Lead Product Ref'),
                'sale_price': fields.float('Sale Price LC', digits_compute=dp.get_precision('Account')),
                'sale_calculated': fields.boolean('Sale Calculated'),
                'cust_selected': fields.boolean('Customer Selected ?'),
                'manufacturer_id': fields.many2one('res.partner', 'Manufacturer'),
                'remark_image_ids': fields.many2many('ir.attachment',
                                                     'pol_atta_rel',
                                                     'pol_id', 'attachment_id', 'Remarks(Snapshot)'),
                'charge_ids': fields.one2many('pol.landing.cost', 'pol_id', 'Other Charges'),
                'parent_pol_id': fields.many2one('purchase.order.line', 'Purchase Order Line'),
                'job_id': fields.related('order_id', 'job_id', type="many2one", relation='job.account',
                                         string='Job No.', store=True),
                'complete_name': fields.related('order_id', 'complete_name', type="char", size=128, string="RFQ"),
                'quote_date': fields.related('order_id', 'quote_date', type="date", string="Supplier Quote Date"),
                'margin': fields.float('Unit Margin'),
                'currency_id': fields.related('order_id', 'currency_id', type="many2one",
                                              relation="res.currency", string='Currency')
                }
    _order = 'seq_float'
    
    def view_po(self, cr, uid, ids, context=None):
        line_obj = self.browse(cr, uid, ids, context=context)[0]
        return {
                'name': 'Request For Quotations',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', '=', line_obj.order_id and line_obj.order_id.id or False)],
                'context': context,
                }
    
    def copy_des_sale(self, cr, uid, ids, context=None):
        sale_line_pool = self.pool.get('sale.order.line')
        for line in self.browse(cr, uid, ids, context=context):
            if not line.order_id and line.order_id.lead_id and line.order_id.lead_id.sale_id:
                raise osv.except_osv(_("Error!!!"),
                                     _("No related sale order found"))
            sale_id = line.order_id.lead_id.sale_id.id
            product_id = line.product_id and line.product_id.id or False
            sale_line_ids = sale_line_pool.search(cr, uid, [('order_id', '=', sale_id),
                                                            ('product_id', '=', product_id)],
                                                  context=context)
            if not sale_line_ids: 
                raise osv.except_osv(_("Error!!!"),
                                     _("No related sale order found!!!"))
            sale_line_obj = sale_line_pool.browse(cr, uid, sale_line_ids[0], context=context)
            line.write({'name': sale_line_obj.name})
        return True
    
    def create_option(self, cr, uid, ids, context=None):
        for id in ids:
            default = {
                       'select_line': False
                       }
            self.copy(cr, uid, id, default, context=context)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
    def customer_select(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            lead_product_id = line.lead_product_id.id or False
            line_ids = self.search(cr, uid, [('cust_selected', '=', True),
                                             ('lead_product_id', '=', lead_product_id)],
                                   context=context)
            if line_ids:
                raise osv.except_osv(_('Error!'), _('Already selected another line. Please cancel that selection to proceed'))
            if line.parent_pol_id:
                parent_pol_po_id = line.parent_pol_id.order_id and line.parent_pol_id.order_id.id or False
                current_po_id = line.order_id and line.order_id.id or False
                line.write({'order_id': parent_pol_po_id})
                line.parent_pol_id.write({'order_id': current_po_id})
        self.write(cr, uid, ids, {'cust_selected': True}, context=context)
        
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
    def cancel_customer_select(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'cust_selected': False}, context=context)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
    def distribute_cost(self, cr, uid, ids, context=None):
        po_ids = []
        po_pool = self.pool.get('purchase.order')
        pol_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.order_id:
                po_ids.append(line.order_id.id)
                pol_ids.extend([x.id for x in line.order_id.order_line if x.cost_distributed == False])
        po_pool.recompute_cost_price(cr, uid, po_ids, context=context)
        return self.write(cr, uid, list(set(pol_ids)), {'cost_distributed': True}, context=context)
    
    def cancel_distribution(self, cr, uid, ids, context=None):
        po_pool = self.pool.get('purchase.order')
        po_ids = []
        for pol_obj in self.browse(cr, uid, ids, context=context):
            if pol_obj.order_id:
                po_ids.append(pol_obj.order_id.id)
        po_pool.write(cr, uid, list(set(po_ids)), {'cost_distributed': False},
                      context=context)
        return self.write(cr, uid, ids, {'cost_distributed': False}, context=context)
    
    def select_po_line(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        claim_product_pool = self.pool.get('crm.product.lines')
        obj_model = self.pool.get('ir.model.data')
        uom_pool = self.pool.get('product.uom')
        for pol_obj in self.browse(cr, uid, ids, context=context):
            purchase_obj = pol_obj.order_id or False
            if pol_obj.price_unit == 0.00:
                raise osv.except_osv(_("Error!!!"),
                                     _("Unit price cannot be 0.00"))
            if purchase_obj:
                product_uom_id = pol_obj.product_id.uom_id.id or False
                enq_id = purchase_obj.lead_id and purchase_obj.lead_id.id or False
                enq_product_qty = 0.00
                same_pol_qty = 0.00
                if enq_id:
                    enq_product_ids = claim_product_pool.search(cr, uid, [('product_id', '=', pol_obj.product_id.id),
                                                                          ('lead_id', '=', enq_id)], context=context)
                    for enq_product_obj in claim_product_pool.browse(cr, uid, enq_product_ids, context=context):
                        enq_qty = enq_product_obj.product_uom_qty or 0.00
                        if enq_product_obj.uom_id.id != product_uom_id:
                            enq_qty = uom_pool._compute_qty(cr, uid, enq_product_obj.uom_id.id,
                                                            enq_qty, product_uom_id)
                        enq_product_qty += enq_qty
                    same_pol_ids = self.search(cr, uid, [('order_id.lead_id', '=', enq_id),
                                                         ('product_id', '=', pol_obj.product_id.id),
                                                         ('state', '!=', 'cancel'),
                                                         ('select_line', '=', True)], context=context)
                    for same_pol_obj in self.browse(cr, uid, same_pol_ids, context=context):
                        same_qty = same_pol_obj.product_qty or 0.00
                        pol_uom = same_pol_obj.product_uom and same_pol_obj.product_uom.id or \
                                            same_pol_obj.product_id.uom_id.id or False
                        if pol_uom != product_uom_id:
                            same_qty = uom_pool._compute_qty(cr, uid, pol_uom, same_qty, product_uom_id)
                        same_pol_qty += same_qty
                pol_qty = pol_obj.product_qty or 0.00
                pol_uom = pol_obj.product_uom and pol_obj.product_uom.id or \
                            pol_obj.product_id.uom_id.id or False
                if pol_uom != product_uom_id:
                    pol_qty = uom_pool._compute_qty(cr, uid, pol_uom, pol_qty, product_uom_id)
                same_pol_qty += pol_qty
                if enq_product_qty < same_pol_qty and not context.get('overide', False):
                    model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),
                                                              ('name','=','pol_select_qty_adjust_form')])
                    resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
                    return {
                            'name': _('Change Select Qty'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'pol.select.qty.adjust',
                            'views': [(resource_id,'form')],
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'context': context,
                            }
                else:
                    pol_obj.write({'select_line': True})
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
    def confirm_bid(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'bid'}, context=context)
    
purchase_order_line()

class charge_type(osv.osv):
    _name = 'charge.type'
    _description = 'Landing Cost Charge Type'
    _columns = {
                'name': fields.char('Name', size=128),
                'charge_type': fields.selection([('freight', 'Freight Charge'), ('fob', 'Fob Charge'),
                                                 ('other', 'Other Charges'), ('comm', 'Agency Commission')], 'Sum Applicable To'),
                'related_cert_id': fields.many2one('product.certificate', 'Product Certificate'),
                'account_id': fields.many2one('account.account', 'Account',
                                              domain="[('type', '!=', 'view')]")
                }
    _defaults = {
                 'charge_type': 'other'
                 }
charge_type()

class pol_landing_cost(osv.osv):
    _name = 'pol.landing.cost'
    _description = 'POL Landing Cost'
    
    def onchange_amount(self, cr, uid, ids, amount_fc, amount_lc, exchange_rate,
                         fc_ch=False, lc_ch=False, arg=False, context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        fc_change = fc_ch
        lc_change = lc_ch
        exchange_rate = context.get('exchange_rate', exchange_rate)
        if fc_change and amount_fc and exchange_rate:
            new_amount_lc = float(amount_fc) * float(exchange_rate)
            if round(new_amount_lc, 2) != round(amount_lc, 2):
                res['value']['amount_lc'] = new_amount_lc
        if lc_change and amount_lc and exchange_rate:
            new_amount_fc = float(amount_lc) / float(exchange_rate)
            if round(new_amount_fc, 2) != round(amount_fc, 2):
                res['value']['amount_fc'] = new_amount_fc
        return res
    
    def onchange_charge_id(self, cr, uid, ids, charge_id, context=None):
        res = {'value': {}}
        charge_pool = self.pool.get('charge.type')
        if charge_id:
            charge_obj = charge_pool.browse(cr, uid, charge_id, context=context)
            res['value']['account_id'] = charge_obj.account_id and charge_obj.account_id.id or False
        return res
    
    _columns = {
                'charge_id': fields.many2one('charge.type', 'Charge'),
                'account_id': fields.many2one('account.account', 'Account',
                                              domain="[('type', '!=', 'view')]"),
                'amount_lc': fields.float('Amount LC', digits_compute=dp.get_precision('Account')),
                'amount_fc': fields.float('Amount FC', digits_compute=dp.get_precision('Account')),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Line Ref'),
                'po_id': fields.many2one('purchase.order', 'Purchase Order Ref'),
                'pay_to_cust': fields.boolean('Pay To Supplier'),
                'info': fields.text('Additional Info')
                }
pol_landing_cost()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

import openerp.addons.decimal_precision as dp
from tools.translate import _
from datetime import datetime
from openerp.tools.safe_eval import safe_eval

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    def _total_eq_cost_fc(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        amount_total = 0.0
        for po in self.browse(cr, uid, ids,context=context):
            amount_total = po.freight_charges + po.fob_charges + po.other_charges
            res[po.id] = amount_total
        return res
    
    def _total_eq_cost_lc(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        lc_amount = 0.00
        amount_total = 0.00
        for po in self.browse(cr, uid, ids, context=context):
            amount_total = po.freight_charges_lc + po.fob_charges_lc + po.other_charges_lc
            res[po.id] = amount_total
        return res
    def _total_amount_fc(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        amount_total = 0.0
        for po in self.browse(cr, uid, ids,context=context):
            amount_total = po.freight_charges + po.fob_charges + po.other_charges + po.total_products_cost
            amount_total_lc = po.freight_charges_lc + po.fob_charges_lc + po.other_charges_lc + po.total_products_cost_lc
            res[po.id] = {
                          'total_amount_fc': amount_total,
                          'total_amount_lc': amount_total_lc
                          }
        return res
    def _total_product_cost(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for po in self.browse(cr, uid, ids,context=context):
            amount_total = 0.00
            for line in po.order_line:
                if line.select_line:
                    amount_total += (line.price_subtotal + line.discount)
            amount_total += po.rem_line_charge or 0.00
            res[po.id] = {
                          'total_products_cost': amount_total,
                          'total_products_cost_lc': amount_total * po.exchange_rate
                          }
        return res
    def _total_amount_lc(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        amount_total = 0.0
        for po in self.browse(cr, uid, ids,context=context):
            amount_total = po.communication_charges + po.bank_charges + po.bank_interest + po.insurance_charges + po.customs_duty + po.clg_agent_charges + po.clearing_expenses + po.transport_delivery_expenses  + po.misc_expenses 
                            
            res[po.id] = amount_total
        return res
    
    def onchange_freight(self, cr, uid, ids, freight_charges, freight_charges_lc, exchange_rate,
                         context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if context.get('fc_change', False) and freight_charges and exchange_rate:
            new_freight_charges_lc = float(freight_charges) * float(exchange_rate)
            if round(new_freight_charges_lc, 2) != round(freight_charges_lc, 2):
                res['value']['freight_charges_lc'] = new_freight_charges_lc
        if context.get('lc_change', False) and freight_charges_lc and exchange_rate:
            new_freight_charges = float(freight_charges_lc) / float(exchange_rate)
            if round(new_freight_charges, 2) != round(freight_charges, 2):
                res['value']['freight_charges'] = new_freight_charges
        return res
    
    def onchange_fob(self, cr, uid, ids, fob_charges, fob_charges_lc, exchange_rate,
                     context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if context.get('fc_change', False) and fob_charges and exchange_rate:
            new_fob_charges_lc = float(fob_charges) * float(exchange_rate)
            if round(new_fob_charges_lc, 2) != round(fob_charges_lc, 2):
                res['value']['fob_charges_lc'] = new_fob_charges_lc
        if context.get('lc_change', False) and fob_charges_lc and exchange_rate:
            new_fob_charges = float(fob_charges_lc) / float(exchange_rate)
            if round(new_fob_charges, 2) != round(fob_charges, 2):
                res['value']['fob_charges'] = new_fob_charges
        return res
    
    def onchange_other_ch(self, cr, uid, ids, other_charges, other_charges_lc, exchange_rate,
                          context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if context.get('fc_change', False) and other_charges and exchange_rate:
            new_other_charges_lc = float(other_charges) * float(exchange_rate)
            if round(new_other_charges_lc, 2) != round(other_charges_lc, 2):
                res['value']['other_charges_lc'] = new_other_charges_lc
        if context.get('lc_change', False) and other_charges_lc and exchange_rate:
            new_other_charges = float(other_charges_lc) / float(exchange_rate)
            if round(new_other_charges, 2) != round(other_charges, 2):
                res['value']['other_charges'] = new_other_charges
        return res
    
    def onchange_shipment(self, cr, uid, ids, shipment_method_id, cost_distributed, context=None):
        res = {'value': {}}
        shipment_method_pool = self.pool.get('hatta.shipment.method')
        if shipment_method_id and not cost_distributed:
            shipment_method_obj = shipment_method_pool.browse(cr, uid, shipment_method_id,
                                                              context=context)
            res['value'] = {
                            'communication_charges': shipment_method_obj.communication_charges,
                            'bank_charges': shipment_method_obj.bank_charges,
                            'insurance_charges': shipment_method_obj.insurance_charges,
                            'clg_agent_charges': shipment_method_obj.clg_agent_charges,
                            'clearing_expenses': shipment_method_obj.clearing_expenses,
                            'transport_delivery_expenses': shipment_method_obj.transport_delivery_expenses,
                            'misc_expenses': shipment_method_obj.misc_expenses,
                            'bank_int_rate': shipment_method_obj.bank_interest,
                            'custom_duty_rate': shipment_method_obj.customs_duty
                            }
        return res
    
    def onchange_weeks(self, cr, uid, ids, payment_interest_ids, context=None):
        res = {'value': {}}
        if payment_interest_ids:
            new_line = []
            for payment_id in payment_interest_ids:
                if not payment_id[2]:
                    new_line.append((2, payment_id[1]))
            res['value'] = {
                            'payment_interest_ids': new_line
                            }
        return res
    
#     def _get_po_line(self, cr, uid, ids, context=None):
#         po_ids = []
#         for pol_obj in self.browse(cr, uid, ids, context=context):
#             if pol_obj.order_id and pol_obj.order_id.state in ['draft', 'bid', 'sent']:
#                 po_ids.append(pol_obj.order_id.id)
#         return po_ids
#     
#     def _get_po(self, cr, uid, ids, context=None):
#         new_ids = []
#         for order in self.browse(cr, uid, ids, context=context):
#             if order.state in ['draft', 'bid', 'sent']:
#                 new_ids.append(order.id)
#         return new_ids
    
    def _get_base_currency(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        return user_obj.company_id and user_obj.company_id.currency_id.id or False
    
    def onchange_coll_hatta(self, cr, uid, ids, collected_by_hatta, context=None):
        res = {'value': {}}
        if collected_by_hatta:
            res['value']['delivered_by_supplier'] = False
        return res
    
    def onchange_del_supp(self, cr, uid, ids, delivered_by_supplier, context=None):
        res = {'value': {}}
        if delivered_by_supplier:
            res['value']['collected_by_hatta'] = False
        return res
    
    def _get_customer_id(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for purchase in self.browse(cr, uid, ids, context=context):
            if purchase.lead_id and purchase.lead_id.partner_id:
                customer_id = purchase.lead_id.partner_id.id
            elif purchase.direct_sale_id:
                customer_id = purchase.direct_sale_id.partner_id.id
            else:
                customer_id = False
            res[purchase.id] = customer_id
        return res
    
    def onchange_lead_id(self, cr, uid, lead_id, context=None):
        res = {'value': {}}
        if lead_id:
            for lead in self.pool.get('crm.lead').browse(cr, uid, lead_id, context=context):
                res['value']['final_destination'] = lead.partner_delivery_id.id
        return res
    
    _columns = {
        'location_id': fields.many2one('stock.location', 'Destination', domain=[('usage','<>','view')], states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]} ),
        'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'enquiry': fields.char('Enquiry', size=64),
        'enquiry_date': fields.date('Enquiry Date'),
        'enquiry_closing_date': fields.date('Enquiry Closing Date'),
#         'currency_id': fields.many2one('res.currency', 'Currency'),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one",
                                      relation='res.currency', string='Currency', store=True),
        'customer_rfq': fields.char('Customer RFQ', size=64),
        'incoterms': fields.selection([('c_and_d', 'C and F'), ('ex_works', 'Ex Works')], 'Incoterms'),
        'quote_validity': fields.integer('Quote Validity'),
        'quote_validity_type': fields.selection([('weeks', 'Weeks'), ('month', 'Month'), ('days', 'Days')],
                                                'Quote Validity Type'),
        'delivery_weeks': fields.integer('Delivery(Weeks)'),
        'manufacturer': fields.many2many('res.partner', 'man_po_rel', 'po_id', 'partner_id',
                                         'Manufacturer', size=64),
        'product_type': fields.char('Product Type', size=128),
        'weight': fields.float('Weight(kg)'),
        'vol': fields.float('Volume(m3)'),
        'select_line': fields.boolean('Select'),
        'need_certificate': fields.selection([('yes', 'Yes'), ('no', 'No')], 'Certificate Required'),
        'supplier_country_id': fields.many2many('res.country', 'country_purchase_rel',
                                                'po_id', 'country_id', 'Supplier Origin'),
        'freight_charges': fields.float('Freight Charges FC', digits_compute= dp.get_precision('Account')),
        'fob_charges': fields.float('Fob Charges FC', digits_compute= dp.get_precision('Account')),
        'other_charges': fields.float('Other Charges FC', digits_compute= dp.get_precision('Account')),
        'freight_charges_lc': fields.float('Freight Charges LC', digits_compute= dp.get_precision('Account')),
        'fob_charges_lc': fields.float('Fob Charges LC', digits_compute= dp.get_precision('Account')),
        'other_charges_lc': fields.float('Other Charges LC', digits_compute= dp.get_precision('Account')),
        'communication_charges': fields.float('Communication Charges', digits_compute= dp.get_precision('Account')),
        'bank_charges': fields.float('Bank Charges', digits_compute= dp.get_precision('Account')),
        'bank_interest': fields.float('Bank Interest', digits_compute= dp.get_precision('Account')),
        'real_bank_interest': fields.float('Bank Interest', digits_compute= dp.get_precision('Account')),
        'insurance_charges': fields.float('Insurance Charges', digits_compute= dp.get_precision('Account')),
        'customs_duty': fields.float('Customs Duty', digits_compute= dp.get_precision('Account')),
        'real_customs_duty': fields.float('Customs Duty', digits_compute= dp.get_precision('Account')),
        'clg_agent_charges': fields.float('Clearing Agent Charges', digits_compute= dp.get_precision('Account')),
        'clearing_expenses': fields.float('Clearing Expenses at port', digits_compute= dp.get_precision('Account')),
        'transport_delivery_expenses': fields.float('Transport and Delivery Expenses', digits_compute= dp.get_precision('Account')),
        'misc_expenses': fields.float('Misc. Expenses if any', digits_compute= dp.get_precision('Account')),
        'exchange_rate': fields.float('Exchange Rate', digits=(16, 5)),
        'foreign_currency': fields.many2one('res.currency', 'Foreign Currency'),
        'select_line': fields.boolean('Select'),
        'total_amount_fc': fields.function(_total_amount_fc, digits_compute=dp.get_precision('Account'), string='Total Cost FC',type="float", multi="pro"),
        'total_amount_lc': fields.function(_total_amount_fc, digits_compute=dp.get_precision('Account'), string='Total Cost LC',type="float", multi="pro"),
        'total_products_cost': fields.function(_total_product_cost, digits_compute=dp.get_precision('Account'), string='Product Cost FC',type="float", multi="cost"),
        'total_products_cost_lc': fields.function(_total_product_cost, digits_compute=dp.get_precision('Account'), string='Product Cost LC',type="float", multi="cost"),
        'total_equipment_cost_fc': fields.function(_total_eq_cost_fc, digits_compute=dp.get_precision('Account'), string='Total Equipment cost in FC',type="float"),
        'total_equipment_cost_lc': fields.function(_total_eq_cost_lc, digits_compute=dp.get_precision('Account'), string='Total Equipment cost in LC',type="float"),
        'total_expenses': fields.function(_total_amount_lc, digits_compute=dp.get_precision('Account'), string='Total Expenses',type="float"),
        'product_landed_cost': fields.float('Product Landed Cost(Unit)', digits_compute=dp.get_precision('Account')),
        'cost_distributed': fields.boolean('Cost Distributed'),
        'shipment_method_id': fields.many2one('hatta.shipment.method', 'Shipping Method'),
        'bank_int_rate': fields.float('Interest Rate', digits_compute= dp.get_precision('Account')),
        'lead_id': fields.many2one('crm.lead', 'Lead'),
        'custom_duty_rate': fields.float('Custom Duty Rate', digits_compute= dp.get_precision('Account')),
        'payment_interest_ids': fields.one2many('purchase.bank.interest', 'purchase_id',
                                                'Bank Interest Schedule'),
        'margin': fields.float('Margin'),
        'factor': fields.float('Factor', digits=(16,8)),
#         'customer_id': fields.related('lead_id', 'partner_id', type='many2one',
#                                       relation='res.partner', store=True, string='Customer'),
        
        'customer_id': fields.function(_get_customer_id, type="many2one",
                                                    relation="res.partner",
                                                    string="Customer", store=True),
        
        'supplier_closing_date': fields.date('Supplier Closing Date'),
        'rem_line_charge': fields.float('Removed Line Charges'),
        'po_notes': fields.text('Notes'),
        'special_notes': fields.text('Special Notes'),
        'duty_required': fields.selection([('Yes', 'Yes'), ('No', 'No')], 'Duty Exemption Required'),
        'remark': fields.text('Remark'),
        'discount': fields.float('Discount'),
        'rounding': fields.float('Rounding off'),
        'item': fields.char('Items'),
        'discount_applied': fields.boolean('Discount Applied'),
        'sp_note_duty_exemption': fields.text('Special Notes for Duty Exemption'),
        'liquid_damage_note': fields.text('Liquidated Damages Note'),
        'datasheet_remark': fields.text('Datasheet Remark'),
        'weight': fields.char('Weight', size=32),
        'volume': fields.char('Volume', size=32),
        'dimension': fields.char('Dimension', size=32),
        'zone': fields.char('Zone', size=32),
        'cancel_note': fields.text(string="Cancellation Note"),
        'shipping_ids' : fields.one2many('shipping.quotation', 'purchase_id', 'Shipping Quotation'),
        'collected_by_hatta': fields.boolean('Collected By Hatta'),
        'delivered_by_supplier': fields.boolean('Delivered By Supplier'),
        'display_final_destination' : fields.boolean('Display Final Destination?'),
        'final_destination' : fields.many2one('res.partner', "Final Destination", required=False),
        'revision_date': fields.date('Date of Revision')
        }
    _defaults = {
                 'quote_validity_type': 'weeks',
                 'foreign_currency': _get_base_currency,
                 'display_final_destination': True
                 }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'shipping_ids': [],
        })
        return super(purchase_order, self).copy(cr, uid, id, default, context=context)
    
    def send_po_mail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi po template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'hatta_purchase', 'email_template_edi_po_send')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    def update_bank_int(self, cr, uid, ids, context=None):
        for po_obj in self.browse(cr, uid, ids, context=context):
            shipping_method_obj = po_obj.shipment_method_id or False
            enq_obj = po_obj.lead_id or False
            if not shipping_method_obj:
                raise osv.except_osv(_('Error !!!'),_('No Shipping Method Selected'))
            if not enq_obj:
                raise osv.except_osv(_('Error !!!'),_('No related enquiry found'))
            interest_rate = (shipping_method_obj.bank_interest or 1.00) / 100
            deadline_date = enq_obj.date_deadline or False
            days = 1
            if deadline_date:
                today = datetime.today()
                date_deadline = datetime.strptime(deadline_date, "%Y-%m-%d")
                delta = date_deadline - today
                days = delta.days
            total_cost = po_obj.total_products_cost_lc
            interest = (total_cost * interest_rate * float(days)) / 360
            po_obj.write({'bank_interest': round(interest, 0)})
        return True
    
    def update_cust_duty(self, cr, uid, ids, context=None):
        product_pool = self.pool.get('product.product')
        for po_obj in self.browse(cr, uid, ids, context=context):
            shipping_method_obj = po_obj.shipment_method_id or False
            if not shipping_method_obj:
                raise osv.except_osv(_('Error !!!'),_('No Shipping Method Selected'))
            rate = (shipping_method_obj.customs_duty or 1.00) / 100
            total_cost = po_obj.total_amount_lc
            duty = total_cost * rate
            po_obj.write({'customs_duty': round(duty, 0), 'real_customs_duty': round(duty, 0)})
        return True
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
    def exchange_rate_change(self, cr, uid, ids, rate, context=None):
        if context is None:
            context = {}
        pol_pool = self.pool.get('purchase.order.line')
        active_ids = context.get('active_ids', [])
        for purchase_obj in self.browse(cr, uid, active_ids, context=context):
            vals = {
                    'freight_charges_lc': purchase_obj.freight_charges * rate,
                    'fob_charges_lc': purchase_obj.fob_charges * rate,
                    'other_charges_lc': purchase_obj.other_charges * rate,
                    }
            purchase_obj.write(vals)
            line_ids = [x.id for x in purchase_obj.order_line]
            pol_pool.exchange_rate_change(cr, uid, line_ids, rate, context=context)
        return True
    
    def recompute_cost_price(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        curr_pool = self.pool.get('res.currency')
        uom_pool = self.pool.get('product.uom')
        line_pool = self.pool.get('purchase.order.line')
        for pur_obj in self.browse(cr, uid, ids, context=context):
            line_qty_dict = {}
            total_equipment_cost_lc = pur_obj.total_equipment_cost_lc or 0.00
            total_expense_lc = pur_obj.total_expenses or 0.00
            net_qty = 0.00
            for line in pur_obj.order_line:
                if line.select_line:
                    product_uom = line.product_id and line.product_id.uom_id and \
                                     line.product_id.uom_id.id or False
                    line_uom_id = line.product_uom and line.product_uom.id or False
                    qty = line.product_qty or 0.00
                    unit_coefficent = 1.00
                    if product_uom and line_uom_id and product_uom != line_uom_id:
                        qty = uom_pool._compute_qty(cr, uid, line_uom_id, qty, product_uom)
                        unit_coefficent = uom_pool._compute_qty(cr, uid, line_uom_id, 1, product_uom)
                    line_qty_dict[line.id] = unit_coefficent
                    net_qty += qty
            net_expense = total_equipment_cost_lc + total_expense_lc
            if net_qty != 0.00:
                unit_expense = net_expense / net_qty
            else:
                unit_expense = net_expense
            pur_obj.write({"product_landed_cost": unit_expense, 'cost_distributed': True})
            for line in pur_obj.order_line:
                if line.select_line:
                    unit_coefficent = line_qty_dict.get(line.id, 1.00)
                    line_expense = unit_expense * unit_coefficent
                    vals = {'dist_cost': line_expense}
                    line.write(vals)
        return True
    
    def onchange_currency(self, cr, uid, ids, base_curr_id, currency_id, context=None):
        value = {}
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')
        if currency_id and base_curr_id:
            base_curr_obj = currency_pool.browse(cr, uid, base_curr_id, context=context)
            po_curr_obj = currency_pool.browse(cr, uid, currency_id, context=context)
            rate = currency_pool._get_conversion_rate(cr, uid, po_curr_obj, base_curr_obj,
                                                      context=context)
#             exchange_rate = 1/currency_pool.browse(cr, uid, currency_id).rate
            value.update({'exchange_rate': rate})
        return {'value': value}


    def onchange_partner_id(self, cr, uid, ids, part=False):
        res = super(purchase_order, self).onchange_partner_id(cr, uid, ids, part)
        if part:
            partner_obj = self.pool.get('res.partner')
            if partner_obj.browse(cr, uid, part).sp_note_duty_exemption:
                res['value'].update({'sp_note_duty_exemption': partner_obj.browse(cr, uid, part).sp_note_duty_exemption})
        return res
    
    def send_po_mail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi po template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'hatta_purchase', 'email_template_edi_po_send')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
            
purchase_order()
class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    
    def _amount_lc_line(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pol_obj in self.browse(cr, uid, ids, context=context):
            unit_price_lc = 0.00
            amount_total_lc = 0.00
            try:
                unit_price = pol_obj.price_unit or 0.00
                discount = pol_obj.discount or 0.00
                exchange_rate = pol_obj and pol_obj.order_id and pol_obj.order_id.exchange_rate or \
                                        0.00
                unit_price_lc = unit_price * exchange_rate
                amount_total_lc = unit_price_lc * pol_obj.product_qty or 0.00
                res[pol_obj.id] = {
                                   'unit_price_lc': unit_price_lc,
                                   'amount_total_lc': amount_total_lc
                                   }
            except:
                res[pol_obj.id] = {
                                   'unit_price_lc': 0.00,
                                   'amount_total_lc': 0.00
                                   }
        return res
    
    def onchange_unit_price_fc(self, cr, uid, ids, unit_price_fc, exchange_rate, quantity, context = None):
        res = {}
        user_pool = self.pool.get('res.users')
        currncy_pool = self.pool.get('res.currency')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_currency_obj = user_obj.company_id.currency_id
        lc_unit_price = unit_price_fc
        lc_unit_price = lc_unit_price * exchange_rate
        res['value'] = {
                        'unit_price_lc': lc_unit_price,
                        'amount_total_lc': lc_unit_price * quantity,
                        'dist_cost': 0.00
                        }
        return res
    
    def onchange_unit_price_lc(self, cr, uid, ids, unit_price_lc, exchange_rate, quantity, context = None):
        res = {}
        user_pool = self.pool.get('res.users')
        currncy_pool = self.pool.get('res.currency')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_currency_obj = user_obj.company_id.currency_id
        fc_unit_price = unit_price_lc
        fc_unit_price = fc_unit_price / exchange_rate
        res['value'] = {
                        'price_unit': fc_unit_price,
                        'amount_total_lc': unit_price_lc * quantity
                        }
        return res
    
    def _get_net_dist_amount(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            dist_cost = line.dist_cost or 0.00
            price_unit_lc = line.unit_price_lc or 0.00
            res[line.id] = dist_cost + price_unit_lc
        return res
    
    def _get_pol(self, cr, uid, ids, context=None):
        pol_ids = []
        for po_obj in self.browse(cr, uid, ids, context=context):
            pol_ids.extend([x.id for x in po_obj.order_line])
        return pol_ids
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = super(purchase_order_line, self)._amount_line(cr, uid, ids, prop, arg, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            discount = line.discount or 0.00
            res[line.id] -= discount
        return res
    
    _columns = {
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure'),
#         'unit_price_lc': fields.float('Unit Price LC', digits_compute=dp.get_precision('Account')),
        'unit_price_lc': fields.function(_amount_lc_line, string='Unit Price LC', digits_compute= dp.get_precision('Account'),
                                           store={
                                                  'purchase.order': (_get_pol, ['exchange_rate'], 20),
                                                  'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit', 'product_qty', 'discount'], 10),
                                                  },
                                         multi="lc_amount"),
        'amount_total_lc': fields.function(_amount_lc_line, string='Subtotal LC', digits_compute= dp.get_precision('Account'),
                                           store={
                                                  'purchase.order': (_get_pol, ['exchange_rate'], 20),
                                                  'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit', 'product_qty', 'discount'], 10),
                                                  },
                                           multi="lc_amount"),
        'freight_charges': fields.related('order_id', 'freight_charges', type='float', string='Freight Charges FC'),
        'fob_charges': fields.related('order_id', 'fob_charges', type='float', string='Fob Charges FC'),
        'other_charges': fields.related('order_id', 'other_charges', type='float', string='Other Charges(Cert of Compliance) FC'),
        'freight_charges_lc': fields.related('order_id', 'freight_charges_lc', type='float', string='Freight Charges LC'),
        'fob_charges_lc': fields.related('order_id', 'fob_charges_lc', type='float', string='Fob Charges LC'),
        'other_charges_lc': fields.related('order_id', 'other_charges_lc', type='float', string='Other Charges(Cert of Compliance) LC'),
        'communication_charges': fields.related('order_id', 'communication_charges', type='float', string='Communication Charges'),
        'bank_charges': fields.related('order_id', 'bank_charges', type='float', string='Bank Charges'),
        'bank_interest': fields.related('order_id', 'bank_interest', type='float', string='Bank Interest(9% days)'),
        'insurance_charges': fields.related('order_id', 'insurance_charges', type='float', string='Insurance Charges'),
        'customs_duty': fields.related('order_id', 'customs_duty', type='float', string='Customs Duty(6%)'),
        'clg_agent_charges': fields.related('order_id', 'clg_agent_charges', type='float', string='Cleaning Agent Charges'),
        'clearing_expenses': fields.related('order_id', 'clearing_expenses', type='float', string='Clearing Expenses at port'),
        'transport_delivery_expenses': fields.related('order_id', 'transport_delivery_expenses', type='float', string='Transport and Delivery Expenses'),
        'misc_expenses': fields.related('order_id', 'misc_expenses', type='float', string='Misc. Expenses if any'),
        'exchange_rate': fields.related('order_id', 'exchange_rate', type='float', string='Exchange Rate'),
        'currency_id': fields.related('order_id', 'currency_id', type="many2one",
                                      relation='res.currency', string='Currency', store=True),
        'dist_cost': fields.float('Other Cost LC', digits_compute=dp.get_precision('Account')),
        'net_dist_cost': fields.function(_get_net_dist_amount, type='float',
                                         string='Net Cost LC',
                                         digits_compute=dp.get_precision('Account'),
                                         store={
                                                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['dist_cost', 'product_qty', 'discount'], 10),
                                                }),
        'select_line': fields.boolean('Select'),
        'account_id': fields.many2one('account.account', 'Account',
                                      domain="[('type', '!=', 'view')]"),
        'discount': fields.float('Total Discount FC', digits_compute=dp.get_precision('Account')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'))
        }
    
    def exchange_rate_change(self, cr, uid, ids, rate, context=None):
        po_ids = []
        po_pool = self.pool.get('purchase.order')
        for pol_obj in self.browse(cr, uid, ids, context=context):
            unit_price_fc = pol_obj.price_unit or 0.00
            unit_price_lc = unit_price_fc * rate
            pol_obj.write({'unit_price_lc': unit_price_lc})
            if pol_obj.order_id:
                po_ids.append(pol_obj.order_id.id)
        if po_ids:
            po_pool.write(cr, uid, list(set(po_ids)), {'exchange_rate': rate}, context=context)
        return True
    
purchase_order_line()

class purchase_bank_int(osv.osv):
    _name = 'purchase.bank.interest'
    _description = 'Purchase Bank Interest'
    _columns = {
                ''
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'days': fields.integer('Days'),
                'int_amount': fields.float('Interest Amount', digits_compute=dp.get_precision('Account')),
                'purchase_id': fields.many2one('purchase.order', 'Purchase')
                }
purchase_bank_int()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

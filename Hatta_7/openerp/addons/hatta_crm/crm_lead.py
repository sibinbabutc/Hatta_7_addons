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
import requests
import os
import tempfile
import base64
import time
from datetime import datetime

class crm_contact_us(osv.TransientModel):
    """ Create new leads through the "contact us" form """
    _inherit = 'portal_crm.crm_contact_us'
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        amount_total = 0.0
        for lead in self.browse(cr, uid, ids, context=context):
            for line in lead.product_lines:
                amount_total += line.price_subtotal
            res[lead.id] = amount_total
        return res
    
    
    def _get_crm(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('crm.product.lines').browse(cr, uid, ids, context=context):
            result[line.lead_id.id] = True
        return result.keys()
    _columns = {
        
        'product_lines': fields.one2many('crm.product.lines', 'lead_id', 'Enquired Products'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',type="float",
            store={
                'crm.lead': (lambda self, cr, uid, ids, c={}: ids, ['product_lines'], 10),
                'crm.product.lines': (_get_crm, ['price_unit','product_uom_qty'], 10),
            },
            help="The total amount."),
        }
crm_contact_us()
class crm_lead(osv.osv):
    _inherit = 'crm.lead'
    _order = 'creation_date desc, reference desc'
    
    def create(self, cr, uid, vals, context=None):
        partner_pool = self.pool.get('res.partner')
        expected_closing_date = vals.get('date_deadline', False)
        transaction_type_pool = self.pool.get('transaction.type')
        avoid_def_seq = False
        transaction_type_id = vals.get('transaction_type_id', False)
        print transaction_type_id,"-------------->TTTT"
        partner_id = vals.get('partner_id', False)
        if partner_id:
            partner_obj = partner_pool.browse(cr, uid, partner_id, context=context)
        else:
            raise osv.except_osv(_("Error !!!"),
                                 _("Please select a customer"))
        if transaction_type_id:
            transaction_type_obj = transaction_type_pool.browse(cr, uid, transaction_type_id, context=context)
            print transaction_type_obj.partner_seq
            if transaction_type_obj.partner_seq:
                partner_id = vals.get('supplier_id', False)
                if partner_id:
                    partner_obj = partner_pool.browse(cr, uid, partner_id, context=context)
                else:
                    raise osv.except_osv(_("Error !!!"),
                                         _("Please select a Supplier"))
                partner_seq = partner_obj.seq_id or False
                if partner_seq:
                    avoid_def_seq = True
                    seq_no = self.pool.get('ir.sequence').next_by_id(cr, uid, partner_seq.id, context=context)
                    vals['reference'] = seq_no
                else:
                    raise osv.except_osv(_("Error !!!"),
                                     _("Please define sequence in customer !!!"))
            elif transaction_type_obj.sequence_id:
                avoid_def_seq = True
                seq_no = self.pool.get('ir.sequence').next_by_id(cr, uid,
                                                                 transaction_type_obj.sequence_id.id,
                                                                 context=context)
                vals['reference'] = seq_no
        if not avoid_def_seq:
            seq_no = self.pool.get('ir.sequence').get(cr, uid, 'crm.lead')
            if expected_closing_date:
                date_deadline = datetime.strptime(expected_closing_date, "%Y-%m-%d")
                date_deadline = str(date_deadline.strftime("%y-%d%m"))
                seq_no += date_deadline
            partner_code = partner_obj.partner_code or ''
            seq_no += str(partner_code)
            vals['reference'] = seq_no
        res = super(crm_lead, self).create(cr, uid, vals, context=context)
        return res
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        amount_total = 0.0
        for lead in self.browse(cr, uid, ids, context=context):
            for line in lead.product_lines:
                amount_total += line.price_unit * line.product_uom_qty
            res[lead.id] = amount_total
        return res
    
    def convert_to_opportunity(self, cr, uid, ids, context=None):
        attachment_pool = self.pool.get('ir.attachment')
        param_pool = self.pool.get('ir.config_parameter')
        for lead_obj in self.browse(cr, uid, ids, context=context):
            if (lead_obj.type == 'lead' or lead_obj.type == False) and \
                        lead_obj.partner_id:
                self.convert_opportunity(cr, uid, ids, lead_obj.partner_id.id, user_ids=False,
                                         section_id=False, context=context)
            attach_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'crm.lead'),
                                                          ('res_id', 'in', ids)],
                                                context=context)
            api_key = param_pool.get_param(cr, uid,
                                           "pdf.doc.api.key",
                                           context=context)
            if api_key:
                for attach_obj in attachment_pool.browse(cr, uid, attach_ids,
                                                         context=context):
                    filename = attach_obj.datas_fname
                    fname,ext = filename and os.path.splitext(filename) or ('','')
                    if ext == '.pdf':
                        temp_file_dir = tempfile.gettempdir()
                        file_path = os.path.join(temp_file_dir, "mail_pdf_download" + ".pdf")
                        doc_file_path = os.path.join(temp_file_dir, "mail_pdf_download" + ".doc")
                        f = open(file_path, 'w')
                        f.write(base64.b64decode(attach_obj.datas))
                        f.close()
                        r = requests.post("https://api.cloudconvert.com/convert?apikey=%s&input=upload&download=inline&inputformat=pdf&outputformat=doc"%(api_key),
                                          files = {'file': open(file_path, 'rb')})
                        with open(doc_file_path, 'wb') as fd:
                            for chunk in r.iter_content(1024):
                                fd.write(chunk)
                        f = open(doc_file_path, 'r')
                        data = f.read()
                        vals = {
                                'name': fname + ".doc",
                                'datas': base64.b64encode(data),
                                'datas_fname': fname + ".doc",
                                'res_model': 'crm.lead',
                                'res_id': lead_obj.id,
                                'type': 'binary'
                                }
                        attach_id = attachment_pool.create(cr, uid, vals, context=context)
                        f.close()
        return True
    
    def _get_crm(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('crm.product.lines').browse(cr, uid, ids, context=context):
            result[line.lead_id.id] = True
        return result.keys()
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, email_from, context=None):
        partner_pool = self.pool.get('res.partner')
        res = super(crm_lead, self).onchange_partner_id(cr, uid, ids, partner_id, email_from)
        if partner_id:
            address_data = partner_pool.address_get(cr, uid, [partner_id],
                                                    adr_pref=['procure', 'delivery', 'contact'], context={})
            print address_data
            procure_address_id = address_data.get('procure', False)
            del_address_id = address_data.get('delivery', False)
            contact_address_id = address_data.get('contact', False)
            res['value']['partner_procure_id'] = procure_address_id
            res['value']['partner_delivery_id'] = del_address_id
            res['value']['contact_id'] = contact_address_id
            res['value']['inquiry_id'] = partner_id
        return res
    
    def _get_default_ana_account(self, cr, uid, context=None):
        analy_pool = self.pool.get('account.analytic.account')
        account_ids = analy_pool.search(cr, uid, [('default', '=', True)],
                                        context=context)
        if account_ids:
            return account_ids[0]
        return False
    
    def onchange_transaction_type(self, cr, uid, ids, transaction_type_id, context=None):
        res = {'value': {}}
        transaction_type_pool = self.pool.get('transaction.type')
        if transaction_type_id:
            transaction_type_obj = transaction_type_pool.browse(cr, uid, transaction_type_id,
                                                                context=context)
            res['value']['analytic_account_id'] = transaction_type_obj.cost_center_id and \
                                                        transaction_type_obj.cost_center_id.id or False
            res['value']['partner_seq'] = transaction_type_obj.partner_seq or False
            res['value']['direct_invoice'] = transaction_type_obj.direct_invoice or False
            res['value']['track_revision'] = transaction_type_obj.track_revision or False
        return res
    
    def _get_default_curr(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        return user_obj.company_id.currency_id.id
    
    _rec_name = 'reference'
    _columns = {
        'reference': fields.char('Reference', size=128),
        'customer_rfq': fields.char('Customer RFQ', size=64),
        'product_lines': fields.one2many('crm.product.lines', 'lead_id', 'Enquired Products'),
        'date_deadline': fields.date('Expected Closing', help="Estimate of the date on which the opportunity will be won."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',type="float",
            store={
                'crm.lead': (lambda self, cr, uid, ids, c={}: ids, ['product_lines'], 10),
                'crm.product.lines': (_get_crm, ['price_unit','product_uom_qty'], 10),
            },
            help="The total amount."),
        'creation_date': fields.date('Creation Date'),
        'name': fields.char('Subject', size=64, required=False, select=1),
        'partner_procure_id': fields.many2one('res.partner', 'Procurement Address'),
        'partner_delivery_id': fields.many2one('res.partner', 'Delivery Address'),
        'call_no': fields.char('Coll. RFQ NO. / Buyer Ref.', size=128),
        'coll_no_type': fields.selection([('coll', 'Coll. RFQ NO.'),
                                          ('buyer', 'Buyer Ref.')],
                                         'Type'),
        'cust_remark': fields.text('Customer Remark'),
        'sale_id': fields.many2one('sale.order', 'Related Sale Order'),
        'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Cost Center'),
        'send_quote_mail': fields.related('analytic_account_id', 'send_quote_mail',
                                          type="boolean", string="Send Quote by mail"),
        'product_type': fields.char('Product Type', size=128),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term'),
        'delivery_terms': fields.char('Delivery Term', size=128),
        'quote_validity': fields.char('Quote Validity', size=128),
        'partner_seq': fields.boolean('Partner Based Seq. Sufix'),
        'supplier_id': fields.many2one('res.partner', 'Principal suppliers'),
        'contact_id': fields.many2one('res.partner', 'Contact'),
        'direct_invoice': fields.boolean('Direct Invoice?'),
        'invoice_ids': fields.one2many('account.invoice', 'direct_lead_id', 'Direct Invoice Rel.'),
        'state': fields.selection([('draft', 'New'), ('quote_send', 'Quotation Sent'), ('revised', 'Revised'),
                                   ('regret', 'Regret'), ('cancel', 'Cancelled')], 'State'),
        'inquiry_id': fields.many2one('res.partner', 'End User', domain="[('customer', '=', True)]"),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'revision_number': fields.char('Revision Number', size=64),
        'track_revision': fields.boolean('Track Revision ?')
        }
    _defaults = {
                 'creation_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'coll_no_type': 'coll',
                 'analytic_account_id': _get_default_ana_account,
                 'state': 'draft',
                 'currency_id': _get_default_curr,
                 'description': """Reference to your inquiry, please find attached our best offer for your kind perusal.

In case of any changes in the quantities, please contact us for confirmation of validity of prices with our principal supplier/s."""
                 }
    
    def create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        transaction_type_pool = self.pool.get('transaction.type')
        invoice_line_pool = self.pool.get('account.invoice.line')
        lead_obj = self.browse(cr, uid, ids[0], context=context)
        ctx = context.copy()
        transaction_type_id = False
        cost_center_id = lead_obj.analytic_account_id and lead_obj.analytic_account_id.id or False
        if cost_center_id:
            transaction_type_ids = transaction_type_pool.search(cr, uid,
                                                                [('cost_center_id', '=', cost_center_id),
                                                                 ('model_id.model', '=', 'account.invoice'),
                                                                 ('refund', '=', False)])
            if not transaction_type_ids:
                raise osv.except_osv(_("Error!!!"),
                                     _("Please configure transaction type"))
            transaction_type_id = transaction_type_ids[0]
        lines = []
        for line in lead_obj.product_lines:
            onchange_product_data = invoice_line_pool.product_id_change(cr, uid, ids, line.product_id.id,
                                                                        False, 1.00, '', 'out_invoice',
                                                                        lead_obj.partner_id and lead_obj.partner_id.id or False,
                                                                        False, 0.00, False, {}, False)
            account_id = onchange_product_data.get('value', {}).get('account_id', False)
            line_vals = {
                         'sequence_no': line.sequence_no or '',
                         'product_id': line.product_id and line.product_id.id,
                         'quantity': line.product_uom_qty or 1.00,
                         'uos_id': line.uom_id and line.uom_id.id or False,
                         'price_unit': line.price_unit or 0.00,
                         'name': line.description or '',
                         'account_id': account_id
                         }
            lines.append((0, 0, line_vals))
        ctx.update({
                    'default_payment_term': lead_obj.payment_term_id and lead_obj.payment_term_id.id or False,
                    'default_partner_id': lead_obj.partner_id and lead_obj.partner_id.id or False,
                    'default_parent_partner_id': lead_obj.partner_id and lead_obj.partner_id.id or False,
                    'default_transaction_type_id': transaction_type_id or False,
                    'default_cost_center_id': lead_obj.analytic_account_id and lead_obj.analytic_account_id.id or False,
                    'default_name': lead_obj.customer_rfq or '',
                    'default_invoice_line': lines,
                    'default_type':'out_invoice',
                    'type':'out_invoice',
                    'journal_type': 'sale'
                    })
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['context'] = ctx
        return result
    
    def send_sale_quote_mail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'hatta_crm', 'email_template_edi_sale_quote')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'crm.lead',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
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
    
#     def copy(self, cr, uid, id, default=None, context=None):
#         if default is None:
#             default = {}
#         crm_obj = self.browse(cr, uid, id, context=context)
#         lines = []
#         for line in crm_obj.product_lines:
#             vals= {
#                    'product_id': line.product_id and line.product_id.id or False,
#                    'description': line.description,
#                    'product_uom_qty': line.product_uom_qty,
#                    'uom_id': line.uom_id.id,
#                    'price_unit': 0.00,
#                    'price_subtotal': 0.00,
#                    'select': True,
#                    'cost_price': 0.00,
#                    'factor': 0.00,
#                    'sequence_no': line.sequence_no
#                    }
#             lines.append((0, 0, vals))
#         default['product_lines'] = lines
#         res = super(crm_lead, self).copy(cr, uid, id, default, context=context)
#         return res
    
    def view_pos(self, cr, uid, ids, context=None):
        lead = self.browse(cr, uid, ids)[0]
        po_pool = self.pool.get('purchase.order')
        lead_po_ids = po_pool.search(cr, uid, [('lead_id', '=', lead.id)])
        if lead_po_ids:
            if context is None:
                context = {}
            context.update({
                'form_view_ref': 'hatta_purchase.purchase_order_form_inherit',
                'tree_view_ref': 'hatta_purchase.purchase_order_tree_inherit'
                })
            return {
                'name': 'Request For Quotations',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('lead_id', '=', lead.id)],
                'res_id': lead_po_ids and lead_po_ids[0] or False,
                
                
                'context': context,
                }
        else:
            raise osv.except_osv(_('Warning!'),_('No requests for quotations'))
        return True
    def view_sqo(self, cr, uid, ids, context=None):
        sale_order_pool = self.pool.get('sale.order')
        lead_so_ids = sale_order_pool.search(cr, uid, [('lead_id', 'in', ids)])
        if lead_so_ids:
            if context is None:
                context = {}
            context.update({
                'form_view_ref': 'hatta_crm.view_order_form_inherit1',
                })
            return {
                'name': 'Sale Order',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('lead_id', 'in', ids)],
                'res_id': lead_so_ids and lead_so_ids or False,
                
                
                'context': context,
                }
        else:
            raise osv.except_osv(_('Warning!'),_('No Sales Quotations'))
        return True
crm_lead()

class crm_product_lines(osv.osv):
    _name = 'crm.product.lines'
    
        
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
#         tax_obj = self.pool.get('account.tax')
#         cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * line.product_uom_qty
            
            res[line.id] = price
        return res
    
    def _get_cost_price(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_pool = self.pool.get('product.uom')
        purchase_pool = self.pool.get('purchase.order')
        purchase_line_pool = self.pool.get('purchase.order.line')
        for line_obj in self.browse(cr, uid, ids, context=context):
            amount = 0.00
            lead_obj = line_obj.lead_id
            product_obj = line_obj.product_id
            if lead_obj and product_obj:
                purchase_ids = purchase_pool.search(cr, uid, [('lead_id', '=', lead_obj.id)],
                                                    context=context)
                recalc = True
                if purchase_ids:
                    recalc = False
                    purchase_line_ids = purchase_line_pool.search(cr, uid, [('order_id', 'in', purchase_ids),
                                                                            ('product_id', '=', product_obj.id),
                                                                            ('cust_selected', '=', True)],
                                                                  context=context)
                    if not purchase_line_ids:
                        recalc = True
                    for purchase_line_obj in purchase_line_pool.browse(cr, uid, purchase_line_ids,
                                                                       context=context):
                        amount += purchase_line_obj.net_dist_cost
                if recalc:
                    product_uom_id = product_obj.uom_id.id or False
                    uom_id = line_obj.uom_id.id or False
                    unit_qty = 1.00
                    if product_uom_id != uom_id:
                        unit_qty = uom_pool._compute_qty(cr, uid, uom_id, 1, product_uom_id)
                    cost_price = product_obj.standard_price or 0.00
                    amount += cost_price * unit_qty
            res[line_obj.id] = amount
        return res
    
    def _default_sequence(self, cr, uid, context=None):
        if context == None:
            context = {}
        order_line = self.pool.get('crm.product.lines')
        false_len = 0
        for line_id in context.get('order_id', []):
            if line_id[1] == False:
                false_len += 1
        if context.get('order_id', False):
            if context['order_id'][0][1] != False:
                ids = context['order_id'][0][1]
                order_id = order_line.browse(cr, uid, ids).lead_id
                return str(false_len)
            else:
                order_id = context.get('order_id', [])
                if order_id==[]:
                    return str(1)
                elif len(order_id)==1:
                    return str(len(order_id)+1)
                else:
                    return str(len(order_id)+1)
        else:
            order_id = context.get('order_id', [])
            if order_id:
                return str(1)
            elif len(order_id)==1:
                return str(len(order_id)+1)
            else:
                return str(len(order_id)+1)
    
    def _get_selected_pol_line(self, cr, uid, ids, name, args, context=None):
        res = {}
        for lead_line in self.browse(cr, uid, ids, context=context):
            result = False
            has = False
            overide = False
            for line in lead_line.pol_ids:
                if line.select_line and not overide and line.order_id.state != 'cancel':
                    result = line.id
                    if line.cust_selected:
                        overide = True
                    if has and not overide:
                        result = False
                    has = True
            res[lead_line.id] = result
        return res
    
    def _get_product_line(self, cr, uid, ids, context=None):
        res = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.lead_product_id:
                res.append(line.lead_product_id.id)
        return res
    
    def _get_price_unit(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = 0.00
            if line.overide_sale_price > 0.00:
                price = line.overide_sale_price or 0.00
            else:
                if line.selected_pol_id:
                    price = line.selected_pol_id.sale_price or 0.00
            res[line.id] = price
        return res
    
    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'description': fields.text('Description'),
        'product_uom_qty': fields.float('Quantity'),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'taxes_id': fields.many2many('account.tax', 'purchase_order_taxe', 'ord_id', 'tax_id', 'Taxes'),
        'overide_sale_price': fields.float('Manual Sale Price', digits_compute= dp.get_precision('Account')),
#         'price_unit': fields.float('Unit Price'),
        'price_unit': fields.function(_get_price_unit, type="float", string="Unit Sale Price"),
#         'price_unit': fields.related('selected_pol_id', 'sale_price', type="float", digits_compute= dp.get_precision('Account')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'selected_pol_id': fields.function(_get_selected_pol_line, type='many2one',
                                           relation='purchase.order.line',
                                           string='Selected Purchase Line'),
        'lead_id': fields.many2one('crm.lead', 'Lead'),
        'select': fields.boolean('Select'),
        'cost_price': fields.function(_get_cost_price, type="float", string="Unit Cost Price"),
        'factor': fields.float('Ratio', digits=(16, 8)),
        'sequence_no': fields.char('Sequence', size=64, select=True),
        'certificate_ids': fields.many2many('product.certificate', 'certificate_lead_rel', 'lead_line_id', 'certificate_id',
                                            'Certificate(s)'),
        'pol_ids': fields.one2many('purchase.order.line', 'lead_product_id', 'Purchase Line'),
        'manufacturer_id': fields.many2one('res.partner', 'Manufacturer')
        }
    _defaults = {
        'product_uom_qty': 1,
        'select': True,
        'price_unit': 0.00,
        'cost_price': 0.00,
#         'sequence_no': lambda obj, cr, uid, context: obj._default_sequence(cr, uid, context),
        }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['price_unit'] = 0.00
        default['cost_price'] = 0.00
        res = super(crm_product_lines, self).copy(cr, uid, id, default, context=context)
        return res
    
    def onchange_product_id(self, cr, uid, ids, product_id, qty, uom_id, context=None):
        value = {}
        if context is None:
            context = {}
        uom_pool = self.pool.get('product.uom')
        ana_pool = self.pool.get('account.analytic.account')
        if product_id:
            product_obj = self.pool.get('product.product')
            product = product_obj.browse(cr, uid, product_id)
            product_uom_id = product.uom_id.id or False
            analytic_account_id = context.get('analytic_account_id', False)
            if analytic_account_id:
                analytic_account_obj = ana_pool.browse(cr, uid, analytic_account_id, context=context)
                if analytic_account_obj.system_sale_price:
                    unit_qty = 1.00
                    if product_uom_id != uom_id:
                        unit_qty = uom_pool._compute_qty(cr, uid, uom_id, 1, product_uom_id)
                    price_unit = product.list_price * unit_qty
                    cost_price = product.standard_price * unit_qty
                    value['price_unit'] = price_unit
                    value['cost_price'] = cost_price
            certiticate_ids = [x.id for x in product.certificate_ids]
            value.update({
                          'certificate_ids': certiticate_ids,
                          'manufacturer_id': product.manufacturer_id and product.manufacturer_id.id or \
                                            False
                          })
            if not uom_id:
                value.update({'uom_id': product.uom_id.id or False})
        return {'value': value}
crm_product_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

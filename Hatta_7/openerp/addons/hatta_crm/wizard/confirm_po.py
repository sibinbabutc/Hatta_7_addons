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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import netsvc

class confirm_po(osv.osv_memory):
    _name = 'confirm.po'
    
    def default_get(self, cr, uid, field_name, context=None):
        if context is None:
            context = {}
        po_pool = self.pool.get('purchase.order')
        obj_sequence = self.pool.get('ir.sequence')
        res = super(confirm_po, self).default_get(cr, uid, field_name, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            po_obj = po_pool.browse(cr, uid, active_id, context=context)
            seq = po_obj.name
            if po_obj.transaction_type_id and po_obj.transaction_type_id.sequence_id:
                check_po_ids = []
                if po_obj.unused_seq:
                    seq = po_obj.unused_seq
                    check_po_ids = po_pool.search(cr, uid, [('name', '=', po_obj.unused_seq), ('id', '!=', po_obj.id)],
                                                  context=context)
                if check_po_ids or not po_obj.unused_seq:
                    seq = obj_sequence.next_by_id(cr, uid,
                                                  po_obj.transaction_type_id.sequence_id.id,
                                                  context=context)
                    po_obj.write({'unused_seq': seq, 'rfq_name': po_obj.name})
            res.update({
                        'payment_term_id': po_obj.payment_term_id and \
                                                po_obj.payment_term_id.id or False,
                        'pricelist_id': po_obj.pricelist_id.id or False,
                        'delivery_term': po_obj.delivery_term or '',
                        'delivery_inco': po_obj.incoterm_id and po_obj.incoterm_id.id or False,
                        'display_end_user': po_obj.display_end_user_name or False,
                        'supplier_quote_ref': po_obj.partner_ref,
                        'quote_send_by': po_obj.quote_send_by,
                        'direct_delivery': po_obj.direct_delivery or False,
#                         'supplier_shipping': po_obj.supplier_shipping or False,
                        'po_id': po_obj.id or False,
                        'minimum_planned_date': po_obj.minimum_planned_date,
                        'quote_date': po_obj.quote_date,
                        'direct_del_address': po_obj.direct_del_address,
                        'po_name': seq,
                        'direct_purchase': po_obj.direct_purchase
                        })
            if po_obj.po_notes or po_obj.direct_purchase:
                res['note'] = po_obj.po_notes or ''
        return res
    
    _columns = {
                'payment_term_id': fields.many2one('account.payment.term', 'Payment Term'),
                'delivery_term': fields.char('Delivery Period', size=128),
                'delivery_inco': fields.many2one('stock.incoterms', 'Delivery Term'),
                'display_end_user': fields.boolean('Display End User ?'),
                'direct_delivery': fields.boolean('Direct Delivery ?'),
#                 'supplier_shipping': fields.boolean('Supplier Shipping ?'),
                'note': fields.text('Note'),
                'supplier_quote_ref': fields.char('Supplier Quote Ref.', size=128),
                'quote_send_by': fields.char('Quote Send By', size=128),
                'po_id': fields.many2one('purchase.order', 'Purchase Order'),
                'minimum_planned_date': fields.date('Delivery Date'),
                'quote_date': fields.date('Quote Date'),
                'direct_del_address': fields.text('Delivery Address'),
                'po_name': fields.char('Purchase Name', sze=128),
                'direct_purchase': fields.boolean('Direct Purchase'),
                'pricelist_id': fields.many2one('product.pricelist', 'Pricelist')
                }
    
    _defaults = {
                 'note': """1) KINDLY ACKNOWLEDGE THE PO DULY STAMPED AND SIGNED.
2) PLEASE ADVICE WHEN THE MATERIAL IS READY FOR COLLECTION
3) KINDLY INDICATE OUR A/C NO & PO NO IN ALL YOUR CORRESPONDENCE, INVOICE, ETC."""
                 }
    
    def confirm_po(self, cr, uid, ids, context=None):
        po_pool = self.pool.get('purchase.order')
        data = self.read(cr, uid, ids, context={})[0]
        po_id = data.get('po_id', False)
        wf_service = netsvc.LocalService('workflow')
        if po_id:
            po_id = po_id[0]
            payment_term_id = data.get('payment_term_id', False)
            delivery_term = data.get('delivery_term', False)
            display_end_user = data.get('display_end_user', False)
            direct_delivery = data.get('direct_delivery', False)
#             supplier_shipping = data.get('supplier_shipping', False)
            note = data.get('note', False)
            supplier_quote_ref = data.get('supplier_quote_ref', False)
            quote_send_by = data.get('quote_send_by', False)
            minimum_planned_date = data.get('minimum_planned_date', False)
            quote_date = data.get('quote_date', False)
            direct_del_address = data.get('direct_del_address', '')
            po_name = data.get('po_name', '')
            delivery_inco = data.get('delivery_inco', False)
            vals = {
                    'delivery_term': delivery_term,
                    'display_end_user_name': display_end_user,
                    'po_notes': note,
                    'partner_ref': supplier_quote_ref,
                    'quote_send_by': quote_send_by,
                    'direct_delivery': direct_delivery,
#                     'supplier_shipping': supplier_shipping,
                    'minimum_planned_date': minimum_planned_date,
                    'quote_date': quote_date,
                    'direct_del_address': direct_del_address,
                    'name': po_name,
                    'incoterm_id': delivery_inco and delivery_inco[0] or False,
                    'state': 'validated'
                    }
            if payment_term_id:
                payment_term_id = payment_term_id[0]
                vals['payment_term_id'] = payment_term_id
            purchase_obj = po_pool.browse(cr, uid, po_id, context=context)
            if purchase_obj.state in ['draft', 'sent']:
                wf_service.trg_validate(uid, 'purchase.order', \
                                            po_id, 'bid_received', cr)
            lead_id = purchase_obj.lead_id and purchase_obj.lead_id.id or False
            domain = [('state', 'not in', ['draft', 'bid', 'cancel', 'sent'])]
            if lead_id:
                domain.append(('lead_id', '=', lead_id))
            elif purchase_obj.direct_sale_id:
                domain.append(('direct_sale_id', '=', purchase_obj.direct_sale_id.id))
            else:
                domain.append(('id', '=', 0))
            po_ids = po_pool.search(cr, uid, domain, context=context)
            po_objs = po_pool.browse(cr, uid, po_ids, context=context)
            old_rfq_no = purchase_obj.name
            vals.update({'unused_seq': old_rfq_no})
            line_order_list = [x.line_of_order for x in po_objs]
            line_order = False
            i = 1
            while True:
                if i not in line_order_list:
                    line_order = i
                    break;
                i += 1
            vals.update({'line_of_order': line_order})
            return po_pool.write(cr, uid, po_id, vals, context=context)
#             return po_pool.purchase_confirm(cr, uid, [po_id], context=context)
        return True
    
confirm_po()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

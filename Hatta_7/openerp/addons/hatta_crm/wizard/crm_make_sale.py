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

from openerp.tools.translate import _
from datetime import datetime, date
from openerp import netsvc

class crm_make_sale(osv.osv_memory):
    _inherit = 'crm.make.sale'
    def makeOrder(self, cr, uid, ids, context=None):
        sale_order_obj = self.pool.get('sale.order')
        crm_obj = self.pool.get('crm.lead')
        sale_order_line_obj = self.pool.get('sale.order.line')
        attachment_pool = self.pool.get('ir.attachment')
        create_line_pool = self.pool.get('so.create.line')
        transaction_type_pool = self.pool.get('transaction.type')
        obj_sequence = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService('workflow')
        res = super(crm_make_sale,self).makeOrder(cr, uid, ids, context=context)
        data = self.read(cr, uid, ids, context=context)[0]
        lines = data.get('line_ids', [])
        date_planned = data.get('delivery_date', False)
        customer_po_no = data.get('customer_po_no', '')
        payment_term_id = data.get('payment_term_id', False) and data.get('payment_term_id', False)[0] or False
        cost_center_id = False
        if data.get('cost_center_id', False):
            cost_center_id = data['cost_center_id'][0]
        to_create_lines = []
        if lines:
            lines_obj = create_line_pool.browse(cr, uid, lines, context=context)
            to_create_lines = [x.line_id.id for x in lines_obj if x.line_id]
        sale_order_ids = res['res_id']
        if not isinstance(sale_order_ids, list):
            sale_order_ids = [sale_order_ids]
        for sale_order_id in sale_order_ids:
            active_ids = context and context.get('active_ids', []) or []
            crm = crm_obj.browse(cr ,uid, active_ids[0], context=context)
            crm.write({'sale_id': sale_order_id})
            analytic_account_id = crm.analytic_account_id and \
                                     crm.analytic_account_id.id or False
            transaction_type_id = False
            if analytic_account_id:
                transaction_type_ids = transaction_type_pool.search(cr, uid, [('cost_center_id', '=', analytic_account_id),
                                                                              ('model_id.model', '=', 'sale.order')])
                if transaction_type_ids:
                    transaction_type_id = transaction_type_ids[0]
            if not transaction_type_id:
                raise osv.except_osv(_("Error !!!"),
                                     _("Please configure transaction type !!"))
            sale_order = sale_order_obj.browse(cr, uid, sale_order_id)
            tran_obj = transaction_type_pool.browse(cr, uid, transaction_type_id, context=context)
            sale_name = sale_order.name or ''
            if tran_obj.sequence_id:
                sale_name = obj_sequence.next_by_id(cr, uid, tran_obj.sequence_id.id, context=context)
            sale_order.write({'date_delivery': date_planned, 'cost_center_id': analytic_account_id,
                              'transaction_type_id': transaction_type_id, 'name':sale_name,
                              'payment_term': payment_term_id, 'delivery_terms': crm.delivery_terms,
                              'lead_id': crm.id, 'client_order_ref': customer_po_no or '',
                              'payment_term_id': payment_term_id})
            if sale_order.job_id:
                sale_order.job_id.write({'lead_id': crm.id})
            if crm.product_lines:
                for product_line in crm.product_lines:
                    if product_line.id in to_create_lines:
                        product_line.selected_pol_id.write({'cust_selected': True})
                        cert_data = [(4, x.id) for x in product_line.certificate_ids]
                        product_line_dict = {
                                    'sequence_no': product_line.sequence_no,
                                    'product_id': product_line.product_id.id,
                                    'name': product_line.description,
                                    'product_uom_qty': product_line.product_uom_qty,
                                    'price_unit': product_line.price_unit,
                                    'price_subtotal': product_line.price_subtotal,
                                    'order_id': sale_order_id,
                                    'type': 'make_to_stock',
                                    'certificate_ids': cert_data,
                                    'crm_line_id': product_line.id,
                                    'pol_remark': product_line.selected_pol_id.remark or '',
                                    'product_uom': product_line.uom_id and product_line.uom_id.id or False
                                    }
                        sale_order_line_obj.create(cr, uid, product_line_dict, context=context)
            lead_attachment_ids  = attachment_pool.search(cr, uid, [('res_model', '=', 'crm.lead'), ('res_id', '=', active_ids[0])], context=context)
            if lead_attachment_ids:
                for lead_attachment_id in lead_attachment_ids:
                    lead_attachment = attachment_pool.browse(cr, uid, lead_attachment_id)
                    dict_attachment = {
                            'name': lead_attachment.name,
                            'type': lead_attachment.type,
                            'datas': lead_attachment.datas,
                            'user_id': lead_attachment.user_id.id,
                            'res_model':'sale.order',
                            'res_id': sale_order_id,
                            'res_name': sale_order.name,
                            'partner': sale_order.partner_id.name,
                            
                            }
                    attachment_pool.create(cr, uid, dict_attachment)
#         sale_order_obj.action_button_confirm(cr, uid, sale_order_ids, context=context)
        return res
crm_make_sale()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

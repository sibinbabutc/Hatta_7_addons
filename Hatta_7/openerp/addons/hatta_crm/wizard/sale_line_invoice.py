# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc
import time

class sale_order_line_make_invoice(osv.osv_memory):
    _inherit = "sale.order.line.make.invoice"
    _description = "Sale OrderLine Make_invoice"
    
    def make_invoices(self, cr, uid, ids, context=None):
        """
             To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        if context is None: context = {}
        res = False
        invoices = {}
        transaction_type_pool = self.pool.get('transaction.type')
        obj_sequence = self.pool.get('ir.sequence')
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_currency = user_obj.company_id.currency_id

    #TODO: merge with sale.py/make_invoice
        def make_invoice(order, lines, company_currency):
            """
                 To make invoices.

                 @param order:
                 @param lines:

                 @return:

            """
            sale_currency = order.currency_id
            exchange_rate = currency_pool._get_conversion_rate(cr, uid, sale_currency, company_currency,
                                                           context=context)
            a = order.partner_id.property_account_receivable.id
            if order.partner_id and order.partner_id.property_payment_term.id:
                pay_term = order.partner_id.property_payment_term.id
            else:
                pay_term = False
            inv = {
                'discount': order.discount,
                'exchange_rate': exchange_rate,
                'name': order.client_order_ref or '',
                'origin': order.name,
                'type': 'out_invoice',
                'reference': "P%dSO%d" % (order.partner_id.id, order.id),
                'account_id': a,
                'partner_id': order.partner_invoice_id.id,
                'invoice_line': [(6, 0, lines)],
                'currency_id' : order.pricelist_id.currency_id.id,
                'comment': order.note,
                'payment_term': pay_term,
                'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                'user_id': order.user_id and order.user_id.id or False,
                'company_id': order.company_id and order.company_id.id or False,
                'date_invoice': fields.date.today(),
                'sale_id': order.id,
                'job_id': order.job_id and order.job_id.id or False,
                'parent_partner_id': order.partner_id and order.partner_id.id or False
            }
            invoice_number = ''
            if order.unposted:
                for invoice in order.invoice_ids:
                    if invoice.unposted and invoice.state == 'cancel':
                        invoice_number = invoice.internal_number or ''
                        print invoice_number
                        inv['internal_number'] = invoice_number
                        invoice.write({'internal_number': invoice_number + "Cancelled" + str(time.strftime('%d/%m/%Y %H:%M:%S')),
                                       'unposted': False})
            if order.cost_center_id:
                transaction_type_ids = transaction_type_pool.search(cr, uid,
                                                                    [('cost_center_id', '=', order.cost_center_id.id),
                                                                     ('model_id.model', '=', 'account.invoice')],
                                                                    context=context)
                if transaction_type_ids:
                    inv['transaction_type_id'] = transaction_type_ids[0]
                    inv['cost_center_id'] = order.cost_center_id.id
                    tran_obj = transaction_type_pool.browse(cr, uid, transaction_type_ids[0], context=context)
                    if tran_obj.sequence_id and not invoice_number:
                        inv_number = obj_sequence.next_by_id(cr, uid,
                                                             tran_obj.sequence_id.id,
                                                             context=context)
                        inv['internal_number'] = inv_number
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv)
            return inv_id

        sales_order_line_obj = self.pool.get('sale.order.line')
        sales_order_obj = self.pool.get('sale.order')
        wf_service = netsvc.LocalService('workflow')
        for line in sales_order_line_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if (not line.invoiced) and (line.state not in ('draft', 'cancel')):
                if not line.order_id in invoices:
                    invoices[line.order_id] = []
                line_id = sales_order_line_obj.invoice_line_create(cr, uid, [line.id])
                for lid in line_id:
                    invoices[line.order_id].append(lid)
        for order, il in invoices.items():
            res = make_invoice(order, il, company_currency)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, res))
            flag = True
            data_sale = sales_order_obj.browse(cr, uid, order.id, context=context)
            for line in data_sale.order_line:
                if not line.invoiced:
                    flag = False
                    break
            if flag:
                wf_service.trg_validate(uid, 'sale.order', order.id, 'manual_invoice', cr)

        if not invoices:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n1.The state of this sales order line is either "draft" or "cancel"!\n2.The Sales Order Line is Invoiced!'))
        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, res, context=context)
        return {'type': 'ir.actions.act_window_close'}

sale_order_line_make_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

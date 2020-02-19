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

from tools.translate import _

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
                'refund_invoice_id': fields.many2one('account.invoice', 'Refunded Invoice')
                }
    
    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None,
                        journal_id=None, context=None):
        transaction_type_pool = self.pool.get('transaction.type')
        obj_sequence = self.pool.get('ir.sequence')
        res = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date, period_id,
                                                           description, journal_id,
                                                           context=context)
        if invoice:
            res['sale_id'] = invoice.sale_id and invoice.sale_id.id or False
            res['job_id'] = invoice.job_id and invoice.job_id.id or False
            res['parent_partner_id'] = invoice.parent_partner_id.id or False
            res['exchange_rate'] = invoice.exchange_rate or 1.0000
            res['discount'] = invoice.discount or 0.00
            res['refund_invoice_id'] = invoice.id
            if invoice.cost_center_id:
                invoice_number = ''
                transaction_type_ids = transaction_type_pool.search(cr, uid,
                                                                    [('model_id.model', '=', 'account.invoice'),
                                                                     ('refund', '=', True)],
                                                                    context=context)
                if transaction_type_ids:
                    res['transaction_type_id'] = transaction_type_ids[0]
                    res['cost_center_id'] = invoice.cost_center_id.id
                    tran_obj = transaction_type_pool.browse(cr, uid, transaction_type_ids[0], context=context)
                    if tran_obj.sequence_id and not invoice_number:
                        inv_number = obj_sequence.next_by_id(cr, uid,
                                                             tran_obj.sequence_id.id,
                                                             context=context)
                        res['internal_number'] = inv_number
        return res
    
    def view_related_returns(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        invoice_pool = self.pool.get('account.invoice')

        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        invoice_ids = invoice_pool.search(cr, uid, [('refund_invoice_id', 'in', ids)],
                                          context=context)
        if not invoice_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("No Sales Return found for this invoice !!!!"))
        #choose the view_mode accordingly
        if len(invoice_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, invoice_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = invoice_ids and invoice_ids[0] or False
        return result
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

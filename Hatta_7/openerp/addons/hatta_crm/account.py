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

import time
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
                'sequence_no': fields.char('SI. No', size=64)
                }
account_invoice_line()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def _get_status(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice_obj in self.browse(cr, uid, ids, context=context):
            if invoice_obj.state in ['draft', 'proforma2']:
                res[invoice_obj.id] = 'Unposted'
            else:
                res[invoice_obj.id] = 'Posted'
        return res

    def _get_amount_in_words(self, cr, uid, ids, name, args, context=None):
        res = {}
        currency_pool = self.pool.get('res.currency')
        for invoice_obj in self.browse(cr, uid, ids, context=context):
            res[invoice_obj.id] = currency_pool.amount_word(cr, uid, invoice_obj.currency_id, invoice_obj.amount_total or 0.00,
                                                     context=context)
        return res
    
    _columns = {
                'unposted': fields.boolean('Unposted ?'),
                'cash_invoice': fields.boolean('Cash Invoice ?'),
                'display_bank_details': fields.boolean('Display Bank Details ?'),
                'direct_lead_id': fields.many2one('account.invoice', 'Related Lead'),
                'status': fields.function(_get_status, type="selection",
                                          selection=[('Posted', 'Posted'), ('Unposted', 'Unposted')],
                                          string="Status",
                                          store={
                                                 'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['state'], 20)
                                                 }
                                          ),
                'edit_inv': fields.boolean('Edit Invoice'),
                'amount_in_words': fields.function(_get_amount_in_words, type="char", string="Amount in Words"),
#                 'supplier_invoice_date': fields.date('Supplier Invoice Date'),
                }
    _defaults = {
                 'display_bank_details': True
                 }
    
    def invoice_print(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_print(cr, uid, ids, context=context)
        res['report_name'] = 'invoice_report_jasper'
        return res
    
    def invoice_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for invoice_id in ids:
            wf_service.trg_validate(uid, 'account.invoice', \
                                    invoice_id, 'invoice_cancel', cr)
#         self.action_cancel_draft(cr, uid, ids)
        self.write(cr, uid, ids, {'unposted': True,'edit_inv': True})
        return True
    
account_invoice()

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    _columns = {
                'cons_quo_stat_report': fields.boolean('Consider in quotation status report'),
                'liquid_damage_note': fields.text('Liquidated Damages Note'),
                }
account_analytic_account()

class account_payment_term(osv.osv):
    _inherit = 'account.payment.term'
    _columns = {
                'name': fields.char('Payment Term', size=256, required=True)
                }
account_payment_term()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

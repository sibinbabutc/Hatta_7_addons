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

import openerp.addons.decimal_precision as dp
from tools.translate import _
from datetime import datetime
from datetime import timedelta
import time
from openerp import netsvc
from openerp.tools.safe_eval import safe_eval
from openerp.tools import float_compare
from openerp import tools


class account_account(osv.osv):
    _inherit = 'account.account'
    _columns = {
                'account_analytic_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'include_subledger': fields.boolean('Include in Subledger Report')
                }
    
    def get_cost_center(self, cr, uid, account_obj, context=None):
        result = False
        if not account_obj.parent_id:
            return result
        if account_obj.account_analytic_id:
            result = account_obj.account_analytic_id
        else:
            result = self.get_cost_center(cr, uid, account_obj.parent_id, context)
        return result
    
    def name_get(self, cr, uid, ids, context = None):
        """displays account name and its corresponding currency"""
        user_pool = self.pool.get('res.users')
        res = super(account_account, self).name_get(cr, uid, ids, context = context)
        ret_value = []
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_curr = user_obj.company_id.currency_id.name
        for value in res:
            account = self.browse(cr, uid, value[0], context=context)
            if account.currency_id.name:
               ret_value.append((value[0], "%s [%s]"%(value[1], account.currency_id.name)))
            else:
                ret_value.append((value[0], "%s [%s]"%(value[1], comp_curr)))
        return ret_value
    
account_account()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def onchange_trnsaction_type(self, cr, uid, ids, transaction_type_id, context=None):
        res = {'value': {}}
        transaction_type_pool = self.pool.get('transaction.type')
        if transaction_type_id:
            transaction_type_obj = transaction_type_pool.browse(cr, uid, transaction_type_id,
                                                                context=context)
            res['value']['cost_center_id'] = transaction_type_obj.cost_center_id and \
                                                    transaction_type_obj.cost_center_id.id or False
        return res
    
    def onchange_parent_partner_id(self, cr, uid, ids, parent_partner_id, context=None):
        res = {'value': {}}
        partner_pool = self.pool.get('res.partner')
        if parent_partner_id:
            partner_obj = partner_pool.browse(cr, uid, parent_partner_id, context=context)
            invoice_partner_id = parent_partner_id
            for child in partner_obj.child_ids:
                if child.type == 'invoice':
                    invoice_partner_id = child.id
            res['value']['partner_id'] = invoice_partner_id
        return res
    
    def onchange_currency_id(self, cr, uid, ids, currency_id, context=None):
        res = {'value': {}}
        currency_pool = self.pool.get('res.currency')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_curr_obj = user_obj.company_id.currency_id
        print company_curr_obj
        if currency_id:
            currency_obj = currency_pool.browse(cr, uid, currency_id, context=context)
            rate = currency_pool._get_conversion_rate(cr, uid, currency_obj, company_curr_obj,
                                                      context=context)
            res['value']['exchange_rate'] = rate
        return res
    
    def _get_invoice_bank(self, cr, uid, ids, fields, args, context=None):
        res = {}
        bank_pool = self.pool.get('res.partner.bank')
        for invoice in self.browse(cr, uid, ids, context=context):
            currency_id = invoice.currency_id.id
            company_id = invoice.company_id.id
            company_currency_id = invoice.company_id.currency_id.id
            domain = []
            if currency_id == company_currency_id:
                domain = [('company_id', '=', company_id), ('footer', '=', True)]
            else:
                domain = [('company_id', '=', company_id), ('currency_id', '=', currency_id)]
            bank_ids = bank_pool.search(cr, uid, domain, context=context)
            if not bank_ids:
                domain = [('company_id', '=', company_id), ('footer', '=', True)]
                bank_ids = bank_pool.search(cr, uid, domain, context=context)
            res[invoice.id] = bank_ids and bank_ids[0] or False
        return res
    
    def invoice_uploaded(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, ids, {'invoice_uploaded':True}, context=context)
        return True
    
#     def post_invoice(self, cr, uid, ids, context=None):
#         for invoice in self.browse(cr, uid, ids, context=context):
#             self.write(cr, uid, ids, {'state':'open'}, context=context)
#         return True
    
    def _get_invs_condtn(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state not in ['draft', 'cancel']:
                if invoice.upload_inv == True and invoice.invoice_uploaded == False:
                    res[invoice.id] = True
                else:
                    res[invoice.id] = False
            else:
                res[invoice.id] = False
        return res
    
    def _get_post_invoice_condtn(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state == 'draft':
                if invoice.upload_inv == False:
                    res[invoice.id] = True
                else:
                    res[invoice.id] = False
            else:
                res[invoice.id] = False
        return res
    
    def _get_condtn_post_invoice(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state == 'draft':
                if invoice.upload_inv == True:
                    res[invoice.id] = True
                else:
                    res[invoice.id] = False
            else:
                res[invoice.id] = False
        return res
    
    _columns = {
                'parent_partner_id': fields.many2one('res.partner', 'Customer'),
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'sale_id': fields.many2one('sale.order', 'Sale Order'),
                'purchase_id': fields.many2one('purchase.order', 'Purchase Order'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'shop_id': fields.related('sale_id', 'shop_id', type="many2one",
                                          relation='sale.shop', string="Shop"),
                'reg_pay_invoice': fields.related('cost_center_id', 'reg_pay_invoice', type='boolean',
                                                  string='Register Payment From Invoice ?'),
                'exchange_rate': fields.float('Exchange Rate', digits=(16, 9)),
                'self_billing_num': fields.char('Self Billing Number', size=128),
                'expected_seq': fields.char('Expected Sequence', size=128),
                'cancel_note': fields.text(string="Cancellation Note"),
                'rel_picking_ids': fields.many2many('stock.picking', 'hatta_invoice_picking_rel',
                                                    'invoice_id', 'picking_id',
                                                    'Related Delivery Order'),
                'partner_bank_id': fields.function(_get_invoice_bank, type="many2one",
                                                   relation="res.partner.bank", string="Bank Account",
                                                   store={
                                                          'account.invoice': (lambda self, cr, uid, ids,
                                                                              c={}: ids,
                                                                              ['currency_id'], 20)},
                                                   readonly=True),
                'invoice_uploaded' : fields.boolean(string="Invoice Uploaded"),
                'upload_inv' : fields.related('parent_partner_id', 'upload_invoice', type="boolean", relation='res.partner', string="Related Upload Invoice"),
                'supplier_invoice_date': fields.date('Supplier Invoice Date'),
#                 'invs_condtn': fields.function(_get_invs_condtn, type="boolean", string="Condition"),
#                 'post_invoice_condtn' : fields.function(_get_post_invoice_condtn, type="boolean", string="Condition"),
#                 'condtn_post_invoice' : fields.function(_get_condtn_post_invoice, type="boolean", string="Condition"),
                }
    _defaults = {
                 'exchange_rate': 1.000
                 }
    
    def invoice_proforma2(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        show_wiz = False
        wf_service = netsvc.LocalService("workflow")
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.upload_inv and not invoice.invoice_uploaded:
                show_wiz = True
        if show_wiz:
            ctx = context.copy()
            ctx['default_validate'] = True
            ctx['default_invoice_id'] = ids[0]
            return {
                    'name': _('Invoice Upload'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'invoice.upload.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': ctx,
                    }
        for invoice_id in ids:
            wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_proforma2', cr)
        return True
    
    def assign_billing_number(self, cr, uid, invoice_id, number, context=None):
        inv_obj = self.browse(cr, uid, invoice_id, context=context)
        if inv_obj.move_id:
            lpo_no = inv_obj.sale_id and inv_obj.sale_id.client_order_ref or inv_obj.number or False
            if not lpo_no and inv_obj.type in ['in_invoice'] and inv_obj.job_id:
                lpo_list = []
                for sale in inv_obj.job_id.sale_ids:
                    lpo_list.append(sale.client_order_ref or '')
                lpo_no = ' '.join(lpo_list)
            job_name = ''
            if inv_obj.job_id:
                job_name = inv_obj.job_id.name or ''
            name = ''
            if lpo_no:
                name += "LPO#%s "%(tools.ustr(lpo_no))
            if job_name:
                name += "JOB# %s"%(tools.ustr(job_name))
            if not name:
                name = doc_no
            else:
                name += " Sales"
            new_name = name + "[" + number + "]"
            inv_obj.move_id.write({'ref': new_name})
            for move_line in inv_obj.move_id.line_id:
                if move_line.account_id.type in ['receivable', 'payable']:
                    move_line.write({'name': new_name})
        return inv_obj.write({'self_billing_num': number})
    
    def assign_number(self, cr, uid, ids, context=None):
        obj_sequence = self.pool.get('ir.sequence')
        for invoice in self.browse(cr, uid, ids, context={}):
            if not invoice.sale_id and not invoice.purchase_id:
                if invoice.transaction_type_id and invoice.transaction_type_id.sequence_id:
                    vals = {}
                    if invoice.unposted or invoice.state == 'proforma2':
                        vals['unposted'] = True
                        name = invoice.internal_number
                    else:
                        name = obj_sequence.next_by_id(cr, uid,
                                                       invoice.transaction_type_id.sequence_id.id,
                                                        context={})
                    vals['internal_number'] = name
                    invoice.write(vals)
        return True
    
    def invoice_open(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        show_wiz = False
        if not context.get('from_wizard', False):
            for invoice in self.browse(cr, uid, ids, context=context):
                if invoice.upload_inv and not invoice.invoice_uploaded:
                    show_wiz = True
        if show_wiz:
            ctx = context.copy()
            ctx['default_post'] = True
            ctx['default_invoice_id'] = ids[0]
            return {
                    'name': _('Invoice Upload'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'invoice.upload.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': ctx,
                    }
        print "Coming HEERERERER\n\n\n",ids
        self.assign_number(cr, uid, ids, context=context)
        res = super(account_invoice, self).invoice_open(cr, uid, ids, context=context)
        return res
    
    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context=context)
        res['analytic_account_id'] = x.get('analytic_account_id', False) or x.get('analytic_account_id', False)
        res['job_id'] = x.get('job_id', False)
        res['sl_cd'] = x.get('re_sl_cd', False) or x.get('sl_cd','')
        res['doc_no'] = x.get('doc_no', '')
        return res
    
    def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
        if context is None:
            context={}
        total = 0
        total_currency = 0
        cur_obj = self.pool.get('res.currency')
        for i in invoice_move_lines:
            if inv.currency_id.id != company_currency:
                context.update({'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                i['currency_id'] = inv.currency_id.id
                i['amount_currency'] = i['price']
                conv_price = cur_obj.compute(cr, uid, inv.currency_id.id,
                                             company_currency, i['price'],
                                             context=context)
                if inv.type == 'in_invoice' and inv.exchange_rate:
                    conv_price = i['price'] * inv.exchange_rate
                i['price'] = conv_price
            else:
                i['amount_currency'] = False
                i['currency_id'] = False
            i['ref'] = ref
            if inv.type in ('out_invoice','in_refund'):
                total += i['price']
                total_currency += i['amount_currency'] or i['price']
                i['price'] = - i['price']
            else:
                total -= i['price']
                total_currency -= i['amount_currency'] or i['price']
        sign = 1
        if total < 0.00:
            sign = -1
        discount = inv.discount
        if discount != 0.00:
            discount *= sign
            discount_currency = discount * inv.exchange_rate
            total -= discount_currency
            total_currency -= discount
        return total, total_currency, invoice_move_lines
    
    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        move_line_pool = self.pool.get('account.move.line')
        res = super(account_invoice, self).finalize_invoice_move_lines(cr, uid, invoice_browse, move_lines)
        new_line = []
        for line in res:
            if not line[2].get('analytic_account_id', False):
                account_id = line[2].get('account_id', False)
                account_id_change = move_line_pool.onchange_account_id(cr, uid, [], account_id,
                                                                       context={})
                line[2].update(account_id_change.get('value', {}))
            if line[2].get('amount_currency', False):
                line[2]['amount_fc_temp'] = line[2]['amount_currency'] < 0.00 and line[2]['amount_currency'] * -1.00 or \
                                                line[2]['amount_currency']
            line[2]['job_id'] = invoice_browse.job_id and invoice_browse.job_id.id or False
            new_line.append(line)
        
        return new_line
    
    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            lpo_no = inv.sale_id and inv.sale_id.client_order_ref or inv.number or False
            if not lpo_no and inv.type in ['in_invoice'] and inv.job_id:
                lpo_list = []
                for sale in inv.job_id.sale_ids:
                    lpo_list.append(sale.client_order_ref or '')
                lpo_no = ' '.join(lpo_list)
            job_no = inv.job_id and inv.job_id.name or ''
            if inv.type == 'in_invoice':
                po_name = inv.purchase_id and inv.purchase_id.name or ''
                supp_inv_number = inv.supplier_invoice_number or ''
                lpo_no = "%s / SINV #%s"%(po_name, supp_inv_number)
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
                    raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)
            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.internal_number
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.internal_number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            acc_id = inv.account_id.id
            doc_no = inv['internal_number'] or inv.number or inv['supplier_invoice_number'] or '/'
#             doc_no = inv.sale_id and inv.sale_id.name or inv.purchase_id and inv.purchase_id.name or ''
            name = ''
            if lpo_no:
                name += "LPO#%s "%(tools.ustr(lpo_no))
            if job_no:
                name += "JOB# %s"%(tools.ustr(job_no))
            if not name:
                name = doc_no
            elif inv.type == 'in_invoice':
                name += " Purchase"
            else:
                name += " Sales"
#             name = "LPO# %s JOB# %s Sales"%(str(lpo_no), str(job_no))
            totlines = False
            sl_cd = inv.partner_id.parent_id and inv.partner_id.parent_id.partner_ac_code or \
                        inv.partner_id.partner_ac_code or ''
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'analytic_account_id': inv.cost_center_id and inv.cost_center_id.id or False,
                        'ref': ref,
                        'sl_cd': sl_cd,
                        'doc_no': doc_no,
                        'job_id': inv.job_id and inv.job_id.id or False
                    })
            else:
                date_maturity = inv.date_due
                if inv.type == 'in_invoice':
                    if inv.purchase_id and inv.purchase_id.supplier_invoice_date and inv.supplier_invoice_date:
                        date_maturity = inv.supplier_invoice_date
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': date_maturity or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'analytic_account_id': inv.cost_center_id and inv.cost_center_id.id or False,
                    'ref': ref,
                    'sl_cd': sl_cd,
                    'doc_no': doc_no,
                    'job_id': inv.job_id and inv.job_id.id or False
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)
            ref = inv.reference and inv.reference or inv.number
            if inv.type in ['out_invoice', 'in_refund']:
                ref = ''
                if lpo_no:
                    ref += "LPO#%s "%(tools.ustr(lpo_no))
                if job_no:
                    ref += "JOB# %s"%(tools.ustr(job_no))
                if not ref:
                    ref = doc_no
                else:
                    ref += " Sales"
#                 ref = "LPO# %s JOB# %s Sales"%(str(lpo_no), str(job_no))
            move = {
                'ref': ref,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            print move
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True
    
    def account_invoice_cancel_paid(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for invoice_obj in self.browse(cr, uid, ids, context=context):
            invoice_obj.write({'unposted': True})
            for payments in invoice_obj.payment_ids:
                if payments.voucher_id:
                    payments.voucher_id.cancel_voucher()
                    payments.voucher_id.unlink()
            if invoice_obj.move_id:
                for line in invoice_obj.move_id.line_id:
                    reconcile_obj = line.reconcile_id or line.reconcile_partial_id or False
                    if reconcile_obj:
                        reconcile_obj.unlink()
            wf_service.trg_validate(uid, 'account.invoice', \
                                    invoice_obj.id, 'invoice_cancel', cr)
        return True
    
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res={}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = (line.price_unit * line.quantity)-line.discount
            res[line.id] = price
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
    
    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context=context)
        if line.invoice_id:
#             res['job_id'] = line.invoice_id.job_id and line.invoice_id.job_id.id or False
            res['re_sl_cd'] = line.invoice_id.job_id and line.invoice_id.job_id.name or False
        res['analytic_account_id'] = line.invoice_id.cost_center_id and line.invoice_id.cost_center_id.id or \
                                            False
        return res
    
    _columns = {
        'discount': fields.float('Discount', digits_compute= dp.get_precision('Discount')),
        'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
            digits_compute= dp.get_precision('Account'), store=True),
        'lpo_ids' : fields.one2many('local.purchase.order', 'invoice_line_id', 'Local Purchase Order')
            }
    
account_invoice_line()

class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
                'display_check_details': fields.boolean('Display Check Number ?'),
                'display_mapping_partner': fields.boolean('Display mapping partner/Account ?'),
                'display_bank_details': fields.boolean('Display Bank Details ?'),
                'display_check_type_date': fields.boolean('Display Check Type & Date'),
                'voucher_no_as_ref': fields.boolean('Line Ref as voucher number ?'),
                'display_invoice_details': fields.boolean('Display Supplier Invoice Detail?'),
                'check_cheque_number': fields.boolean('Check Cheque Number'),
                'show_crd': fields.boolean('Filter Supplier ?'),
                'show_deb': fields.boolean('Filter Customer ?'),
#                 'default_credit_amount': fields.boolean('Credit/Debit Party Acc By Default'),
#                 'default_credit_journal': fields.boolean('Credit Journal Acc By Default'),
#                 'default_debit_journal': fields.boolean('Debit Journal Acc By Default'),
                'voucher_label': fields.char('Voucher Label', size=128),
                'display_in_voucher': fields.boolean('Display in Vouchers'),
                'credit_journal_acc': fields.boolean('Credit Journal A/C'),
                'debit_journal_acc': fields.boolean('Debit Journal A/C'),
                'credit_partner_acc': fields.boolean('Credit Partner A/C'),
                'debit_partner_acc': fields.boolean('Debit Partner A/C'),
                'credit_gl_acc': fields.boolean('Credit GL A/C'),
                'debit_gl_acc': fields.boolean('Debit GL A/C'),
                'credit_bank_acc': fields.boolean('Credit Bank A/C'),
                'debit_bank_acc': fields.boolean('Debit Bank A/C'),
                'display_amount': fields.boolean('Display Amount?'),
                'seq_period': fields.boolean('Sequence based on period'),
                'man_seq': fields.char('Manual Period Seq', size=128),
                'check_voucher' : fields.boolean('Check Voucher'),
                'diplay_tr_details': fields.boolean('Display TR Details')
                }
    _defaults = {
                 'display_amount': True
                 }
    
    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone

        @return: Returns a list of tupples containing id, name
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            name = "%s" % (rs.name)
            res += [(rs.id, name)]
        return res
    
account_journal()

class account_move(osv.osv):
    _inherit = 'account.move'
    
    def onchange_amount(self, cr, uid, ids, cheque_amt, line_id, context=None):
        res={'value': {}}
        new_line = []
        move_line_pool = self.pool.get('account.move.line')
        for line in line_id:
            if line[0] == 0:
                line_data = line[2]
                if line_data.get('credit_line', False):
                    line_data['credit'] = cheque_amt
                elif line_data.get('debit_line', False):
                    line_data['debit'] = cheque_amt
                new_line.append((0, 0, line_data))
            elif line[0] == 1:
                line_id = line[1]
                line_obj = move_line_pool.browse(cr, uid, line_id, context=context)
                line_data = line[2]
                if line_data.get('credit_line', False) or line_obj.credit_line:
                    line_data['credit'] = cheque_amt
                if line_data.get('debit_line', False) or line_obj.debit_line:
                    line_data['debit'] = cheque_amt
                new_line.append((1, line_id, line_data))
            elif line[0] == 4:
                line_id = line[1]
                line_obj = move_line_pool.browse(cr, uid, line_id, context=context)
                line_data = {}
                if line_obj.credit_line:
                    line_data['credit'] = cheque_amt
                if line_obj.debit_line:
                    line_data['debit'] = cheque_amt
                if line_data:
                    new_line.append((1, line_id, line_data))
                else:
                    new_line.append(line)
            else:
                new_line.append(line)
        res['value']['line_id'] = new_line
        return res
    
    def onchange_chq_amount(self, cr, uid, ids, journal_id, cheque_amt, journal_partner_id, emp_partner_id,
                            bank_account_id, line_id, ref, date, part_type, gl_account_id,
                            cheque_type, context=None):
        if context is None:
            context = {}
        journal_pool = self.pool.get('account.journal')
        partner_pool = self.pool.get('res.partner')
        account_pool = self.pool.get('account.account')
        move_line_pool = self.pool.get('account.move.line')
        icp = self.pool.get('ir.config_parameter')
        res = {'value': {}}
        new_line = []
        if not journal_id:
            return res
        journal_obj = journal_pool.browse(cr, uid, journal_id, context=context)
        credit = False
        debit = False
        account_id = False
        partner_id = False
        if part_type == 'empl':
            partner_id = emp_partner_id
        if context.get('journal_change', False):
            domain = [('is_manufac', '=', False)]
            display_check_details = journal_obj.display_check_details or False
            display_bank_details = journal_obj.display_bank_details or False
            display_check_type_date = journal_obj.display_check_type_date or False
            display_amount = journal_obj.display_amount or False
            display_invoice_details = journal_obj.display_invoice_details or False
            display_mapping_partner = journal_obj.display_mapping_partner or False
            display_tr_details = journal_obj.diplay_tr_details or False
            
            if not display_check_type_date:
                res['value']['cheque_type'] = False
                res['value']['cheque_date'] = False
            if not display_check_details:
                res['value']['cheque_no'] = False
            if not display_bank_details:
                res['value']['bank_details'] = False
                res['value']['bank_account_id'] = False
            if not display_amount:
                res['value']['cheque_amt'] = False
            
            res['value']['display_check_details'] = display_check_details
            res['value']['display_bank_details'] = display_bank_details
            res['value']['display_check_type_date'] = display_check_type_date
            res['value']['display_amount'] = display_amount
            res['value']['display_invoice_details'] = display_invoice_details
            res['value']['display_mapping_partner'] = display_mapping_partner
            res['value']['diplay_tr_details'] = display_tr_details
            if not display_check_details:
                res['value']['cheque_no'] = 'CASH'
            if journal_obj.show_crd or journal_obj.show_deb:
                domain = []
            if journal_obj.show_crd:
                domain.append(('supplier', '=', True))
            if journal_obj.show_deb:
                if domain:
                    domain.insert(0, '|')
                domain.append(('customer', '=', True))
            if domain:
                res['domain'] = {
                                 'journal_partner_id': domain
                                 }
            if journal_obj.credit_journal_acc and journal_obj.default_credit_account_id:
                account_id = journal_obj.default_credit_account_id.id
                credit = True
                debit = False
            if journal_obj.debit_journal_acc and journal_obj.default_debit_account_id:
                account_id = journal_obj.default_debit_account_id.id
                credit = False
                debit = True
        if context.get('gl_change', False):
            if gl_account_id and journal_obj.credit_gl_acc:
                account_id = gl_account_id
                credit = True
                debit = False
            if gl_account_id and journal_obj.debit_gl_acc:
                account_id = gl_account_id
                credit = False
                debit = True
        partner_change = False
        if context.get('partner_change', False):
            partner_change = True
            if journal_partner_id:
                partner_obj = partner_pool.browse(cr, uid, journal_partner_id, context=context)
                temp_account_id = partner_obj.property_account_receivable and \
                                        partner_obj.property_account_receivable.id or False
                if partner_obj.supplier:
                    temp_account_id = partner_obj.property_account_payable and \
                                             partner_obj.property_account_payable.id or False
            if journal_partner_id and journal_obj.debit_partner_acc:
                account_id = temp_account_id
                debit = True
                credit = False
                partner_id = journal_partner_id
            if journal_partner_id and journal_obj.credit_partner_acc:
                account_id = temp_account_id
                debit = False
                credit = True
                partner_id = journal_partner_id
        if context.get('bank_ac_change', False):
            if (bank_account_id or cheque_type) and journal_obj.credit_bank_acc:
                account_id = bank_account_id
                if cheque_type == 'pdc':
                    account_id = safe_eval(icp.get_param(cr, uid,
                                                         'hatta_account.pdc_issue_account', 'False'))
                credit = True
                debit = False
            if (bank_account_id or cheque_type) and journal_obj.debit_bank_acc:
                account_id = bank_account_id
                if cheque_type == 'pdc':
                    account_id = safe_eval(icp.get_param(cr, uid,
                                                         'hatta_account.pdc_rec_account', 'False'))
                credit = False
                debit = True
        if account_id and (debit or credit):
            hit = False
            onchange_account_data = move_line_pool.onchange_account_id(cr, uid, ids, account_id, context=context)
            onchange_data = onchange_account_data.get('value', {})
            for line in line_id:
                if line[0] == 0:
                    line_data = line[2]
                    if credit and line_data.get('credit_line', False):
                        hit = True
                        line_data['account_id'] = account_id
                        line_data['partner_id'] = partner_id
                        line_data.update(onchange_data)
                    if debit and line_data.get('debit_line', False):
                        hit = True
                        line_data['account_id'] = account_id
                        line_data['partner_id'] = partner_id
                        line_data.update(onchange_data)
                    if partner_change:
                        line_data['voucher_id'] = False
                    line[2] = line_data
                    new_line.append((0, 0, line_data))
                elif line[0] == 1:
                    line_data = line[2]
                    move_line_id = line[1]
                    move_line_obj = move_line_pool.browse(cr, uid, move_line_id, context=context)
                    if credit and (line_data.get('credit_line', False) or move_line_obj.credit_line):
                        hit = True
                        line_data['account_id'] = account_id
                        line_data['partner_id'] = partner_id
                        line_data.update(onchange_data)
                    if debit and (line_data.get('debit_line', False) or move_line_obj.debit_line):
                        hit = True
                        line_data['account_id'] = account_id
                        line_data['partner_id'] = partner_id
                        line_data.update(onchange_data)
                    if partner_change:
                        line_data['voucher_id'] = False
                    new_line.append((1, move_line_id, line_data))
                elif line[0] == 4:
                    move_line_id = line[1]
                    move_line_obj = move_line_pool.browse(cr, uid, move_line_id, context=context)
                    line_data = {}
                    if credit and move_line_obj.credit_line:
                        hit = True
                        line_data['account_id'] = account_id
                        line_data['partner_id'] = partner_id
                        line_data.update(onchange_data)
                    if debit and move_line_obj.debit_line:
                        hit = True
                        line_data['account_id'] = account_id
                        line_data['partner_id'] = partner_id
                        line_data.update(onchange_data)
                    if partner_change:
                        line_data['voucher_id'] = False
                    new_line.append((1, move_line_id, line_data))
                else:
                    new_line.append(line)
            if not hit:
                vals = {
                        'account_id': account_id,
                        'partner_id': partner_id,
                        'name': ref,
                        'debit': debit and cheque_amt or 0.00,
                        'credit': credit and cheque_amt or 0.00,
                        'credit_line': credit,
                        'debit_line': debit
                        }
                vals.update(onchange_data)
                new_line.append((0, 0, vals))
        if new_line:
            res['value']['line_id'] = new_line
#         for line in line_id:
#                 if 
        return res

    
    def onchange_ref(self, cr, uid, ids, ref, line_id, context=None):
        res = {'value': {}}
        new_line = []
        for line in line_id:
            if line[0] == 0:
                data = line[2]
                data['name'] = ref
                new_line.append((0, 0, data))
            elif line[0] == 4:
                id = line[1]
                new_line.append((1, id, {'name': ref}))
            elif line[0] == 1:
                data = line[2]
                data.update({'name': ref})
                new_line.append((1, line[1], data))
            res['value']['line_id'] = new_line
        return res
    
    def onchange_date(self, cr, uid, ids, date, context=None):
        res = {'value': {'period_id': False}}
        period_pool = self.pool.get('account.period')
        if date:
            res['value']['cheque_date'] = date
            try:
                fiscalyear_ids = period_pool.find(cr, uid, date, context=context)
                if fiscalyear_ids:
                    fiscalyear_obj = period_pool.browse(cr, uid, fiscalyear_ids[0], context=context)
                    if fiscalyear_obj.state == 'done':
                        warning = {
                                   'title': _('Error !!'),
                                   'message': _('Period Closed for this date: %s.'%(tools.ustr(date)))
                                   }
                        res['warning'] = warning
                    else:
                        res['value']['period_id'] = fiscalyear_ids[0]
            except:
                warning = {
                           'title': _('Error !!'),
                           'message': _('There is no period defined for this date: %s.\nPlease create one.'%(tools.ustr(date)))
                           }
                res['warning'] = warning
        return res
    
    def onchange_cheque_date(self, cr, uid, ids, date, context=None):
        res = {'value': {}}
        if date:
            today = datetime.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")
            date = datetime.strptime(date, "%Y-%m-%d")
            if date <= today:
                res['value']['cheque_type'] = 'curr'
            elif date > today:
                res['value']['cheque_type'] = 'pdc'
        return res
    
    def onchange_invoice(self, cr, uid, ids, invoice_id, context=None):
        invoice_pool = self.pool.get('account.invoice')
        res = {'value': {'invoice_date': False, 'lpo_no': ''}}
        if invoice_id:
            invoice_obj = invoice_pool.browse(cr, uid, invoice_id, context=context)
            res['value']['invoice_date'] = invoice_obj.date_invoice
            res['value']['lpo_no'] = invoice_obj.supplier_invoice_number
        return res
    
    def action_check_cleared(self, cr, uid, ids, context=None):
        if ids:
            self.write(cr, uid, ids, {'check_cleared' : True}, context=context)
        return True 
    
    def _check_debit_credit(self, cr, uid, ids, context=None):
        """checks whether debit or credit field is filled"""
        account_obj = self.browse(cr, uid, ids, context = context)
        for account in account_obj:
            if account.skip_check:
                return True
            if not account.journal_id.display_in_voucher:
                return True
            if account.line_id:
                for line in account.line_id:
                    if line.debit == 0.00 and line.credit == 0.00:
                        return False   
        return True
    
    def _check_name(self, cr, uid, ids, context=None):
        for move_obj in self.browse(cr, uid, ids, context=context):
            if move_obj.skip_check:
                return True
            move_ids = self.search(cr, uid, [('name', '=', move_obj.name),
                                             ('id', '!=', move_obj.id),
                                             ('skip_check', '=', False)], context=context)
            if move_ids:
                return False
        return True
    
    def _check_check_number(self, cr, uid, ids, context=None):
        for move_obj in self.browse(cr, uid, ids, context=context):
            if move_obj.cheque_no and move_obj.journal_id.check_cheque_number:
                bank_id = move_obj.bank_account_id and move_obj.bank_account_id.id or False
                move_ids = self.search(cr, uid, [('cheque_no', '=', move_obj.cheque_no),
                                                 ('bank_account_id', '=', bank_id),
                                                 ('id', '!=', move_obj.id)],
                                       context=context)
                if move_ids:
                    return False
        return True
    
    def get_comp_account(self, cr, uid, ids, context=None):
        user_pool = self.pool.get('res.users')
        account_ids = []
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for bank_obj in user_obj.company_id.bank_ids:
            if bank_obj.journal_id:
                default_debit_account = bank_obj.journal_id.default_debit_account_id and \
                                            bank_obj.journal_id.default_debit_account_id.id or False
                if default_debit_account:
                    account_ids.append(default_debit_account)
                default_credit_account = bank_obj.journal_id.default_credit_account_id and \
                                            bank_obj.journal_id.default_credit_account_id.id or False
                if default_credit_account:
                    account_ids.append(default_credit_account)
        account_ids = list(set(account_ids))
        return account_ids
    
    def _get_checking_status(self, cr, uid, ids, fields, args, context=None):
        res = {}
        company_account_ids = self.get_comp_account(cr, uid, ids, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            has_bank_account = False
            for move_line in move.line_id:
                if move_line.account_id.id in company_account_ids:
                    has_bank_account = True
                    break
            if has_bank_account:
                res[move.id] = True
            else:
                res[move.id] = False
        return res
    
    def _get_line_move_ids(self, cr, uid, ids, context=None):
        move_line_pool = self.pool.get('account.move.line')
        move_ids = []
        for move_line_obj in move_line_pool.browse(cr, uid, ids, context=context):
            move_ids.append(move_line_obj.move_id.id)
        return move_ids
    
    def _get_se_integer(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            name = move.name or ''
            name_float = ''
            seq_obj = move.journal_id.sequence_id and move.journal_id.sequence_id or False
            if move.journal_id.display_in_voucher and seq_obj:
                seq_prefix = seq_obj.prefix or ''
                seq_sufix = seq_obj.suffix or ''
                name = name.replace(seq_prefix, '')
                name = name.replace(seq_sufix, '')
            try:
                name_float = float(name)
            except:
                name_float = 0.00
            res[move.id] = name_float
        return res
    
    _columns = {
                'display_check_details': fields.boolean('Display Check Details ?'),
                'display_mapping_partner': fields.boolean('Display mapping partner/Account ?'),
                'display_bank_details': fields.boolean('Display Bank Details ?'),
                'display_check_type_date': fields.boolean('Display Check Type & Date'),
                'display_amount': fields.boolean('Display Amount?'),
                'display_invoice_details': fields.boolean('Display Invoice Detail?'),
                'diplay_tr_details': fields.boolean('Display TR Details'),
                'cheque_no': fields.char('Cheque No', size=128),
                'cheque_type': fields.selection([('curr', 'Current Dated'), ('pdc', 'Post Dated')],
                                                'Cheque Type'),
                'cheque_date': fields.date('Date'),
                'bank_details': fields.char('Bank Details', size=128),
                'journal_partner_id': fields.many2one('res.partner', 'Partner'),
                'journal_employee_part_id': fields.many2one('res.partner', 'Employee',
                                                            domain="[('is_employee', '=', True)]"),
                'partner_name': fields.char('Payee Name', size=128),
                'bank_account_id': fields.many2one('account.account', 'Bank A/c'),
                'cheque_amt': fields.float('Chq.Amt', digits_compute=dp.get_precision('Account')),
                'part_type': fields.selection([('party', 'Partner'), ('gl', 'GL Account'),
                                               ('empl', 'Employee')], 'Type'),
                'gl_account_id': fields.many2one('account.account', 'GL Account'),
                'create_uid': fields.many2one('res.users', 'Created User'),
                'write_uid': fields.many2one('res.users', 'Created User'),
                'write_date': fields.datetime('Write Date'),
                'create_date': fields.datetime('Create Date'),
                'ref': fields.char('Narration', size=512),
                'release_date': fields.date('Release Date'),
                'cheque_released': fields.boolean('Check Released'),
                'bounced': fields.boolean('Cheque Bounced'),
                'invoice_id': fields.many2one('account.invoice', 'Invoice No'),
                'invoice_date': fields.date('Date'),
                'lpo_no': fields.char('LPO. No', size=128),
                'skip_check': fields.boolean('Skip Check'),
                'check_cleared' : fields.boolean('Check Cleared'),
                'include_for_checking': fields.function(_get_checking_status, type="boolean",
                                                        string="Include for checking", store={
                                                'account.move.line': (_get_line_move_ids, ['account_id'], 10), 
                                                'account.move': (lambda self, cr, uid, ids, ctx: ids, ['check_cleared'], 10),
                                                }),
                'int_seq': fields.function(_get_se_integer, type="float", string="Integer Seq"),
                'is_a_tr': fields.boolean('Is a TR ?'),
                'tr_type': fields.selection([('new', 'New'), ('settle', 'Settlement')],
                                            'TR Type'),
                'tr_id': fields.many2one('tr.details', 'Settlement Against'),
                'tr_no': fields.char('Tr #', size=128),
                'tr_date': fields.date('TR Date'),
                'tr_duration': fields.float('Credit Days'),
                'interest_rate': fields.float('Interest Rate'),
                }
    _defaults = {
                 'cheque_type': 'curr',
                 'part_type': 'party',
                 'cheque_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'tr_id': False
                 }
    _sql_constraints = [
        ('name_unique', 'Check(1=1)', 'Voucher Number Should be unique!!!'),
    ]
    _constraints = [
        (_check_name, 'Voucher Number should be unique!!!', ['name']),
        (_check_check_number, 'Check Number Should be Unique !!!', ['cheque_no']),
        (_check_debit_credit, 'Either debit or credit field in Journal Items should be filled', ['line_id'])
    ]
    
    def button_dummy(self, cr, uid, ids, context=None):
        voucher_pool = self.pool.get('account.voucher')
        for move in self.browse(cr, uid, ids, context=context):
            if move.state == 'draft':
                for line in move.line_id:
                    if line.voucher_id:
                        voucher_pool.unlink(cr, uid, [line.voucher_id.id], context=context)
        return True
    
    def copy(self, cr, uid, id, default=None, context=None):
        default['create_tr_id'] = False
        default['tr_id'] = False
        res = super(account_move, self).copy(cr, uid, id, default, context=context)
        move_obj = self.browse(cr, uid, id, context=context)
        self.write(cr, uid, [res], {'ref': move_obj.ref or ''}, context=context)
        return res
    
    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        valid_moves = self.validate(cr, uid, ids, context)

        if not valid_moves:
            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name =='/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.internal_number:
                    new_name = invoice.internal_number
                elif not move.journal_id.display_in_voucher:
                    if journal.sequence_id:
                        c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                        new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                    else:
                        raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))

                if new_name:
                    self.write(cr, uid, [move.id], {'name':new_name})

        cr.execute('UPDATE account_move '\
                   'SET state=%s '\
                   'WHERE id IN %s',
                   ('posted', tuple(valid_moves),))
        return True
    
    def create(self, cr, uid, vals, context=None):
        """creates the unique sequence number for journal_id"""
        if context is None:
            context = {}
        journal_pool = self.pool.get('account.journal')
        period_pool = self.pool.get('account.period')
        obj_sequence = self.pool.get('ir.sequence')
        move_line_pool = self.pool.get('account.move.line')
        if vals.get('journal_id', False):
            journal = journal_pool.browse(cr, uid, vals['journal_id'], context=context)
            
        if vals.get('journal_id', False) and not context.get('invoice', False):
            if not journal.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))
            elif not vals.get('name', False):
                vals['name'] = '\\'
        res = super(account_move, self).create(cr, uid, vals, context=context)
        move_obj = self.browse(cr, uid, res, context=context)
        if move_obj.state != 'posted' and move_obj.skip_check:
            tmp = self.validate(cr, uid, [res], context)
            if tmp:
                self.button_validate(cr,uid, [res], context)
        if vals.get('journal_id', False) and journal.seq_period and journal.sequence_id and \
                    vals.get('date', False) and vals.get('period_id', False):
            seq = journal.sequence_id.prefix
            if journal.man_seq:
                name = seq + journal.man_seq
                journal.write({'man_seq': ''})
            else:
                date = vals.get('date', False)
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                year = date_obj.strftime('%y')
                month = '{:02d}'.format(date_obj.month)
                exist_move_ids = self.search(cr, uid, [('journal_id', '=', journal.id),
                                                       ('period_id', '=', vals['period_id']),
                                                       ('skip_check', '=', False)])
                move_line_len = '{:02d}'.format(len(exist_move_ids))
                name = "%s%s%s%s"%(tools.ustr(seq), tools.ustr(move_line_len), tools.ustr(month), tools.ustr(year))
            self.write(cr, uid, [res], {'name' : name}, context=context)
        elif vals.get('journal_id', False) and journal.display_in_voucher and \
                        journal.sequence_id and not vals.get('skip_check', False) and \
                        not journal.seq_period:
            if vals.get('period_id', False):
                period_obj = period_pool.browse(cr, uid, vals['period_id'], context=context)
                c = {'fiscalyear_id': period_obj.fiscalyear_id.id}
                new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                self.write(cr, uid, [res], {'name' : new_name}, context=context)
        elif not vals.get('skip_check', False):
            new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, context=context)
            self.write(cr, uid, [res], {'name' : new_name}, context=context)
        return res
    
    def get_tr_from_account(self, cr, uid, account_id, context=None):
        tr_id = False
        tr_model_pool = self.pool.get('tr.model')
        if account_id:
            tr_ids = tr_model_pool.search(cr, uid, [('account_id', '=', account_id)],
                                          context=context)
        return tr_ids and tr_ids[0] or False
    
    def button_validate(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        tr_pool = self.pool.get('tr.details')
        for move_obj in self.browse(cr, uid, ids, context=context):
            tr_list = []
            for line in move_obj.line_id:
                account_id = line.account_id.id
                if move_obj.is_a_tr and move_obj.tr_type == 'new':
                    balance = abs(line.debit - line.credit)
                    tr_id = self.get_tr_from_account(cr, uid, account_id, context=context)
                    if tr_id:
                        tr_list.append({'tr_id': tr_id, 'amount': balance})
                line_balance = line.debit - line.credit
                if line.currency_id and line.amount_fc_temp != 0.00:
                    if line_balance < 0.00:
                        line.write({'amount_currency': line.amount_fc_temp * -1.00})
                    else:
                        line.write({'amount_currency': line.amount_fc_temp})
                else:
                    line.write({'amount_currency': 0.00})
            
#             if move_obj.tr_id and move_obj.tr_id.state != 'cancel':
#                 raise osv.except_osv(_("Error!!"),
#                                      _("There is a related TR. Please cancel it before proceeding!!!"))
            if move_obj.is_a_tr and move_obj.tr_type != 'settle':
                if not tr_list:
                    raise osv.except_osv(_("Error!!!"),
                                         _("Invalid TR configuration!!!"))
                for tr in tr_list:
                    tr_vals = {
                               'name': move_obj.tr_no,
                               'amount': tr.get('amount', 0.00),
                               'duration': move_obj.tr_duration,
                               'interest_rate': move_obj.interest_rate,
                               'voucher_id': move_obj.id,
                               'start_date': move_obj.tr_date,
                               'notify_before': 7.00,
                               'tr_model_id': tr.get('tr_id', 0.00),
                               'note': move_obj.ref
                               }
                    onchange_date_data = tr_pool.onchange_start_date(cr, uid, [], move_obj.tr_date,
                                                                     move_obj.tr_duration)
                    tr_vals.update(onchange_date_data.get('value', {}))
                    tr_id = tr_pool.create(cr, uid, tr_vals, context=context)
                    tr_pool.action_confirm(cr, uid, [tr_id], context=context)
            elif move_obj.is_a_tr and move_obj.tr_type == 'settle' and move_obj.tr_id:
                tr_account_id = move_obj.tr_id.tr_model_id.account_id.id
                amount = 0.00
                for line in move_obj.line_id:
                    if line.account_id.id == tr_account_id:
                        amount += abs(line.debit - line.credit)
                if amount == 0.00:
                    raise osv.except_osv(_("Error!!!"),
                                         _("Invalid settlement!!!"))
                settle_details_wizard = self.pool.get('settle.tr.wizard')
                tr_id = move_obj.tr_id.id
                settle_vals = {
                           'date': move_obj.date,
                           'amount': amount,
                           'name': move_obj.ref or '',
                           'voucher_id': move_obj.id,
                           'tr_id': tr_id
                           }
                wizard_id = settle_details_wizard.create(cr, uid, settle_vals, context=context)
                settle_details_wizard.settle_tr(cr, uid, [wizard_id], context=context)
#                 move_obj.tr_id.action_settle()
#        res = super(account_move, self).button_validate(cr, uid, ids, context=context)
        for move_obj in self.browse(cr, uid, ids, context=context):
            if move_obj.is_a_tr and move_obj.tr_type == 'settle' and move_obj.tr_id:
                tr_obj = tr_pool.browse(cr, uid, tr_id, context=context)
                if tr_obj and tr_obj.state not in ['settle'] and tr_obj.amount_total >= tr_obj.amount:
                    tr_obj.action_settle()
                
        for move_obj in self.browse(cr, uid, ids, context=context):
            move_name = move_obj.name or ''
            for line in move_obj.line_id:
                if not line.doc_no:
                    ref_name = move_name
                    if line.man_ref:
                        ref_name = line.man_ref
                    line.write({'doc_no': ref_name})
                if line.voucher_id:
                    for vou_line in line.voucher_id.line_cr_ids:
                        if vou_line == line.id:
                            move_line_bal = abs(line.debit - line.credit)
                            vou_line.write({'amount': move_line_bal})
                            if move_line_bal == vou_line.amount_unreconciled:
                                vou_line.write({'reconcile': True})
                    for vou_line in line.voucher_id.line_dr_ids:
                        if vou_line == line.id:
                            move_line_bal = abs(line.debit - line.credit)
                            vou_line.write({'amount': move_line_bal})
                            if move_line_bal == vou_line.amount_unreconciled:
                                vou_line.write({'reconcile': True})
        for move_obj in self.browse(cr, uid, ids, context=context):
            for line in move_obj.line_id:
                if line.voucher_id:
                    if line.voucher_id.writeoff_amount < 0.00:
                        raise osv.except_osv(_("Error!!!"),
                                             _("Invalid matching detected !!!!"))
                    if line.voucher_id.state == 'cancel':
                        line.voucher_id.action_cancel_draft()
                    line.voucher_id.write({'exist_move_line_id': line.id})
                    line.voucher_id.write({'active': True})
                    wf_service.trg_validate(uid, 'account.voucher', \
                                            line.voucher_id.id, 'proforma_voucher', cr)
        res = super(account_move, self).button_validate(cr, uid, ids, context=context)
	return res
    
    def button_cancel(self, cr, uid, ids, context=None):
        tr_pool = self.pool.get('tr.details')
        settle_details_pool = self.pool.get('tr.settle.details')
        tr_ids = tr_pool.search(cr, uid, ['|', ('voucher_id', 'in', ids),
#                                           ('settle_voucher_id', 'in', ids),
                                          ('state', '!=', 'cancel')], context=context)
        
        for move_obj in self.browse(cr, uid, ids, context=context):
            if tr_ids and move_obj.is_a_tr and move_obj.tr_type != 'settle':
                raise osv.except_osv(_("Error!!"),
                                     _("Related TR created for record. Please cancel it first!!!"))
        res = super(account_move, self).button_cancel(cr, uid, ids, context=context)
        settle_tr_ids = settle_details_pool.search(cr, uid, [('settle_voucher_id', 'in', ids)], context=context)
        if settle_tr_ids:
            for settle_obj in settle_details_pool.browse(cr, uid, settle_tr_ids, context=context):
                amount_total = self.pool.get('tr.details')._amount_all(cr, uid,[settle_obj.tr_details_id.id], ['amount_all'], None, context=context)[settle_obj.tr_details_id.id]
                agrred_amount = amount_total and amount_total.get('amount_total',False)
                if settle_obj.tr_details_id.state in ['settle','close']:
                    if agrred_amount < settle_obj.tr_details_id.amount:
                        settle_obj.tr_details_id.write({'state': 'open'})
        
        for move_obj in self.browse(cr, uid, ids, context=context):
            for line in move_obj.line_id:
                if line.voucher_id:
                    line.voucher_id.cancel_voucher()
                    line.write({'voucher_id': False}) 
        return res
    
    def cheque_release(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        icp = self.pool.get('ir.config_parameter')
        pdc_journal = safe_eval(icp.get_param(cr, uid,'hatta_account.pdc_journal_id', 'False'))
        pdc_receive_id = safe_eval(icp.get_param(cr, uid,'hatta_account.pdc_rec_account', 'False'))
        pdc_issue_id = safe_eval(icp.get_param(cr, uid,'hatta_account.pdc_issue_account', 'False'))
        for mov in self.browse(cr, uid, ids,context=context):
            period_ids = self.pool.get('account.period').find(cr, uid, mov.release_date, context=context)
            period_id = period_ids and period_ids[0] or False
            if not mov.release_date:
                raise osv.except_osv(_("Error!!"),
                                     _("Please set a release date!!!"))
            if not pdc_journal or not pdc_receive_id or not pdc_issue_id:
                raise osv.except_osv(_("Error!!!"),
                                     _("Please configure account details!!!"))
            move_id = self.copy(cr, uid, mov.id,default={'line_id':[],
                                                         'date': mov.release_date,
                                                         'period_id':period_id or mov.period_id or False,
                                                         'cheque_date':mov.release_date,
                                                         'journal_id': pdc_journal,
                                                         'cheque_type':'curr'},context=context)
            if mov.journal_partner_id and  mov.journal_partner_id.customer:
                debit_line_vals = {
                             'account_id':  mov.bank_account_id and mov.bank_account_id.id or False,
                             'partner_id': mov.journal_partner_id and  mov.journal_partner_id.id or False,
                             'debit': mov.cheque_amt or 0.00,
                             'credit':0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
                credit_line_vals = {
                             'account_id': pdc_receive_id or False,
                             'partner_id': False,
                             'debit': 0.00,
                             'credit':mov.cheque_amt or 0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
            if mov.journal_partner_id and  mov.journal_partner_id.supplier:
                debit_line_vals = {
                             'account_id':  mov.bank_account_id and mov.bank_account_id.id or False,
                             'partner_id': mov.journal_partner_id and  mov.journal_partner_id.id or False,
                             'debit': 0.00,
                             'credit': mov.cheque_amt or 0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
                credit_line_vals = {
                             'account_id': pdc_issue_id or False,
                             'partner_id': False,
                             'debit': mov.cheque_amt or 0.00,
                             'credit': 0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
            self.pool.get('account.move.line').create(cr, uid,debit_line_vals,context=context)
            self.pool.get('account.move.line').create(cr, uid,credit_line_vals,context=context)
            self.write(cr, uid, [mov.id], {'cheque_released':True},context=context)
            self.button_validate(cr, uid, [move_id], context=context)
                
        return True
    
    def cheque_bounce(self,cr,uid,ids,context=None):
        if context is None:
            context={}
        icp = self.pool.get('ir.config_parameter')
        pdc_journal = safe_eval(icp.get_param(cr, uid,'hatta_account.pdc_journal_id', 'False'))
        pdc_receive_id = safe_eval(icp.get_param(cr, uid,'hatta_account.pdc_rec_account', 'False'))
        pdc_issue_id = safe_eval(icp.get_param(cr, uid,'hatta_account.pdc_issue_account', 'False'))
        for mov in self.browse(cr, uid, ids,context=context):
            period_ids = self.pool.get('account.period').find(cr, uid, mov.release_date, context=context)
            period_id = period_ids and period_ids[0] or False
            move_id = self.copy(cr, uid, mov.id,default={'line_id':[],
                                                         'period_id':period_id or mov.period_id or False,
                                                         'cheque_date':mov.release_date,
                                                         'journal_id': pdc_journal,
                                                         'cheque_type':'curr'},context=context)
            if not mov.cheque_released:
                if mov.journal_partner_id and  mov.journal_partner_id.customer:
                    debit_line_vals = {
                             'account_id':  mov.journal_partner_id and mov.journal_partner_id.property_account_receivable and mov.journal_partner_id.property_account_receivable.id or False,
                             'partner_id': mov.journal_partner_id and  mov.journal_partner_id.id or False,
                             'debit': mov.cheque_amt or 0.00,
                             'credit':0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
                    credit_line_vals = {
                                 'account_id': pdc_receive_id or False,
                                 'partner_id': False,
                                 'debit': 0.00,
                                 'credit':mov.cheque_amt or 0.00,
                                 'move_id':move_id,
                                 'name': mov.ref
                                 }
                if mov.journal_partner_id and  mov.journal_partner_id.supplier:
                    debit_line_vals = {
                             'account_id':  pdc_issue_id or False,
                             'partner_id': False,
                             'debit': mov.cheque_amt or 0.00,
                             'credit':0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
                    credit_line_vals = {
                                 'account_id': mov.journal_partner_id and mov.journal_partner_id.property_account_payable and  mov.journal_partner_id.property_account_payable.id or False,
                                 'partner_id': mov.journal_partner_id and  mov.journal_partner_id.id or False,
                                 'debit': 0.00,
                                 'credit':mov.cheque_amt or 0.00,
                                 'move_id':move_id,
                                 'name': mov.ref
                                 }
            if mov.cheque_released:
                if mov.journal_partner_id and  mov.journal_partner_id.customer:
                    debit_line_vals = {
                             'account_id':  mov.journal_partner_id and mov.journal_partner_id.property_account_receivable and mov.journal_partner_id.property_account_receivable.id or False,
                             'partner_id': mov.journal_partner_id and  mov.journal_partner_id.id or False,
                             'debit': mov.cheque_amt or 0.00,
                             'credit':0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
                    credit_line_vals = {
                                 'account_id': mov.bank_account_id and mov.bank_account_id.id or False,
                                 'partner_id': False,
                                 'debit': 0.00,
                                 'credit':mov.cheque_amt or 0.00,
                                 'move_id':move_id,
                                 'name': mov.ref
                                 }
                if mov.journal_partner_id and  mov.journal_partner_id.supplier:
                    debit_line_vals = {
                             'account_id':  mov.bank_account_id and mov.bank_account_id.id or False,
                             'partner_id': False,
                             'debit': mov.cheque_amt or 0.00,
                             'credit':0.00,
                             'move_id':move_id,
                             'name': mov.ref
                             }
                    credit_line_vals = {
                                 'account_id': mov.journal_partner_id and mov.journal_partner_id.property_account_payable and  mov.journal_partner_id.property_account_payable.id or False,
                                 'partner_id': mov.journal_partner_id and  mov.journal_partner_id.id or False,
                                 'debit': 0.00,
                                 'credit':mov.cheque_amt or 0.00,
                                 'move_id':move_id,
                                 'name': mov.ref
                                 }
            self.pool.get('account.move.line').create(cr, uid,debit_line_vals,context=context)
            self.pool.get('account.move.line').create(cr, uid,credit_line_vals,context=context)
            self.button_validate(cr, uid, [move_id], context=context)
            mov.write({'bounced': True})
        return True
    
account_move()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def onchange_amount_currency(self, cr, uid, ids, amount_currency, currency_id, context=None):
        res = {'value': {}}
        currency_pool = self.pool.get('res.currency')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        if currency_id:
            amount_curr = currency_pool.compute(cr, uid, user_obj.company_id.currency_id.id,
                                                currency_id, amount_currency)
            if amount_currency < 0.00:
                res['value']['credit'] = abs(amount_curr)
            else:
                res['value']['debit'] = abs(amount_curr)
        return res
    
    def onchange_partner_id(self, cr, uid, ids, move_id, partner_id, account_id=None,
                            debit=0, credit=0, date=False, journal=False, context=None):
        partner_pool = self.pool.get('res.partner')
        res = super(account_move_line, self).onchange_partner_id(cr, uid, ids, move_id, partner_id,
                                                                 account_id, debit, credit, date, journal,
                                                                 context=context)
        if partner_id:
            partner_obj = partner_pool.browse(cr, uid, ids, context=context)
            vals = {
                    'sl_cd': partner_obj.partner_ac_code or '',
                    'analytic_account_id': partner_obj.analytic_account_id and \
                                                partner_obj.analytic_account_id.id or False
                    }
            res['value'].update(vals)
        return res
    
    def onchange_partner_hatta(self, cr, uid, ids, partner_id, context=None):
        res = {'value': {}}
        res['value']['voucher_id'] = False
        return res
    
    def onchange_account_id(self, cr, uid, ids, account_id, context=None):
        res = {'value': {}, 'domain': {}}
        account_pool = self.pool.get('account.account')
        if account_id:
            account_obj = account_pool.browse(cr, uid, account_id, context=context)
            cost_center_obj = account_pool.get_cost_center(cr, uid, account_obj, context=context)
            if cost_center_obj:
                res['value']['analytic_account_id'] = cost_center_obj.id
            if account_obj.type == 'receivable':
                res['value']['line_type'] = 'customer'
                res['domain']['partner_id'] = "[('customer', '=', True)]"
            elif account_obj.type == 'payable':
                res['value']['line_type'] = 'supplier'
                res['domain']['partner_id'] = "[('supplier', '=', True)]"
            else:
                res['value']['line_type'] = 'general'
        return res
    
    def onchange_amount_curr(self, cr, uid, ids, currency_id, amount_currency, amount_curr_temp, debit, credit,
                             context=None):
        res = {'value': {'amount_currency': 0.00}}
        if currency_id:
            balance = debit - credit
            if balance < 0.00:
                amount = amount_curr_temp * -1.00
            else:
                amount = amount_curr_temp
            if amount != amount_currency:
                res['value']['amount_currency'] = amount
        return res
    
    def _get_move_lines(self, cr, uid, ids, context=None):
        result = []
        for move in self.pool.get('account.move').browse(cr, uid, ids, context=context):
            for line in move.line_id:
                result.append(line.id)
        return result
    
    def _get_move_line_date(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for move_line_obj in self.browse(cr, uid, ids, context=context):
            if move_line_obj.man_date:
                res[move_line_obj.id] = move_line_obj.man_date
            else:
                res[move_line_obj.id] = move_line_obj.move_id.date
        return res
    
    def _get_move_line_name(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for move_line in self.browse(cr, uid, ids, context=context):
            name = move_line.move_id and move_line.move_id.name or ''
            if move_line.ref:
                name = move_line.ref
            res[move_line.id] = name
        return res
    
    def _get_now(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in ids:
            due_date_from = datetime.today().date()
            res[id] =  due_date_from.strftime("%d/%m/%Y")
        return res
    
    def _get_diff_date(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in ids:
            due_date_from = datetime.today().date()
            due_date_to = due_date_from + timedelta(days=10)
            res[id] =  due_date_to.strftime("%d/%m/%Y")
        return res
    
    _columns = {
                'id': fields.integer('ID'),
                'sl_cd': fields.char('SL Cd.', size=128),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'doc_no': fields.char('Doc No.', size=128),
                'credit_line': fields.boolean('Credit Line'),
                'debit_line': fields.boolean('Debit Line'),
#                 'journal_acc_line': fields.boolean('Journal Account Line'),
#                 'bank_account_line': fields.boolean('Bank Account Line'),
                'voucher_id': fields.many2one('account.voucher', 'Voucher'),
                'matching_move_line_id': fields.many2one('account.move.line', 'Move line to match'),
                'line_type': fields.selection([('customer', 'Customer'), ('supplier', 'Supplier'), ('general', 'General')],
                                              'Line Type'),
                'name': fields.char('Remark', size=512),
                'amount_fc_temp': fields.float('Amount FC', digits_compute=dp.get_precision('Account')),
                'ref': fields.char('Reference', size=64),
                'man_ref': fields.char('Manual Reference', size=64),
                'man_date': fields.date('Manual Date'),
                'date': fields.function(_get_move_line_date, type="date", string="Date",
                                        store = {
                                                 'account_move_line': (lambda self, cr, uid, ids, c={}: ids, ['man_date'], 20),
                                                 'account.move': (_get_move_lines, ['date'], 20)
                                                 }),
                'move_line_name': fields.function(_get_move_line_name, type="char", size=128,
                                                  string="Voucher Name"),
                'date_today': fields.function(_get_now, string='Today', size=128),
                'diff_date': fields.function(_get_diff_date, string='', size=128)
                }
    
    def match_line(self, cr, uid, ids, context=None):
        
        return True
    
    def _query_get(self, cr, uid, obj='l', context=None):
        if context is None:
            context = {}
        
        res = super(account_move_line, self)._query_get(cr, uid, obj, context=context)
        if context.get('ann_account_ids', False):
            if len(context['ann_account_ids']) == 1:
                res += ' AND '+obj+'.analytic_account_id = %s' % context['ann_account_ids'][0]
            else:
                res += ' AND '+obj+'.analytic_account_id in %s' % tools.ustr(tuple(context['ann_account_ids']))
        if context.get('no_ann_account_ids', False):
            res += ' AND '+obj+'.analytic_account_id is null'
        return res
    
    def action_notification_mail(self, cr, uid, context=None):
        context = context or {}
        current_date = datetime.today().date()
        move_line_pool = self.pool.get('account.move.line')
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hatta_account',
                            'upcoming_payable_data_email')[1]
        condition = []
        condition.extend([('account_id.type','=','payable'),('reconcile_id','=',False),
                          ('credit', '>', 0.00), ('partner_id', '!=', False),('move_id.skip_check', '=', False)])
        due_date_from = datetime.today().date()
        due_date_to = due_date_from + timedelta(days=10)
#         condition.append(('date_maturity', '>=', due_date_from))
        condition.append(('date_maturity', '<=', due_date_to))
        move_line_ids = move_line_pool.search(cr, uid, condition, context=context)
        if move_line_ids:
            move_line_id = move_line_ids and move_line_ids[0]
#                 next_date = (datetime.strptime(tr.closing_date, '%Y-%m-%d')).date()
#                 notify_date = current_date + relativedelta(days=tr.notify_before)
#                 if notify_date == next_date:
            self.pool.get('email.template').send_mail(cr, uid, template_id, move_line_id, force_send=True, context=context)
        return True
    
account_move_line()

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def _check_voucher_balance(self, cr, uid, ids, context=None):
        for voucher_obj in self.browse(cr, uid, ids, context=context):
            if voucher_obj.writeoff_amount != 0.00:
                return False
        return True
    
    _columns = {
                'exist_move_line_id': fields.many2one('account.move.line', 'Existing Move Id'),
                }
    
    constraints = [
        (_check_voucher_balance, 'Invalid Matching!!!', ['name']),
        ]
    
    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        res = super(account_voucher, self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency,
                                                               current_currency, context=context)
        account_pool = self.pool.get('account.account')
        voucher_obj = self.browse(cr, uid, voucher_id, context=context)
        cost_center_obj = account_pool.get_cost_center(cr, uid, voucher_obj.account_id, context=context)
        res['analytic_account_id'] = cost_center_obj and cost_center_obj.id or False
        res['name'] = voucher_obj.reference and voucher_obj.reference or voucher_obj.name or '/'
        return res
    
    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency,
                               current_currency, context=None):
        voucher_obj = self.browse(cr, uid, voucher_id, context=context)
        res = super(account_voucher, self).writeoff_move_line_get(cr, uid, voucher_id, line_total,
                                                                  move_id, name, company_currency,
                                                                  current_currency, context=context)
        print res,">>>>>>>>>>>>>>>>>\n\n\n"
        if voucher_obj.reference and res:
            res['name'] = voucher_obj.reference
            res['date'] = voucher_obj.date
        return res
    
    def account_move_get(self, cr, uid, voucher_id, context=None):
        res = super(account_voucher, self).account_move_get(cr, uid, voucher_id, context=context)
        voucher_obj = self.browse(cr, uid, voucher_id, context=context)
        if voucher_obj.exist_move_line_id:
            move = voucher_obj.exist_move_line_id.move_id
            res['name'] = move.name
            res['skip_check'] = True
            res['display_check_details'] = move.display_check_details
            res['display_bank_details'] = move.display_bank_details
            res['display_check_type_date'] = move.display_check_type_date
            res['display_amount'] = move.display_amount
            res['display_invoice_details'] = move.display_invoice_details
            res['cheque_no'] = move.cheque_no
            res['cheque_type'] = move.cheque_type
            res['cheque_date'] = move.cheque_date
            res['bank_details'] = move.bank_details
            res['journal_partner_id'] = move.journal_partner_id and move.journal_partner_id.id or False
            res['journal_employee_part_id'] = move.journal_employee_part_id and \
                                                    move.journal_employee_part_id.id or False
            res['partner_name'] = move.partner_name
            res['bank_account_id'] = move.bank_account_id and move.bank_account_id.id or False
            res['cheque_amt'] = move.cheque_amt
            res['part_type'] = move.part_type
            res['gl_account_id'] = move.gl_account_id and move.gl_account_id.id or False
            res['ref'] = move.ref
            res['release_date'] = move.release_date
            res['cheque_released'] = move.cheque_released
            res['bounced'] = move.bounced
            res['invoice_id'] = move.invoice_id and move.invoice_id.id or False
            res['invoice_date'] = move.invoice_date
            res['lpo_no'] = move.lpo_no
        return res
    
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id,
                                ttype, date, context=None):
        if context is None:
            context = {}
        res = super(account_voucher, self).recompute_voucher_lines(cr, uid, ids, partner_id,
                                                                   journal_id, 0.00, currency_id,
                                                                   ttype, date, context=context)
        active_move_line = context.get('active_move_line', False)
        if not active_move_line:
            raise osv.except_osv(_("Error!!!"),
                                 _("Please save the record before proceeding !!!!"))
        value = res['value']
        line_cr_ids = value.get('line_cr_ids', [])
        line_dr_ids = value.get('line_dr_ids', [])
        new_line_cr_ids = []
        new_line_dr_ids = []
        active_move_line = context['active_move_line']
        for line in line_cr_ids:
            line_move_id = line.get('move_line_id', '')
            if line_move_id == active_move_line:
                line['reconcile'] = True
                line['amount'] = line.get('amount_unreconciled', 0.00)
            elif line_move_id != active_move_line:
                line['reconcile'] = False
                line['amount'] = 0.00
            new_line_cr_ids.append(line)
        for line in line_dr_ids:
            line_move_id = line.get('move_line_id', '')
            if line_move_id == active_move_line:
                line['reconcile'] = True
                line['amount'] = line.get('amount_unreconciled', 0.00)
            elif line_move_id != active_move_line:
                line['reconcile'] = False
                line['amount'] = 0.00
            new_line_dr_ids.append(line)
        res['value']['line_cr_ids'] = new_line_cr_ids
        res['value']['line_dr_ids'] = new_line_dr_ids
        return res
    
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        account_pool = self.pool.get('account.account')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = voucher.type in ('payment', 'purchase') and -1 or 1
                print line.move_line_id.amount_residual,"---------------",amount,"\n\n\n"
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
                print currency_rate_difference
            else:
                currency_rate_difference = 0.0
            
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                account_obj = line.account_id
                cost_center_obj = account_pool.get_cost_center(cr, uid, account_obj, context=context)
                move_line['sl_cd'] = line.move_line_id.sl_cd
                move_line['job_id'] = line.move_line_id.job_id and line.move_line_id.job_id.id or False
                move_line['doc_no'] = line.move_line_id.doc_no
                move_line['credit_line'] = line.move_line_id.credit_line
                move_line['debit_line'] = line.move_line_id.debit_line
                move_line['voucher_id'] = False
                move_line['line_type'] = line.move_line_id.line_type
                move_line['name'] = line.move_line_id.name
                move_line['amount_fc_temp'] = line.move_line_id.amount_fc_temp
                move_line['ref'] = line.move_line_id.ref
                move_line['man_ref'] = line.move_line_id.man_ref
                move_line['analytic_account_id'] = cost_center_obj and cost_center_obj.id or False
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
#                         if line.move_line_id.invoice and line.move_line_id.invoice.type == 'in_invoice':
#                             exchange_rate = line.move_line_id.invoice.exchange_rate or 1.000
#                             amount = move_line['debit']-move_line['credit']
#                             amount_currency = amount / exchange_rate
                        
                if line.amount == line.amount_unreconciled:
                    sign = voucher.type in ('payment', 'purchase') and -1 or 1
                    foreign_currency_diff = sign * line.move_line_id.amount_residual_currency + amount_currency

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                account_obj = line.account_id
                cost_center_obj = account_pool.get_cost_center(cr, uid, account_obj, context=context)
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                    'analytic_account_id': cost_center_obj and cost_center_obj.id or False
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return (tot_line, rec_lst_ids)
    
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            local_context = dict(context, force_company=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            first_move_line_vals = self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context)
            first_move_line_credit = first_move_line_vals.get('credit', 0.00)
            first_move_line_debit = first_move_line_vals.get('debit', 0.00)
            line_total = 0.00
            if first_move_line_credit != 0.00 or first_move_line_debit != 0.00:
                move_line_id = move_line_pool.create(cr, uid, first_move_line_vals, local_context)
                move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
                line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, local_context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True
    
    def cancel_voucher(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            # refresh to make sure you don't unlink an already removed move
            voucher.refresh()
            voucher_move_line_ids = [x.id for x in voucher.move_ids]
            for line_id in voucher_move_line_ids:
                line = move_line_pool.browse(cr, uid, line_id, context=context)
                if line.reconcile_id:
                    move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
                    move_lines.remove(line.id)
                    reconcile_pool.unlink(cr, uid, [line.reconcile_id.id])
                    if len(move_lines) >= 2:
                        move_line_pool.reconcile_partial(cr, uid, move_lines, 'auto',context=context)
            if voucher.move_id:
                if voucher.move_id != voucher.exist_move_line_id.move_id or voucher.move_id.skip_check:
                    move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                    move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True
     
    def proforma_voucher(self, cr, uid, ids, context=None):
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.writeoff_amount != 0.00:
                raise osv.except_osv(_("Error!!!"),
                                     _("Invalid Matching!!!!. Please check difference amount."))
        res = super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)
        return res
     
account_voucher()

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    _columns = {
                'sequence_id': fields.many2one('ir.sequence', 'Sequence'),
                'default': fields.boolean('Default ?'),
                'system_sale_price': fields.boolean('Get System Sale Price?'),
                'send_quote_mail': fields.boolean('Send Quote by mail ?'),
                'reg_pay_invoice': fields.boolean('Register Payment From Invoice ?')
                }
account_analytic_account()

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'
    _columns = {
                'account_type': fields.selection([('current', 'Current'), ('od', 'OD')], 'Account Type'),
                'od_limit' : fields.float('OD Limit', digits_compute=dp.get_precision('Account'))
                }
res_partner_bank()

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
#                 'tr_limit': fields.float('TR Limit', digits_compute=dp.get_precision('Account'))
                'tr_limit' : fields.one2many('tr.model', 'company_id', string="TR Limit")
                }
res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

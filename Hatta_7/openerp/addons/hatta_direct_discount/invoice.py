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

import openerp.addons.decimal_precision as dp
from tools.translate import _
from openerp.tools.safe_eval import safe_eval


class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = super(account_invoice, self)._amount_all(cr, uid, ids, name, args, context)
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id]['amount_orginal'] = res[invoice.id]['amount_untaxed']
            res[invoice.id]['amount_untaxed'] -= invoice.discount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res
    
    _columns = {
                'discount': fields.float('Discount', digits_compute=dp.get_precision('Account')),
                'amount_orginal': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Orginal Amount', track_visibility='always',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'discount'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all'),
                'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'discount'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all'),
                'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'discount'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all'),
                'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'discount'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all'),
                }
    
    def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
        total, total_currency, invoice_move_lines = super(account_invoice, self).compute_invoice_totals(cr, uid, inv, company_currency, ref,
                                                                  invoice_move_lines, context=context)
        sign = 1
        if total < 0.00:
            sign = -1
        discount = inv.discount
        exchange_rate = total_currency / total
        if discount != 0.00:
            discount *= sign
            discount_currency = discount * inv.exchange_rate
            total -= discount
            total_currency -= discount_currency
        return total, total_currency, invoice_move_lines
    
    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        #if invoice_browse.global_discount > 0.00:
        icp = self.pool.get('ir.config_parameter')
        account_pool = self.pool.get('account.account')
        discount_account_id =False
        if invoice_browse.type in ['in_invoice', 'out_refund']:
            discount_account_id = safe_eval(icp.get_param(cr, uid,
                                                          'hatta_direct_discount.discount_in_account', 'False'))
        elif invoice_browse.type in ['out_invoice', 'in_refund']:
            discount_account_id = safe_eval(icp.get_param(cr, uid,
                                                          'hatta_direct_discount.discount_out_account', 'False'))
        if not discount_account_id and invoice_browse.discount != 0.00:
            raise osv.except_osv(_("Error!!!!"),
                                 _("Please configure discount account !!!"))
#         total_amount = 0.0
        precisione = self.pool.get('decimal.precision').precision_get(cr, 1, 'Account')
        for m in move_lines:
            if m[2]['credit'] > 0.00:
                m[2]['credit'] = round(m[2]['credit'], precisione)
            if m[2]['debit'] > 0.00:
                m[2]['debit'] = round(m[2]['debit'], precisione)

        new_line = {'analytic_account_id': False, 'tax_code_id': False, 'analytic_lines': [],
            'tax_amount': False, 'name': _('Global Discount'), 'ref': '',
            'analytics_id': False, 'currency_id': False, 'debit': False ,
            'product_id': False, 'date_maturity': False, 'credit': False, 'date': move_lines[0][2]['date'],
            'amount_currency': 0, 'product_uom_id': False, 'quantity': 1, 'partner_id': move_lines[0][2]['partner_id'],
            'account_id': discount_account_id}
        # se c'è lo sconto va tolto dalle scadenze 
        if invoice_browse.discount != 0.00:
            discount = invoice_browse.discount
            discount = discount * invoice_browse.exchange_rate
            if invoice_browse.currency_id.id != invoice_browse.company_id.currency_id.id:
                new_line['amount_currency'] = invoice_browse.discount * -1.00
                new_line['currency_id'] = invoice_browse.currency_id.id
            if invoice_browse.type in ['out_invoice', 'in_refund']:
                if invoice_browse.discount > 0.00:
                    new_line['debit'] = round(abs(discount), precisione)
                else:
                    new_line['credit'] = round(abs(discount), precisione)
            else:
                if invoice_browse.discount > 0.00:
                    new_line['credit'] = round(abs(discount), precisione)
                else:
                    new_line['debit'] = round(abs(discount), precisione)
            move_lines += [(0,0,new_line)]
        credit_amount = 0.00
        debit_amount = 0.00
        for m in move_lines:
            if m[2]['credit'] > 0.00:
                credit_amount += m[2]['credit']
            if m[2]['debit'] > 0.00:
                debit_amount += m[2]['debit']
        net_balance = debit_amount - credit_amount
        net_balance = round(net_balance, precisione)
        if net_balance != 0.00:
            credit = 0.00
            debit = 0.00
            if net_balance < 0.00:
                debit = net_balance * -1.00
            else:
                credit = net_balance
            for m in move_lines:
                if m[2]['credit'] > 0.00 and credit > 0.00:
                    m[2]['credit'] += credit
                    credit = 0.00
                    break
                if m[2]['debit'] > 0.00 and debit > 0.00:
                    m[2]['debit'] += debit
                    debit = 0.00
                    break
        return move_lines
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

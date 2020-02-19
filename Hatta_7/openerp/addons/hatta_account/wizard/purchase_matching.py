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
from openerp import netsvc

class purchase_matching(osv.osv_memory):
    _name = 'purchase.matching'
    _description = 'Matching in Purchase'
    
    def default_get(self, cr, uid, field_names, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        res = super(purchase_matching, self).default_get(cr, uid, field_names, context=context)
        picking_pool = self.pool.get('stock.picking.in')
        invoice_pool = self.pool.get('account.invoice')
        voucher_pool = self.pool.get('account.voucher')
        journal_pool = self.pool.get('account.journal')
        currency_pool = self.pool.get('res.currency')
        active_id = context.get('active_id', False)
        if active_id:
            picking_obj = picking_pool.browse(cr, uid, active_id, context=context)
            if not picking_obj.invoice_id:
                raise osv.except_osv(_("Error!!!"),
                                     _("No Invoice Found for this purchase !!!"))
            partner_id = picking_obj.partner_id.parent_id and picking_obj.partner_id.parent_id.id or \
                                picking_obj.partner_id.id or False
            invoice_obj = invoice_pool.browse(cr, uid, picking_obj.invoice_id.id, context=context)
            res['partner_id'] = partner_id
            res['invoice_id'] = invoice_obj.id or False
            if invoice_obj.move_id:
                invoice_account_id = invoice_obj.account_id.id
                active_move_objs = [x for x in invoice_obj.move_id.line_id if x.account_id.id == invoice_account_id]
                if active_move_objs:
                    active_move_obj = active_move_objs[0]
                    line_currency_id = active_move_obj.currency_id and active_move_obj.currency_id.id or False
                    comp_current_id = invoice_obj.company_id.currency_id.id
                    invoice_amount = abs(active_move_obj.amount_residual)
                    res['invoice_amount'] = invoice_amount
                    res['balance_amount'] = invoice_amount
                    res['invoice_move_line_id'] = active_move_obj.id
                    ctx.update({
                                'default_number': invoice_obj.move_id.name,
                                'active_move_line': active_move_obj.id,
                                'line_type': 'dr',
                                'default_type': 'payment',
                                'type': 'payment',
                                'account_id': invoice_obj.account_id.id
                                })
                    journal_ids = journal_pool.search(cr, uid, [('display_in_voucher', '=', True)],
                                                      context=context)
                    line_data = voucher_pool.recompute_voucher_lines(cr, uid, [], partner_id,
                                                                     journal_ids[0], 0.00,
                                                                     comp_current_id,
                                                                     'payment', invoice_obj.date_invoice, context=ctx)
                    line_cr_ids = line_data['value'].get('line_cr_ids', [])
                    line_dr_ids = line_data['value'].get('line_dr_ids', [])
                    real_line_cr_ids = []
                    real_line_dr_ids = []
                    for line in line_cr_ids:
                        real_line_cr_ids.append((0, 0, line))
                    for line in line_dr_ids:
                        real_line_dr_ids.append((0, 0, line))
                    res['line_ids'] = real_line_cr_ids
                    res['line_dr_ids'] = real_line_dr_ids
                else:
                    raise osv.except_osv(_("Error!!!"),
                                         _("Invalid Invoice !!!!!"))
            else:
                raise osv.except_osv(_("Error!!!"),
                                     _("Invalid Invoice !!!!"))
        else:
            raise osv.except_osv(_("Error!!!!"),
                                 _("Unable to process request. Please Contact Admin!!!!"))
        return res
    
    def onchange_lines(self, cr, uid, ids, invoice_amount, line_ids, context=None):
        res = {'value': {'balance_amount': invoice_amount or 0.00}}
        line_pool = self.pool.get('purchase.matching.line')
        if line_ids:
            amount_rec = 0.00
            for line in line_ids:
                amount = 0.00
                if line[0] == 0:
                    data = line[2]
                    amount = data.get('amount', 0.00)
                elif line[0] == 4:
                    line_obj = line_pool.browse(cr, uid, line[1], context=context)
                    amount = line_obj.amount or 0.00
                amount_rec += amount
            res['value']['balance_amount'] = invoice_amount - amount_rec
        return res
    
    _columns = {
                'invoice_id': fields.many2one('account.invoice', 'Invoice'),
                'invoice_move_line_id': fields.many2one('account.move.line', 'Invoice Move Ref'),
                'partner_id': fields.many2one('res.partner', 'Partner'),
                'line_ids': fields.one2many('purchase.matching.line', 'wizard_id', 'Matching Lines'),
                'line_dr_ids': fields.one2many('purchase.matching.line', 'wizard_id2', 'Matching Lines'),
                'invoice_amount': fields.float('Purchase Amount', digits_compute=dp.get_precision('Account')),
                'balance_amount': fields.float('Balance Purchase Amount',
                                               digits_compute=dp.get_precision('Account'))
                }
    
    def match_payments(self, cr, uid, ids, context=None):
        line_pool = self.pool.get('purchase.matching.line')
        move_line_pool = self.pool.get('account.move.line')
        voucher_pool = self.pool.get('account.voucher')
        invoice_pool = self.pool.get('account.invoice')
        data = self.read(cr, uid, ids, context={})[0]
        unmatched_pmt = data.get('balance_amount', 0.00)
        if unmatched_pmt < 0.00:
            raise osv.except_osv(_("Error!!!"),
                                 _("Invalid Matching!!!!"))
        line_cr_ids = data.get('line_ids', [])
        line_dr_ids = data.get('line_dr_ids', [])
        invoice_id = data.get('invoice_id', False)
        print invoice_id
        invoice_obj = invoice_pool.browse(cr, uid, invoice_id[0], context=context)
        line_cr_vals = []
        line_dr_vals = []
        rec_line_data = {}
        for line_obj in line_pool.browse(cr, uid, line_cr_ids, context=context):
            if line_obj.amount:
                line_dr_vals = []
                line_move_line_id = line_obj.move_line_id.id
                move_line_obj = move_line_pool.browse(cr, uid, line_move_line_id, context=context)
                line_amount = line_obj.amount
                vals = {
                        'date_due': line_obj.date_due,
                        'reconcile': line_obj.reconcile,
                        'date_original': line_obj.date_original,
                        'amount_original': line_obj.amount_original,
                        'account_id': line_obj.account_id.id,
                        'name': line_obj.name,
                        'move_line_id': line_obj.move_line_id.id,
                        'amount_unreconciled': line_obj.amount_unreconciled,
                        'amount': line_obj.amount,
                        'type': line_obj.type
                        }
                for dr_line_obj in line_pool.browse(cr, uid, line_dr_ids, context=context):
                    if dr_line_obj.amount and line_amount:
                        dr_vals = {
                                   'date_due': dr_line_obj.date_due,
                                   'reconcile': False,
                                   'date_original': dr_line_obj.date_original,
                                   'amount_original': dr_line_obj.amount_original,
                                   'account_id': dr_line_obj.account_id.id,
                                   'name': dr_line_obj.name,
                                   'move_line_id': dr_line_obj.move_line_id.id,
                                   'amount_unreconciled': dr_line_obj.amount_unreconciled,
                                   'amount': line_amount,
                                   'type': dr_line_obj.type
                                   }
                        line_amount = 0.00
                        line_dr_vals.append((0, 0, dr_vals))
                voucher_vals = {}
                context['active_move_line'] = move_line_obj.id
                onchange_partner_data = voucher_pool.onchange_partner_id(cr, uid, ids, data['partner_id'][0],
                                                                         move_line_obj.move_id.journal_id.id,
                                                                         0.00,
                                                                         invoice_obj.company_id.currency_id.id,
                                                                         'payment', move_line_obj.move_id.date,
                                                                         context=context)
                voucher_vals.update(onchange_partner_data.get('value', {}))
                onchange_journal_data = voucher_pool.onchange_journal(cr, uid, ids,
                                                                      move_line_obj.move_id.journal_id.id,
                                                                      line_dr_vals, False,
                                                                      data['partner_id'][0],
                                                                      move_line_obj.move_id.date,
                                                                      0.00, 'payment',
                                                                      invoice_obj.company_id.id,
                                                                      context=context
                                                                      )
                voucher_vals.update(onchange_journal_data.get('value', {}))
                voucher_vals['journal_id'] = move_line_obj.move_id.journal_id.id
                onchange_date_data = voucher_pool.onchange_date(cr, uid, ids, move_line_obj.move_id.date,
                                                                invoice_obj.company_id.currency_id.id,
                                                                invoice_obj.company_id.currency_id.id,
                                                                0.00, invoice_obj.company_id.id,
                                                                context=context)
                voucher_vals.update(onchange_date_data.get('value', {}))
                voucher_vals.update({
                                     'number': move_line_obj.move_id.name or '/',
                                     'type': 'payment',
                                     'partner_id': data['partner_id'][0],
                                     'journal_id': move_line_obj.move_id.journal_id.id,
                                     'reference': move_line_obj.name,
                                     'date': move_line_obj.move_id.date,
                                     'name': move_line_obj.name,
                                     'active': True,
                                     'account_id': move_line_obj.account_id.id,
                                     'pre_line': line_dr_vals and True or False,
                                     'line_cr_ids': [(0, 0, vals)],
                                     'line_dr_ids': line_dr_vals,
                                     'exist_move_line_id': move_line_obj.id,
                                     'payment_rate_currency_id': invoice_obj.company_id.currency_id.id,
                                     'paid_amount_in_company_currency': line_obj.amount
                                     })
                voucher_id = voucher_pool.create(cr, uid, voucher_vals, context=context)
                if move_line_obj.move_id.state == 'posted':
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(uid, 'account.voucher', \
                                            voucher_id, 'proforma_voucher', cr)
                move_line_obj.write({'voucher_id': voucher_id})
        return True
    
purchase_matching()

class purchase_matching_line(osv.osv_memory):
    _name = 'purchase.matching.line'
    _description = 'Matching Lines'
    
    def onchange_reconcile(self, cr, uid, ids, reconcile, amount_unreconciled, context=None):
        res = {'value': {'amount': 0.00}}
        if reconcile:
            res['value']['amount'] = amount_unreconciled
        return res
    
    _columns = {
                'wizard_id':fields.many2one('purchase.matching', 'Wizard'),
                'wizard_id2':fields.many2one('purchase.matching', 'Wizard'),
                'name':fields.char('Description', size=256),
                'account_id':fields.many2one('account.account','Account', required=True),
                'untax_amount':fields.float('Untax Amount'),
                'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'reconcile': fields.boolean('Full Reconcile'),
                'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Dr/Cr'),
                'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),
                'move_line_id': fields.many2one('account.move.line', 'Journal Item'),
                'date_original': fields.date('Date'),
                'date_due': fields.date('Due Date'),
                'amount_original': fields.float(string='Original Amount',
                                                digits_compute=dp.get_precision('Account')),
                'amount_unreconciled': fields.float(string='Open Balance', store=True,
                                                    digits_compute=dp.get_precision('Account'))
                }
purchase_matching_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

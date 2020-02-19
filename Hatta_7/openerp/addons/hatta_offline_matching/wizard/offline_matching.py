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
from openerp.tools import float_compare

class offline_matching(osv.osv_memory):
    _name = 'offline.matching'
    _description = 'Offline Matching'
    
    def onchange_cr_lines(self, cr, uid, ids, line_cr_ids, context=None):
        res = {'value': {}}
        line_pool = self.pool.get('offline.matching.line')
        amount_rec = 0.00
        for line in line_cr_ids:
            amount = 0.00
            if line[0] == 4:
                line_obj = line_pool.browse(cr, uid, line[1], context=context)
                amount = line_obj.amount or 0.00
            elif line[0] == 0:
                data = line[2]
                amount = data.get('amount', 0.00)
            elif line[0] == 1:
                line_obj = line_pool.browse(cr, uid, line[1], context=context)
                data = line[2]
                if data.get('amount', 0.00):
                    amount = data['amount']
                else:
                    amount = line_obj.amount
            amount_rec += amount
        res['value']['credit_amount'] = amount_rec
        return res
    
    def onchange_dr_lines(self, cr, uid, ids, line_dr_ids, context=None):
        res = {'value': {}}
        line_pool = self.pool.get('offline.matching.line')
        amount_rec = 0.00
        for line in line_dr_ids:
            amount = 0.00
            if line[0] == 4:
                line_obj = line_pool.browse(cr, uid, line[1], context=context)
                amount = line_obj.amount or 0.00
            elif line[0] == 0:
                data = line[2]
                amount = data.get('amount', 0.00)
            elif line[0] == 1:
                line_obj = line_pool.browse(cr, uid, line[1], context=context)
                data = line[2]
                if data.get('amount', 0.00):
                    amount = data['amount']
                else:
                    amount = line_obj.amount
            amount_rec += amount
        res['value']['debit_amount'] = amount_rec
        return res
    
    _columns = {
                'partner_id': fields.many2one('res.partner', 'Partner',
                                              domain="[('parent_id', '=', False)]"),
                'credit_amount': fields.float('Credit Amount', digits_compute=dp.get_precision('Account')),
                'debit_amount': fields.float('Debit Amount', digits_compute=dp.get_precision('Account')),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'account_id': fields.many2one('account.account', "GL Code",
                                              domain="[('type', 'in', ['receivable', 'payable'])]"),
                'line_cr_ids': fields.one2many('offline.matching.line', 'wizard_id', 'Credit'),
                'line_dr_ids': fields.one2many('offline.matching.line', 'wizard_id2', 'Debit'),
                'ongoing_matching': fields.boolean('Ongoing Matching')
                }
    
    def display_tran(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        voucher_pool = self.pool.get('account.voucher')
        journal_pool = self.pool.get('account.journal')
        user_pool = self.pool.get('res.users')
        move_line_pool = self.pool.get('account.move.line')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_currency_id = user_obj.company_id.currency_id.id
        for wiz in self.browse(cr, uid, ids, context=context):
            clear_vals = {
                          'line_cr_ids': [(5, wiz.id)],
                          'line_dr_ids': [(5, wiz.id)]
                          }
            wiz.write(clear_vals)
            partner_id = wiz.partner_id.id
            cost_center_id = wiz.cost_center_id and wiz.cost_center_id.id or False
            account_id = wiz.account_id.id
            type = wiz.account_id.type == 'receivable' and 'receipt' or 'payment'
            ctx = context.copy()
            ctx.update({
                        'default_number': '/',
                        'active_move_line': 1,
                        'line_type': type == 'receipt' and 'cr' or 'dr',
                        'default_type': type,
                        'type': type,
                        'account_id': account_id
                        })
            journal_ids = journal_pool.search(cr, uid, [('display_in_voucher', '=', True)],
                                              context=context)
            today = fields.date.today()
            line_data = voucher_pool.recompute_voucher_lines(cr, uid, [], partner_id,
                                                             journal_ids[0], 0.00,
                                                             comp_currency_id,
                                                             type, today, context=ctx)
            line_cr_ids = line_data['value'].get('line_cr_ids', [])
            line_dr_ids = line_data['value'].get('line_dr_ids', [])
            real_line_cr_ids = []
            real_line_dr_ids = []
            for line in line_cr_ids:
                move_line_id = line.get('move_line_id', False)
                move_line_obj = move_line_pool.browse(cr, uid, move_line_id, context=context)
                if move_line_obj.move_id.state == 'posted':
                    real_line_cr_ids.append((0, 0, line))
            for line in line_dr_ids:
                move_line_id = line.get('move_line_id', False)
                move_line_obj = move_line_pool.browse(cr, uid, move_line_id, context=context)
                if move_line_obj.move_id.state == 'posted':
                    real_line_dr_ids.append((0, 0, line))
            vals = {
                    'line_cr_ids': real_line_cr_ids,
                    'line_dr_ids': real_line_dr_ids
                    }
            if not real_line_cr_ids and not real_line_dr_ids and not wiz.ongoing_matching:
                raise osv.except_osv(_("Error!!!"),
                                     _("Nothing to display!!!"))
            if wiz.ongoing_matching:
                wiz.write({'ongoing_matching': False})
            wiz.write(vals)
        return True
    
    def update_tran(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context=context):
            cr_amount = 0.00
            dr_amount = 0.00
            for cr_line in wiz.line_cr_ids:
                cr_amount += cr_line.amount
            for dr_line in wiz.line_dr_ids:
                dr_amount += dr_line.amount
            wiz.write({'credit_amount': cr_amount, 'debit_amount': dr_amount})
        return True
    
    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        user_pool = self.pool.get('res.users')
        voucher_pool = self.pool.get('account.voucher')
        move_line_pool = self.pool.get('account.move.line')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_id = user_obj.company_id.id
        company_curr_id = user_obj.company_id.currency_id.id
        for wiz in self.browse(cr, uid, ids, context=context):
            partner_id = wiz.partner_id.id
            account_obj = wiz.account_id
            account_type = account_obj.type
            voucher_name_list = []
            name_list = []
            journal_id = False
            type = ''
            paid_amount = 0.00
            adj_amount = 0.00
            exist_line_id = False
            payment_line_ids = []
            today = fields.date.today()
            if account_type == 'payable':
                type = 'payment'
                for line in wiz.line_cr_ids:
                    if line.amount:
                        exist_line_id = line.move_line_id.id
                        payment_line_ids.append(exist_line_id)
                        voucher_name_list.append(line.move_line_id.move_id.name)
                        journal_id = line.move_line_id.move_id.journal_id.id
                        name_list.append(line.name)
                        paid_amount += line.amount
                        today = line.date_original
                if not voucher_name_list:
                    raise osv.except_osv(_("Error!!!"),
                                         _("No Payment Mapped!!!!"))
            elif account_type == 'receivable':
                type = 'receipt'
                for line in wiz.line_dr_ids:
                    if line.amount:
                        exist_line_id = line.move_line_id.id
                        payment_line_ids.append(exist_line_id)
                        voucher_name_list.append(line.move_line_id.move_id.name)
                        journal_id = line.move_line_id.move_id.journal_id.id
                        name_list.append(line.name)
                        paid_amount += line.amount
                        today = line.date_original
                if not voucher_name_list:
                    raise osv.except_osv(_("Error!!!"),
                                         _("No Payment Mapped!!!!"))
            voucher_name = ','.join(voucher_name_list)
            name = ','.join(name_list)
            print voucher_name,"------------------>VOUCHER NAME\n\n\n"
            voucher_vals = {}
            context['active_move_line'] = 1
            
            
            
            line_cr_vals = []
            line_dr_vals = []
            for dr_line_obj in wiz.line_dr_ids:
                if dr_line_obj.amount:
                    if type == 'payment':
                        adj_amount += dr_line_obj.amount
                    dr_vals = {
                               'date_due': dr_line_obj.date_due,
                               'reconcile': dr_line_obj.reconcile,
                               'date_original': dr_line_obj.date_original,
                               'amount_original': dr_line_obj.amount_original,
                               'account_id': dr_line_obj.account_id.id,
                               'name': dr_line_obj.name,
                               'move_line_id': dr_line_obj.move_line_id.id,
                               'amount_unreconciled': dr_line_obj.amount_unreconciled,
                               'amount': dr_line_obj.amount,
                               'type': dr_line_obj.type
                               }
                    line_dr_vals.append((0, 0, dr_vals))
            for cr_line_obj in wiz.line_cr_ids:
                if cr_line_obj.amount:
                    print cr_line_obj.amount
                    if type == 'receipt':
                        adj_amount += cr_line_obj.amount
                    cr_vals = {
                               'date_due': cr_line_obj.date_due,
                               'reconcile': cr_line_obj.reconcile,
                               'date_original': cr_line_obj.date_original,
                               'amount_original': cr_line_obj.amount_original,
                               'account_id': cr_line_obj.account_id.id,
                               'name': cr_line_obj.name,
                               'move_line_id': cr_line_obj.move_line_id.id,
                               'amount_unreconciled': cr_line_obj.amount_unreconciled,
                               'amount': cr_line_obj.amount,
                               'type': cr_line_obj.type
                               }
                    line_cr_vals.append((0, 0, cr_vals))
            precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
            comp_res = float_compare(adj_amount, paid_amount, precision_digits=precision)
            if comp_res == -1:
                raise osv.except_osv(_("Error!!!"),
                                     _("Invalid Matching!!!!"))
#             today = fields.date.today()
            onchange_partner_data = voucher_pool.onchange_partner_id(cr, uid, ids, partner_id,
                                                                     journal_id,
                                                                     0.00,
                                                                     company_curr_id,
                                                                     type, today,
                                                                     context=context)
            voucher_vals.update(onchange_partner_data.get('value', {}))
            onchange_journal_data = voucher_pool.onchange_journal(cr, uid, ids,
                                                                  journal_id,
                                                                  line_dr_vals, False,
                                                                  partner_id,
                                                                  today,
                                                                  0.00, type,
                                                                  company_id,
                                                                  context=context
                                                                  )
            voucher_vals.update(onchange_journal_data.get('value', {}))
            voucher_vals['journal_id'] = journal_id
            onchange_date_data = voucher_pool.onchange_date(cr, uid, ids, today,
                                                            company_curr_id,
                                                            company_curr_id,
                                                            0.00, company_id,
                                                            context=context)
            voucher_vals.update(onchange_date_data.get('value', {}))
            voucher_vals.update({
                                 'number': voucher_name,
                                 'type': type,
                                 'partner_id': partner_id,
                                 'journal_id': journal_id,
                                 'reference': name,
                                 'date': today,
                                 'name': name,
                                 'active': True,
                                 'account_id': wiz.account_id.id,
                                 'pre_line': type == 'payment' and line_dr_vals or line_cr_vals,
                                 'line_cr_ids': line_cr_vals,
                                 'line_dr_ids': line_dr_vals,
                                 'exist_move_line_id': exist_line_id,
                                 'payment_rate_currency_id': company_curr_id,
                                 'paid_amount_in_company_currency': paid_amount
                                 })
            print voucher_vals
            voucher_id = voucher_pool.create(cr, uid, voucher_vals, context=context)
            print voucher_id,"------------>VOUCHER ID"
            move_line_pool.write(cr, uid, payment_line_ids, {'voucher_id': voucher_id}, context=context)
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'account.voucher', \
                                    voucher_id, 'proforma_voucher', cr)
            wiz.write({'ongoing_matching': True})
            wiz.display_tran()
            wiz.update_tran()
            
            
            
            
            
            
            
            
#         raise osv.except_osv(_("Error!!!"),
#                              _("Not Implemented!!!!"))
        return True
    
offline_matching()

class offline_matching_line(osv.osv_memory):
    _name = 'offline.matching.line'
    _description = 'Offline Matching Line'
    
    def onchange_reconcile(self, cr, uid, ids, reconcile, amount_unreconciled, context=None):
        res = {'value': {'amount': 0.00}}
        if reconcile:
            res['value']['amount'] = amount_unreconciled
        return res
    
    _columns = {
                'wizard_id':fields.many2one('offline.matching', 'Wizard'),
                'wizard_id2':fields.many2one('offline.matching', 'Wizard'),
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
offline_matching_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

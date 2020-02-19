# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
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

from osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class bank_status_report(osv.osv):
    _name = "bank.status.report"
    _description = "Bank Status Report"
    _order = "id desc"
    _rec_name = 'account_id'
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for bank_status_obj in self.browse(cr, uid, ids, context=context):
            total_deposit = 0.0
            total_withdraw = 0.0
            amount_available = 0.0
            total_fund = 0.0
            res[bank_status_obj.id] = {
                'total_deposit': 0.0,
                'total_withdraw': 0.0,
                'book_balance': 0.0,
                'amount_available': 0.0,
                'total_fund': 0.0,
            }
            for deposit_obj in bank_status_obj.deposit_ids:
                total_deposit += deposit_obj.amount_selected
            for withdraw_obj in bank_status_obj.withdrawal_ids:
                total_withdraw += withdraw_obj.amount_selected
            book_balance = bank_status_obj.bank_balance + (total_deposit - total_withdraw)
            amount_available = bank_status_obj.od_limit + book_balance
            total_fund = bank_status_obj.safe_funds + amount_available
            res[bank_status_obj.id]['total_deposit'] = total_deposit
            res[bank_status_obj.id]['total_withdraw'] = total_withdraw
            res[bank_status_obj.id]['book_balance'] = book_balance
            res[bank_status_obj.id]['amount_available'] = amount_available
            res[bank_status_obj.id]['total_fund'] = total_fund
        return res
    
    _columns = { 
                'account_id': fields.many2one('account.account','Bank'),
                'date': fields.date('Date'),
                'bank_balance': fields.float('Balance as per Bank '),
                'deposit_ids': fields.one2many('bank.status.deposit', 'bank_status_id', 'Deposits'),
                'withdrawal_ids': fields.one2many('bank.status.withdraw', 'bank_status_id', 'Withdrawals'),
                'book_balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Balance as per Book',
                                                multi='sums'),
                'od_limit': fields.float('OD Limit'),
                'safe_funds': fields.float('Less Safe Funds [Checques not yet Issues]'),
                'amount_available': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Amount Available Including OD Limit',
                                                    multi='sums'), 
                'total_deposit': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Deposit',
                                                multi='sums'),
                'total_withdraw': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Withdrawal',
                                                multi='sums'),
                'total_fund': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Funds Available after considering Safe Funds',
                                                multi='sums'),
                'edit_mode': fields.boolean('Edit Mode', copy=False),
                }
    
    _defaults = {
        'date': fields.date.context_today,
        }
    
    def onchange_account_id(self, cr, uid, ids, account_id, date, context=None):
        res = {}
        deposit_ids = []
        withdrawal_ids = []
        warning = {}
        move_line_pool = self.pool.get('account.move.line')
        if account_id:
            account_obj = self.pool.get('account.account').browse(cr, uid, account_id, context=context)
            deposit_journal_items = move_line_pool.search(cr, uid, [('account_id', '=',account_id),
                                                                   ('journal_id.is_deposit', '=',True),
                                                                   '|',('rec_date', '=',False),('rec_date', '>',date)],context=context)
            withdrawal_journal_items = move_line_pool.search(cr, uid, [('account_id', '=',account_id),
                                                                       ('journal_id.is_withdrawal', '=',True),
                                                                       '|',('rec_date', '=',False),('rec_date', '>',date)], context=context)
            warning_msgs = ''
            if not deposit_journal_items and not withdrawal_journal_items:
                res.update({'deposit_ids': deposit_ids, 'withdrawal_ids': withdrawal_ids})
                warn_msg = _("No Deposits and Withdrawals for this Bank!")
                warning_msgs += _("No Transactions found for the bank %s %s !")% (account_obj.code,account_obj.name) + "\n\n"
            if deposit_journal_items:
                for deposit_move_line in move_line_pool.browse(cr, uid, deposit_journal_items, context=context):
                    deposit_dict = { 
                        'move_line_id': deposit_move_line.id,
                        'remark':  deposit_move_line.name,
                        'original_amount': deposit_move_line.debit,
                        'select_amount': True,
                        'amount_selected': deposit_move_line.debit,
                    }
                    deposit_ids.append(deposit_dict)
            if withdrawal_journal_items:
                for withdraw_move_line in move_line_pool.browse(cr, uid, withdrawal_journal_items, context=context):
                    withdraw_dict = { 
                        'move_line_id': withdraw_move_line.id,
                        'remark':  withdraw_move_line.name,
                        'original_amount': withdraw_move_line.credit,
                        'select_amount': True,
                        'amount_selected': withdraw_move_line.credit,
                    }
                    withdrawal_ids.append(withdraw_dict)
            if warning_msgs:
                warning = {
                           'title': _('Warning!'),
                           'message' : warning_msgs
                        }
            res.update({'deposit_ids': deposit_ids, 'withdrawal_ids': withdrawal_ids})
        else:
            res.update({'deposit_ids': deposit_ids, 'withdrawal_ids': withdrawal_ids})
        return {'value': res, 'warning': warning}
    
    def create(self, cr, uid, vals, context=None):
        result = super(bank_status_report, self).create(cr, uid, vals, context=context)
        bank_obj = self.browse(cr, uid, result, context=context)
        if not vals.get('deposit_ids') and vals.get('account_id'):
            deposit_ids = []
            for deposit in bank_obj.deposit_ids:
                deposit_ids.append(deposit.id)
            self.pool.get('bank.status.deposit').unlink(cr, uid, deposit_ids, context=context)
        if not vals.get('withdrawal_ids') and vals.get('account_id'):
            withdrawal_ids = []
            for withdraw in bank_obj.withdrawal_ids:
                withdrawal_ids.append(withdraw.id)
            self.pool.get('bank.status.withdraw').unlink(cr, uid, withdrawal_ids, context=context)
        return result
    
    def write(self, cr, uid, ids, vals, context=None):
        result = super(bank_status_report, self).write(cr, uid, ids, vals, context=context)
        bank_objs = self.browse(cr, uid, ids, context=context)
        for bank_obj in bank_objs:
            if not vals.get('deposit_ids') and vals.get('account_id'):
                deposit_ids = []
                for deposit in bank_obj.deposit_ids:
                    deposit_ids.append(deposit.id)
                self.pool.get('bank.status.deposit').unlink(cr, uid, deposit_ids, context=context)
            if not vals.get('withdrawal_ids') and vals.get('account_id'):
                withdrawal_ids = []
                for withdraw in bank_obj.withdrawal_ids:
                    withdrawal_ids.append(withdraw.id)
                self.pool.get('bank.status.withdraw').unlink(cr, uid, withdrawal_ids, context=context)
        return result
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
bank_status_report()

class bank_status_deposit(osv.osv):
    _name = "bank.status.deposit"
    _description = "Bank Status Deposit"
    _order = "id desc"
    _rec_name = 'move_line_id'
    
    _columns = { 
                'bank_status_id': fields.many2one('bank.status.report','Bank Status'),
                'move_line_id': fields.many2one('account.move.line','Voucher'),
                'remark': fields.char('Remark'),
                'original_amount': fields.float('Original Amount'),
                'select_amount': fields.boolean('Selected'),
                'amount_selected': fields.float('Selected Amount'),
                }
    
    _defaults = {
        'select_amount': True,
    }
    
    def onchange_move_line_id(self, cr, uid, ids, move_line_id, select_amount, original_amount, context=None):
        res = {}
        line_ids = []
        move_line_pool = self.pool.get('account.move.line')
        if move_line_id:
            move_line_obj = move_line_pool.browse(cr, uid, move_line_id, context=context)
            res.update({'remark': move_line_obj.name, 'original_amount': move_line_obj.debit})
            original_amount = move_line_obj.debit
        if select_amount:
            res.update({'amount_selected': original_amount})
        else:
            res.update({'amount_selected': 0.0})
        return {'value': res}
    
    def onchange_select_amount(self, cr, uid, ids, select_amount, original_amount, context=None):
        res = {}
        line_ids = []
        if select_amount:
            res.update({'amount_selected': original_amount or 0.0})
        else:
            res.update({'amount_selected': 0.0})
        return {'value': res}
    
bank_status_deposit()

class bank_status_withdraw(osv.osv):
    _name = "bank.status.withdraw"
    _description = "Bank Status Withdrawal"
    _order = "id desc"
    _rec_name = 'move_line_id'
    
    _columns = { 
                'bank_status_id': fields.many2one('bank.status.report','Bank Status'),
                'move_line_id': fields.many2one('account.move.line','Voucher'),
                'remark': fields.char('Remark'),
                'original_amount': fields.float('Original Amount'),
                'select_amount': fields.boolean('Selected'),
                'amount_selected': fields.float('Selected Amount'),
                }
    
    _defaults = {
        'select_amount': True,
    }
    
    def onchange_move_line_id(self, cr, uid, ids, move_line_id, select_amount, original_amount, context=None):
        res = {}
        line_ids = []
        move_line_pool = self.pool.get('account.move.line')
        if move_line_id:
            move_line_obj = move_line_pool.browse(cr, uid, move_line_id, context=context)
            res.update({'remark': move_line_obj.name, 'original_amount': move_line_obj.credit})
            original_amount = move_line_obj.credit
        if select_amount:
            res.update({'amount_selected': original_amount})
        else:
            res.update({'amount_selected': 0.0})
        return {'value': res}
    
    def onchange_select_amount(self, cr, uid, ids, select_amount, original_amount, context=None):
        res = {}
        line_ids = []
        if select_amount:
            res.update({'amount_selected': original_amount or 0.0})
        else:
            res.update({'amount_selected': 0.0})
        return {'value': res}
    
bank_status_withdraw()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
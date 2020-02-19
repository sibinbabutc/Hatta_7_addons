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
import datetime
import time
from datetime import datetime, timedelta, date

class telephone_expense(osv.osv):
    _name = "telephone.expense"
    _description = "Telephone Expense"
    _order = "id desc"
    
    _month_selection = [('01','January'), ('02','February'), ('03','March'), ('04','April'),
                        ('05','May'), ('06','June'), ('07','July'), ('08','August'), 
                        ('09','September'),('10','October'), ('11','November'), ('12','December')
                        ]
    
    def _default_month(self, cr, uid, context=None):
        if context is None:
            context = {}
        month = "{0:0=2d}".format(datetime.now().month)
        if month:
            return str(month)
        return False
    
    def _default_year(self, cr, uid, context=None):
        if context is None:
            context = {}
        year = datetime.now().year
        return year
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for expense_obj in self.browse(cr, uid, ids, context=context):
            total_amount = 0.0
            total_prev_month_balance = 0.0
            total_prev_month_increase = 0.0
            total_prev_month_decrease = 0.0
            net_prev_month_increase = 0.0
            res[expense_obj.id] = {
                'total_amount': 0.0,
                'total_prev_month_balance': 0.0,
                'total_prev_month_increase': 0.0,
                'total_prev_month_decrease': 0.0,
                'net_prev_month_increase': 0.0
            }
            for expense_line_obj in expense_obj.expense_line_ids:
                total_amount += expense_line_obj.total_amount
                total_prev_month_balance += expense_line_obj.prev_month_balance
                total_prev_month_increase += expense_line_obj.prev_month_increase
                total_prev_month_decrease += expense_line_obj.prev_month_decrease
            net_prev_month_increase = total_prev_month_increase - total_prev_month_decrease
            res[expense_obj.id]['total_amount'] = total_amount
            res[expense_obj.id]['total_prev_month_balance'] = total_prev_month_balance
            res[expense_obj.id]['total_prev_month_increase'] = total_prev_month_increase
            res[expense_obj.id]['total_prev_month_decrease'] = total_prev_month_decrease
            res[expense_obj.id]['net_prev_month_increase'] = net_prev_month_increase
        return res
    
    def _total_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for expense_obj in self.browse(cr, uid, ids, context=context):
            account_total_value = 0.0
            group_total_value = 0.0
            res[expense_obj.id] = {
                'account_total_value': 0.0,
                'group_total_value': 0.0,
            }
            for account_line_obj in expense_obj.account_allocation_ids:
                account_total_value += account_line_obj.value
            for group_line_obj in expense_obj.group_allocation_ids:
                group_total_value += group_line_obj.value
            res[expense_obj.id]['account_total_value'] = account_total_value
            res[expense_obj.id]['group_total_value'] = group_total_value
        return res
    
    def _get_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        name_prefix = 'Telephone Expense for '
        name = ''
        for expense in self.browse(cr, uid, ids, context=context):
            name_prefix = 'Telephone Expense for '
            if expense.service_provider_id:
                name_prefix += '('+ expense.service_provider_id.name + ') '
            if expense.month:
                month = dict(self.pool.get('telephone.expense').fields_get(cr, uid, allfields=['month'], context=context)['month']['selection'])[expense.month]
                name_prefix += '('+ month + ') '
            if expense.year:
                name_prefix += '('+ str(expense.year) + ') '
            if expense.sequence:
                name = name_prefix + str(expense.sequence)
            else:
                name = name_prefix
            res[expense.id] = name
        return res
    
    _columns = { 
                'name': fields.function(_get_name, string='Name',type='char'),
                'sequence': fields.char('Sequence'),
                'year': fields.integer('Year'),
                'month': fields.selection(selection=_month_selection,  string='Month'),
                'prev_year': fields.integer('Previous Year'),
                'prev_month': fields.selection(selection=_month_selection,  string='Previous Month'),
                'service_provider_id': fields.many2one('tel.service.provider', 'Service Provider'),
                'partner_id': fields.many2one('res.partner', 'Party'),
                'expense_line_ids': fields.one2many('telephone.expense.line', 'expense_id', 'Expense Lines'),
                'account_allocation_ids': fields.one2many('tel.account.allocation', 'expense_id', 'Account Allocation', copy=False),
                'group_allocation_ids': fields.one2many('tel.group.allocation', 'expense_id', 'Group Allocation', copy=False),
                'state': fields.selection(string='Status',selection=[('draft','Draft'),
                                                            ('confirm','Confirmed'),
                                                            ('validated','Validated')], copy=False),
                'total_amount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Amount',
                                                multi='sums', help="The total amount."),
                'total_prev_month_balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Previous Month Balance',
                                                multi='sums'),
                'total_prev_month_increase': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Increase Over Previous Month',
                                                multi='sums'),
                'total_prev_month_decrease': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Decrease Over Previous Month',
                                                multi='sums'),
                'net_prev_month_increase': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Net Increase Over Previous Month',
                                                multi='sums'),
                'account_total_value': fields.function(_total_value, digits_compute=dp.get_precision('Account'), string='Total Account Value',
                                                multi='value'),
                'group_total_value': fields.function(_total_value, digits_compute=dp.get_precision('Account'), string='Total Group Value',
                                                multi='value'),
                'journal_id': fields.many2one('account.journal', 'Posting Journal'),
                'account_id': fields.many2one('account.account', 'Credit Account'),
                'posted_move_id': fields.many2one('account.move', 'Posted Voucher', copy=False),
                'payment_move_id': fields.many2one('account.move', 'Payment Voucher', copy=False),
                'notes': fields.text('Notes'),
                'check_no': fields.related('payment_move_id','ref', type='char', size=64, store=True, string='Check No', copy=False),
                'bank_journal_id': fields.related('payment_move_id', 'journal_id', type='many2one', relation='account.journal', string='Bank', copy=False),
                'remarks': fields.char('Remarks'),
                'loaded_accounts_groups': fields.boolean('Loaded Accounts and Group Info', copy=False),
                'compared_prev_month': fields.boolean('Compared With Previos Month', copy=False),
        }
    
    _defaults = { 
                'state': 'draft',
                'month': _default_month,
                'year': _default_year,
        }
    
    def _check_sp_year_month(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=context):
            enpense_ids = self.search(cr, uid, [('service_provider_id','=',expense.service_provider_id.id),
                                       ('year','=',expense.year),
                                       ('month','=',expense.month)], context=context)
            if len(enpense_ids) > 1:
                return False
        return True
    
    _constraints = [
        (_check_sp_year_month, 'Expense should be Unique for a month, year and service provider!', ['service_provider_id','year','month']),
    ]
    
    def create(self, cr, uid, vals, context=None):
        vals.update({'sequence': self.pool.get('ir.sequence').get(cr, uid, 'tel.expense') or '/'})
        result = super(telephone_expense, self).create(cr, uid, vals, context=context)
        return result
    
    def copy(self, cr, uid, id, default=None, context=None):
        default['posted_move_id'] = False
        default['payment_move_id'] = False
        default['check_no'] = False
        default['bank_journal_id'] = False
        default['loaded_accounts_groups'] = False
        default['compared_prev_month'] = False
#         default['service_provider_id'] = False
        default['account_allocation_ids'] = []
        default['group_allocation_ids'] = []
        res = super(telephone_expense, self).copy(cr, uid, id, default, context=context)
        return res
    
    def onchange_service_provider_id(self, cr, uid, ids, service_provider_id, context=None):
        res = {}
        line_ids = []
        directory_pool = self.pool.get('telephone.directory')
        if service_provider_id:
            sp_obj = self.pool.get('tel.service.provider').browse(cr, uid, service_provider_id, context=context)
            partner_id = sp_obj.partner_id and sp_obj.partner_id.id or False
            directory_ids = directory_pool.search(cr, uid, [('service_provider_id','=',service_provider_id)])
            if directory_ids:
                sl_no = 1
                for directory in directory_pool.browse(cr, uid, directory_ids, context=context):
                    line_dict = { 
                        'directory_id': directory.id,
                        'sl_no':  sl_no,
                        'mobile': directory.mobile,
                        'allowed_amount': directory.allowed_amount,
                    }
                    sl_no += 1
                    line_ids.append(line_dict)
            res.update({'partner_id': partner_id, 'expense_line_ids': line_ids})
        return {'value': res}
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
    def button_compare_prev_month(self, cr, uid, ids, context=None):
        expense_line_pool = self.pool.get('telephone.expense.line')
        for expense_obj in self.browse(cr, uid, ids, context=context):
            prev_expense_ids = self.search(cr, uid, [('service_provider_id', '=', expense_obj.service_provider_id.id),
                                                     ('month', '=', expense_obj.prev_month),
                                                     ('year', '=', expense_obj.prev_year)])
            for prev_obj in self.browse(cr, uid, prev_expense_ids, context=context):
                for prev_line in prev_obj.expense_line_ids:
                    expense_line_ids = expense_line_pool.search(cr, uid, [('expense_id', '=', expense_obj.id),
                                                                          ('directory_id', '=', prev_line.directory_id.id)])
                    if expense_line_ids:
                        expense_line_id = expense_line_ids and expense_line_ids[0]
                        expense_line_obj = expense_line_pool.browse(cr, uid, expense_line_id, context=context)
                        expense_line_obj.write({'prev_month_balance': prev_line.balance})
                    else:
                        if prev_line.remarks:
                            remarks = 'Remarks: ' + prev_line.remarks
                        else:
                            remarks = ''
                        line_dict = {
                            'expense_id': expense_obj.id,
                            'directory_id': prev_line.directory_id.id,
                            'sl_no':  prev_line.sl_no,
                            'mobile': prev_line.mobile,
                            'total_amount': prev_line.total_amount,
                            'allowed_amount': prev_line.allowed_amount,
                            'deduction': prev_line.deduction,
                            'prev_month_balance': prev_line.balance,
                            'remarks': "From Previous Expense. "+ remarks
                        }
                        expense_line_pool.create(cr, uid, line_dict, context=context)
            expense_obj.write({'compared_prev_month': True})
        return True
    
    def button_action_confirm(self, cr, uid, ids, context=None):
        for expense_obj in self.browse(cr, uid, ids, context=context):
            expense_obj.write({'state': 'confirm'})
        return True
    
    def button_print_expense_report(self, cr, uid, ids, context=None): 
        if context is None:
           context = {}
        record_ids = ids
        report = {
           'type' : 'ir.actions.report.xml',
           'datas': {
               'model':'telephone.expense',
               'id': context.get('active_ids') and context.get('active_ids')[0] or False,
               'ids': context.get('active_ids') and context.get('active_ids') or [],
               'report_type': 'pdf',
               'form': record_ids,
               
               },
           'report_name': 'telephone_expense_jasper',
           'nodestroy': False
        }
        #print '>' * 333, report
        return report
    
    def _unlink_accounts_groups(self, cr, uid, expense_obj, context=None):
        account_info_pool = self.pool.get('tel.account.allocation')
        group_info_pool = self.pool.get('tel.group.allocation')
        account_info_ids = []
        group_info_ids = []
        if expense_obj:
            if expense_obj.account_allocation_ids:
                for account_line in expense_obj.account_allocation_ids:
                    account_info_ids.append(account_line.id)
                if account_info_ids:
                    account_info_pool.unlink(cr, uid, account_info_ids, context=context)
            if expense_obj.group_allocation_ids:
                for group_line in expense_obj.group_allocation_ids:
                    group_info_ids.append(group_line.id)
                if group_info_ids:
                    group_info_pool.unlink(cr, uid, group_info_ids, context=context)
        return True
    
    def _get_percentages(self, cr, uid, account_info_list, group_info_list, account_total, group_total, context=None):
        account_info_pool = self.pool.get('tel.account.allocation')
        group_info_pool = self.pool.get('tel.group.allocation')
        if account_info_list:
            for account_line in account_info_pool.browse(cr, uid, account_info_list, context=context):
                if account_total!=0:
                    percentage = (account_line.value/account_total) * 100
                    account_line.write({'percentage': percentage})
        if group_info_list:
            for group_line in group_info_pool.browse(cr, uid, group_info_list, context=context):
                if group_total!=0:
                    percentage = (group_line.value/group_total) * 100
                    group_line.write({'percentage': percentage})
        return True
    
    def button_load_account_group_info(self, cr, uid, ids, context=None):
        directory_pool = self.pool.get('telephone.directory')
        account_info_pool = self.pool.get('tel.account.allocation')
        group_info_pool = self.pool.get('tel.group.allocation')
        account_info_list = []
        group_info_list = []
        account_total = 0.0
        group_total = 0.0
        for expense_obj in self.browse(cr, uid, ids, context=context):
            if expense_obj.account_allocation_ids or expense_obj.group_allocation_ids:
                self._unlink_accounts_groups(cr, uid, expense_obj, context=None)
            
            for line in expense_obj.expense_line_ids:
                for account_line in line.directory_id.account_allocation_ids:
                    value = 0.0
                    analytic_account_id = account_line.analytic_account_id and account_line.analytic_account_id.id or False
                    account_info_ids = account_info_pool.search(cr, uid, [('expense_id','=',expense_obj.id),
                                                                          ('account_id','=',account_line.account_id.id),
                                                                          ('analytic_account_id','=',analytic_account_id)])
                    if account_info_ids:
                        account_info_id = account_info_ids and account_info_ids[0]
                        account_info_obj = account_info_pool.browse(cr, uid, account_info_id, context=context)
                        new_value = line.balance * (account_line.percentage/100)
                        value = account_info_obj.value + new_value
                        account_info_obj.write({'value': value})
                        account_total += new_value
                    else:
                        value = line.balance * (account_line.percentage/100)
                        account_info_dict = {
                            'account_id': account_line.account_id and account_line.account_id.id or False,
                            'analytic_account_id': analytic_account_id,
                            'value': value,
                            'expense_id': expense_obj.id
                        }
                        account_info_list.append(account_info_pool.create(cr, uid, account_info_dict, context=context))
                        account_total += value
                for group_line in line.directory_id.group_allocation_ids:
                    group_info_ids = group_info_pool.search(cr, uid, [('expense_id','=',expense_obj.id),
                                                                      ('group_id','=',group_line.group_id.id)])
                    value = 0.0
                    if group_info_ids:
                        group_info_id = group_info_ids and group_info_ids[0]
                        group_info_obj = group_info_pool.browse(cr, uid, group_info_id, context=context)
                        new_value = line.balance * (group_line.percentage/100)
                        value = group_info_obj.value + new_value
                        group_info_obj.write({'value': value})
                        group_total += new_value
                    else:
                        value = line.balance * (group_line.percentage/100)
                        group_info_dict = {
                            'group_id': group_line.group_id and group_line.group_id.id or False,
                            'value': value,
                            'expense_id': expense_obj.id
                        }
                        group_info_list.append(group_info_pool.create(cr, uid, group_info_dict, context=context))
                        group_total += value
            expense_obj.write({'loaded_accounts_groups': True})
            self._get_percentages(cr, uid, account_info_list, group_info_list, account_total, group_total, context=context)
        return True
    
    def line_get_convert(self, cr, uid, x, part, date, context=None):
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'analytic_account_id': x.get('account_analytic_id', False),
        }
    
    def _create_account_move_line(self, cr, uid, expense_obj, context=None):
        """
        Generate the account.move.line values.
        """
        partner_id = expense_obj.partner_id and expense_obj.partner_id.id or False
        move_line_pool = self.pool.get('account.move.line')
        line_data = []
        line_ids = []
        for account_line in expense_obj.account_allocation_ids:
            debit_line_vals = {
                        'type': 'src',
                        'name': 'CASH',
                        'ref': account_line.directory_id and account_line.directory_id.name or False,
                        'partner_id': partner_id,
#                         'debit': account_line.value,
                        'price': account_line.value,
                        'account_id': account_line.account_id and account_line.account_id.id or False,
                        'account_analytic_id': account_line.analytic_account_id and account_line.analytic_account_id.id or False,
            }
            line_data.append(debit_line_vals)
        credit_line_vals = {
                    'type': 'dest',
                    'name': expense_obj.name,
                    'ref': expense_obj.name or False,
                    'date_maturity': time.strftime('%Y-%m-%d'),
                    'partner_id': partner_id,
                    'price': -(expense_obj.account_total_value),
#                     'credit': expense_obj.account_total_value,
                    'account_id': expense_obj.account_id and expense_obj.account_id.id,
        }
        line_data.append(credit_line_vals)
        line = [(0, 0, self.line_get_convert(cr, uid, l, expense_obj.partner_id.id, time.strftime('%Y-%m-%d'))) for l in line_data]
        return line
    
    def button_create_account_move(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for expense_obj in self.browse(cr, uid, ids, context=context):
            today = datetime.today()
            ctx = dict(context or {}, account_period_prefer_normal=True)
            period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
            period_id = period_ids and period_ids[0] or False
            move_lines = self._create_account_move_line(cr, uid, expense_obj, context)
            move_id = move_pool.create(cr, uid,
                {
                 'journal_id': expense_obj.journal_id.id,
                 'line_id': move_lines,
                 'ref': expense_obj.name or '',
                 'date': today,
                 'period_id': period_id,
                 }, context=context)
            expense_obj.write({'state': 'validated', 'posted_move_id': move_id})
        return True
    
telephone_expense()

class telephone_expense_line(osv.osv):
    _name = "telephone.expense.line"
    _description = "Telephone Expense Line"
    _rec_name = 'directory_id'
    
    def _compute_balance(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            prev_month_balance = 0.0
            prev_month_increase = 0.0
            prev_month_decrease = 0.0
            balance = line.total_amount - line.deduction
            res[line.id] = {
                            'balance': balance,
                            }
            prev_month_balance = balance - line.prev_month_balance
            if prev_month_balance < 0.0:
                prev_month_decrease = abs(prev_month_balance)
            else:
                prev_month_increase = prev_month_balance
            res[line.id] = {
                            'balance': balance,
                            'prev_month_decrease': prev_month_decrease,
                            'prev_month_increase': prev_month_increase,
                            }
            
        return res
    
    _columns = { 
                'expense_id': fields.many2one('telephone.expense', 'Telephone Expense'),
                'directory_id': fields.many2one('telephone.directory', 'Name'),
                'sl_no': fields.integer('Sl No'),
                'mobile': fields.char('Mobile No'),
                'total_amount': fields.float('Total Amount'),
                'allowed_amount': fields.float('Allowed Amount'),
                'deduction': fields.float('Deduction'),
                'balance': fields.function(_compute_balance, string='Balance', digits_compute= dp.get_precision('Account'), multi='subtotal'),
                'remarks': fields.char('Remarks'),
                'prev_month_balance': fields.float('Previous Month Balance'),
                'prev_month_increase': fields.function(_compute_balance, string='Increase Over Previous Month', digits_compute= dp.get_precision('Account'), multi='subtotal'),
                'prev_month_decrease': fields.function(_compute_balance, string='Decrease Over Previous Month', digits_compute= dp.get_precision('Account'), multi='subtotal'),
        }
    
    def onchange_directory_id(self, cr, uid, ids, directory_id, context=None):
        value = {}
        if directory_id:
            tel_directory_obj = self.pool.get('telephone.directory').browse(cr, uid, directory_id, context=context)
            mobile = tel_directory_obj.mobile
            allowed_amount = tel_directory_obj.allowed_amount
            value.update({'mobile': mobile, 'allowed_amount': allowed_amount})
        return {'value': value}

telephone_expense_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
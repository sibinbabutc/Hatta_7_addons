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

from datetime import datetime
import openerp.addons.decimal_precision as dp
from tools.translate import _

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    def _get_emp_contract(self, cr, uid, ids, fields, args, context=None):
        res = {}
        today = datetime.today()
        contract_pool = self.pool.get('hr.contract')
        for employee in self.browse(cr, uid, ids, context=context):
            domain = []
            res[employee.id] = False
            domain.append(('employee_id', '=', employee.id))
            if employee.contract_id.date_start:
                domain.append(('date_start', '<=', today))
            if employee.contract_id.date_end:
                domain.append(('date_end', '>=', today))
            contract_ids = contract_pool.search(cr, uid, domain, context=context)
            if contract_ids:
                if employee.last_working_date:
                    emp_last_date = datetime.strptime(employee.last_working_date, "%Y-%m-%d")
                    if emp_last_date > today:
                        res[employee.id] = employee.contract_id.id
                    else:
                        res[employee.id] = False
                else:
                    res[employee.id] = contract_ids[0]
        return res
    
    def _get_employee_details(self, cr, uid, ids, context=None):
        employee_ids = []
        for contract in self.browse(cr, uid, ids, context=context):
            employee_ids.append(contract.employee_id.id)
        return employee_ids
    
    
    _columns = {
                'sal_transfer_mode': fields.selection([('WPS', 'WPS'),
                                                       ('CHQ', 'Cheque')],
                                                      'Salary Payment Mode'),
                'last_working_date' : fields.date('Last Working Date'),
                'contract' : fields.function(_get_emp_contract, type="many2one",
                                             relation="hr.contract", string="Contract",
                                             store={
                                                    'hr.employee': (lambda self, cr, uid, ids, c={}: ids, ['last_working_date'], 20),
                                                    'hr.contract': (_get_employee_details, ['date_start','date_end'], 20),
                                                    })
                }

    def create(self, cr, uid, data, context=None):
        vals={
            'name': data['name'],
            'partner_ac_code': data.get('emp_no', ''),
            'customer' : False,
            'supplier' : False,
            'is_employee' : True
            }
        partner_id = self.pool.get('res.partner').create(cr, uid, vals, context=context)
        data.update({
            'address_home_id': partner_id
                     })
        employee_id = super(hr_employee, self).create(cr, uid, data, context=context)
        return employee_id
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('name', False) or vals.get('emp_no', False):
            partner_vals = {}
            if vals.get('name', False):
                partner_vals.update({'name': vals['name']})
            if vals.get('emp_no', False):
                partner_vals.update({'partner_ac_code': vals['emp_no']})
            for emp in self.browse(cr, uid, ids, context=context):
                if emp.address_home_id:
                    emp.address_home_id.write(partner_vals)
        return super(hr_employee, self).write(cr, uid, ids, vals, context=context)

hr_employee()

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    def _get_total_days(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for payslip in self.browse(cr, uid, ids, context=context):
            from_date = payslip.date_from
            to_date = payslip.date_to
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
            days = ((to_date - from_date).days) + 1
            res[payslip.id] = days
        return res
    
    def compute_sheet(self, cr, uid, ids, context=None):
        payslip_sal_pool = self.pool.get('payslip.salary.structure')
        for payslip in self.browse(cr, uid, ids, context=context):
            payslip_sal_ids = payslip_sal_pool.search(cr, uid, [('payslip_id', '=', payslip.id)],
                                                      context=context)
            payslip_sal_pool.unlink(cr, uid, payslip_sal_ids, context=context)
            lines = []
            if payslip.contract_id:
                for sal_line in payslip.contract_id.sal_ids:
                    vals = {
                            'categ_id': sal_line.categ_id.id,
                            'amount': sal_line.amount or 0.00
                            }
                    lines.append((0, 0, vals))
            payslip.write({'sal_ids': lines})
        res = super(hr_payslip, self).compute_sheet(cr, uid, ids, context=context)
        return res
    
    def onchange_leave_sal(self, cr, uid, ids, contract_id=False, context=None):
        res = {'value': {}}
        contract_pool = self.pool.get('hr.contract')
        if contract_id:
            contract_obj = contract_pool.browse(cr, uid, contract_id, context=context)
            res['value']['last_leave_date'] = contract_obj.last_leave_date
            res['value']['leave_base_amt'] = contract_obj.wage
        return res
    
    def onchange_leave_sal_ids(self, cr, uid, ids, leave_sal_ids, contract_id, context=None):
        res={'value':{}}
        amt = 0
        contract_pool = self.pool.get('hr.contract')
        if contract_id:
            contract_obj = contract_pool.browse(cr, uid, contract_id, context=context)
            amt = contract_obj.wage
        for sal in self.pool.get('employee.salary.structure').browse(cr, uid, leave_sal_ids[0][2], context=context):
            amt +=sal.amount or 0.00
            res['value']['leave_base_amt'] = amt
        return res
    
    def onchange_leave_from(self, cr, uid, ids, leave_from, last_leave_date,  context=None):
        res={'value':{}}
        date_from = last_leave_date
        date_to = leave_from
        days = (datetime.strptime(date_to, "%Y-%m-%d") - datetime.strptime(date_from, "%Y-%m-%d")).days
        res['value']['days_after_leave'] = days
        return res
    
    def _get_leave_salary(self, cr, uid, ids, fields, args, context=None):
        res={}
        for payslip in self.browse(cr, uid, ids, context=context):
            leave_amount = 0.00
            if payslip.leave_sal:
                base_amt = payslip.leave_base_amt
                leave_amount = round((base_amt / 30.00) * payslip.leave_sal_eligible_for)
            res[payslip.id] = leave_amount
        return res
    
#     def _get_days_after_leave(self, cr, uid, ids, fields, args, context=None):
#         res = {}
#         for payslip in self.browse(cr, uid, ids, context=context):
#             days = 0.00
#             if payslip.leave_sal:
#                 date_from = payslip.last_leave_date
#                 date_to = payslip.leave_from
#                 days = (datetime.strptime(date_to, "%Y-%m-%d") - datetime.strptime(date_from, "%Y-%m-%d")).days
#             res[payslip.id] = days
#         return res
    
    def _get_advance_balance(self, cr, uid, ids, fields, args, context=None):
        res = {}
        icp = self.pool.get('ir.config_parameter')
        move_line_pool = self.pool.get('account.move.line')
        account_id = icp.get_param(cr, uid, 'hatta_hr_management.emp_adv_account_id', False)
        for payslip in self.browse(cr, uid, ids, context=context):
            avoid_move_ids = []
            if payslip.move_id:
                avoid_move_ids = [payslip.move_id.id]
            amount = 0.00
            if account_id:
                domain = [('account_id', '=', int(account_id)),
                          ('partner_id', '=', payslip.employee_id.address_home_id.id),
                          ('date', '<=', payslip.date_to)]
                if avoid_move_ids:
                    domain.append(('move_id', '!=', avoid_move_ids))
                move_line_ids = move_line_pool.search(cr, uid, domain, context=context)
                for move_line_obj in move_line_pool.browse(cr, uid, move_line_ids, context=context):
                    balance = move_line_obj.debit - move_line_obj.credit
                    amount += balance
            res[payslip.id] = amount
        return res
    
    def _get_leave_sal_ele(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for payslip in self.browse(cr, uid, ids, context=context):
            actual_wking_days = payslip.days_after_leave
            res[payslip.id] = round((30.00 / 365.00) * actual_wking_days)
        return res
    
    def onchange_days_after_leave(self, cr, uid, ids, leave_sal, days_after_leave,
                                  context=None):
        res = {'value': {}}
        if leave_sal:
            res['value']['leave_sal_eligible_for'] = (30.00 / 365.00) * days_after_leave
        return res
    
    _columns = {
                'total_days': fields.function(_get_total_days, type="float",
                                              string="Total Days",
                                              store={
                                                     'hr.payslip': (lambda self, cr, uid, ids, c={}: ids, ['date_from', 'date_to'], 20),
                                                     }),
                'days_payable': fields.float('Days Payable'),
                'leave_days': fields.float('Days Leave'),
                'sick_leave': fields.float('Sick Leave'),
                'sal_advance': fields.float('Salary Advance', digits_compute=dp.get_precision('Account')),
                'advance_ids': fields.one2many('employee.sal.advances', 'payslip_id',
                                               'Advances'),
                'other_allow_ids': fields.one2many('employee.other.allowances', 'payslip_id',
                                                   'Other Allowances'),
                'overtime_normal': fields.float('Normal Overtime(Hours)'),
                'holiday_overtime': fields.float('Holiday Overtime(Hours)'),
                'holiday_worked': fields.float('Holiday Worked'),
#                 'advance_balance': fields.float('Balance Advance',
#                                                 digits_compute=dp.get_precision('Account')),
                'advance_balance': fields.function(_get_advance_balance, type="float",
                                                   digits_compute=dp.get_precision('Account'),
                                                   string="Balance Advance"),
                'advance_ded': fields.float('Advance Deduction',
                                            digits_compute=dp.get_precision('Account')),
                'tel_deduction': fields.float('Telephone Deduction',
                                              digits_compute=dp.get_precision('Account')),
                'sal_ids': fields.one2many('payslip.salary.structure', 'payslip_id',
                                           'Salary Structure'),
                'notes' : fields.text('Notes'),
                'leave_sal': fields.boolean('Leave Salary'),
                'leave_from': fields.date('Leave From'),
                'leave_to': fields.date('Leave To'),
                'last_leave_date': fields.date('Last Leave Date'),
                'days_after_leave' : fields.float('Actual Working Days',
                                                  digits_compute=dp.get_precision('Account')),
#                 'days_after_leave': fields.function(_get_days_after_leave, type="float",
#                                                     string="Days After Last Leave"),
                'leave_sal_ids' : fields.many2many('employee.salary.structure', 'leave_salary_rel', 'leave_id', 'salary_id',
                                                   string="Leave Salary Details"),
                'leave_sal_eligible_for': fields.function(_get_leave_sal_ele,
                                                          string='Leave Salary Eligible For',
                                                          type="float"),
                'leave_base_amt' : fields.float('Leave Salary Base Amount', digits_compute=dp.get_precision('Account')),
                'leave_salary' : fields.function(_get_leave_salary, type='float', string="Leave Salary"),
                'date_of_rejoining': fields.date('Date of Re-joining After Last Leave'),
                'less_availed': fields.integer('Less : Already Availed'),
                'actual_leave_days': fields.integer('Actual Leave Days'),
                'leave_encashed': fields.integer('Leaves Encashed'),
                }
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True
    
#     def process_sheet(self, cr, uid, ids, context=None):
#         move_pool = self.pool.get('account.move')
#         period_pool = self.pool.get('account.period')
#         precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Payroll')
#         move = {
#                 'ref': name,
#                 'date': timenow,
#                 'ref': slip.number,
#                 'journal_id': slip.journal_id.id,
#                 'period_id': period_id,
#                 }
#         for slip in self.browse(cr, uid, ids, context=context):
#             line_ids = []
#             debit_sum = 0.0
#             credit_sum = 0.0
#             if not slip.period_id:
#                 ctx = dict(context or {}, account_period_prefer_normal=True)
#                 search_periods = period_pool.find(cr, uid, slip.date_to, context=ctx)
#                 period_id = search_periods[0]
#             else:
#                 period_id = slip.period_id.id
# 
#             default_partner_id = slip.employee_id.address_home_id.id
#             move = {
#                 'narration': name,
#                 'date': timenow,
#                 'ref': slip.number,
#                 'journal_id': slip.journal_id.id,
#                 'period_id': period_id,
#             }
#             for line in slip.details_by_salary_rule_category:
#                 amt = slip.credit_note and -line.total or line.total
#                 partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
#                 debit_account_id = line.salary_rule_id.account_debit.id
#                 credit_account_id = line.salary_rule_id.account_credit.id
# 
#                 if debit_account_id:
# 
#                     debit_line = (0, 0, {
#                     'name': line.name,
#                     'date': timenow,
#                     'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_debit.type in ('receivable', 'payable')) and partner_id or False,
#                     'account_id': debit_account_id,
#                     'journal_id': slip.journal_id.id,
#                     'period_id': period_id,
#                     'debit': amt > 0.0 and amt or 0.0,
#                     'credit': amt < 0.0 and -amt or 0.0,
#                     'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
#                     'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
#                     'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
#                 })
#                     line_ids.append(debit_line)
#                     debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
# 
#                 if credit_account_id:
# 
#                     credit_line = (0, 0, {
#                     'name': line.name,
#                     'date': timenow,
#                     'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_credit.type in ('receivable', 'payable')) and partner_id or False,
#                     'account_id': credit_account_id,
#                     'journal_id': slip.journal_id.id,
#                     'period_id': period_id,
#                     'debit': amt < 0.0 and -amt or 0.0,
#                     'credit': amt > 0.0 and amt or 0.0,
#                     'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
#                     'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
#                     'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
#                 })
#                     line_ids.append(credit_line)
#                     credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
# 
#             if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
#                 acc_id = slip.journal_id.default_credit_account_id.id
#                 if not acc_id:
#                     raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
#                 adjust_credit = (0, 0, {
#                     'name': _('Adjustment Entry'),
#                     'date': timenow,
#                     'partner_id': False,
#                     'account_id': acc_id,
#                     'journal_id': slip.journal_id.id,
#                     'period_id': period_id,
#                     'debit': 0.0,
#                     'credit': debit_sum - credit_sum,
#                 })
#                 line_ids.append(adjust_credit)
# 
#             elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
#                 acc_id = slip.journal_id.default_debit_account_id.id
#                 if not acc_id:
#                     raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
#                 adjust_debit = (0, 0, {
#                     'name': _('Adjustment Entry'),
#                     'date': timenow,
#                     'partner_id': False,
#                     'account_id': acc_id,
#                     'journal_id': slip.journal_id.id,
#                     'period_id': period_id,
#                     'debit': credit_sum - debit_sum,
#                     'credit': 0.0,
#                 })
#                 line_ids.append(adjust_debit)
#             move.update({'line_id': line_ids})
#             move_id = move_pool.create(cr, uid, move, context=context)
#             self.write(cr, uid, [slip.id], {'move_id': move_id, 'period_id' : period_id}, context=context)
#             if slip.journal_id.entry_posted:
#                 move_pool.post(cr, uid, [move_id], context=context)
#         return super(hr_payslip, self).process_sheet(cr, uid, [slip.id], context=context)
    
    
hr_payslip()

class hr_payslip_run(osv.osv):
    _inherit = 'hr.payslip.run'
    
    def _get_payroll_name(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for payroll in self.browse(cr, uid, ids, context=context):
            date_from = payroll.date_start
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            month = date_from_obj.strftime("%B")
            year = str(date_from_obj.strftime("%Y"))
            company_name = payroll.company_id.name or ''
            name = "SALARY FOR THE MONTH OF %s - %s (%s)"%(month.upper(), year, company_name)
            res[payroll.id] = name
        return res
    
    _columns = {
                'note': fields.text('Notes'),
                'payment_id': fields.many2one('account.move', 'Related Voucher'),
                'sal_detail_ids': fields.one2many('payroll.emp.line', 'payroll_id', 'Salary Details'),
                'gen_allowance_ids': fields.one2many('gen.employee.allowances', 'payroll_id',
                                                     'General Allowances'),
                'company_id': fields.many2one('res.company', 'Company'),
                'name': fields.function(_get_payroll_name, type="char", size=128,
                                        string="Name")
                }
    
    def view_sal_slips(self, cr, uid, ids, context=None):
        slip_ids = []
        for batch in self.browse(cr, uid, ids, context=context):
            slip_ids = [x.id for x in batch.slip_ids]
        if not slip_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("No Related Salary Slip Found !!!"))
        return {
                'domain': "[('id', 'in', "+str(slip_ids)+")]",
                'name': _('Salary Slip'),
                'view_type':'form',
                'view_mode':'tree,form',
                'res_model': 'hr.payslip',
                'type':'ir.actions.act_window',
                'context':context,
                }
    
    def update_payslip(self, cr, uid, ids, context=None):
        allowance_dict = {}
        other_dict = {}
        for payroll in self.browse(cr, uid, ids, context=context):
            for allowance in payroll.gen_allowance_ids:
                allowance_dict[allowance.id] = {
                                                'name': allowance.name or '',
                                                'amount': allowance.amount or 0.00
                                                }
            for sal_lines in payroll.sal_detail_ids:
                other_dict[sal_lines.payslip_id.id] = {
                                                       'days_payable': sal_lines.days_payable,
                                                       'sal_advance': sal_lines.sal_advance,
                                                       'sick_leave': sal_lines.sick_leave,
                                                       'overtime_normal': sal_lines.overtime_normal,
                                                       'holiday_overtime': sal_lines.holiday_overtime,
                                                       'advance_ded': sal_lines.advance_ded,
                                                       'tel_deduction': sal_lines.tel_deduction,
                                                       'holiday_worked': sal_lines.holiday_worked,
                                                       'leave_days': sal_lines.leave_days
                                                       }
            for slip in payroll.slip_ids:
                slip_vals = other_dict.get(slip.id, {})
                temp_gen_allo_dict = allowance_dict.copy()
                for allowance in slip.other_allow_ids:
                    if allowance.gen_allowance:
                        if not allowance.general_all_id:
                            allowance.unlink()
                        else:
                            vals = temp_gen_allo_dict.get(allowance.general_all_id.id, {})
                            if not vals:
                                allowance.unlink()
                            else:
                                allowance.write(vals)
                                del temp_gen_allo_dict[allowance.general_all_id.id]
                if temp_gen_allo_dict:
                    allow_lines = []
                    for gen_all in temp_gen_allo_dict:
                        vals = temp_gen_allo_dict.get(gen_all, {})
                        vals['gen_allowance'] = True
                        vals['general_all_id'] = gen_all
                        allow_lines.append((0, 0, vals))
                    slip_vals['other_allow_ids'] = allow_lines
                print slip_vals,"------------->Salip Vals"
                if slip_vals:
                    slip.write(slip_vals)
                slip.compute_sheet()
        return True
    
    def process_payroll(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        period_pool = self.pool.get('account.period')
        account_move_line = self.pool.get('account.move.line')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        icp = self.pool.get('ir.config_parameter')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        payslip_pool = self.pool.get('hr.payslip')
        netsal_code = icp.get_param(cr, uid,
                                    'hatta_hr_management.net_salary_code',
                                    False)
        sal_earned_code = icp.get_param(cr, uid,
                                        'hatta_hr_management.salary_earned_code',
                                        'False')
        allowance_code = icp.get_param(cr, uid,
                                        'hatta_hr_management.allowance_code',
                                        'False')
        overtime_code = icp.get_param(cr, uid,
                                        'hatta_hr_management.overtime_code',
                                        'False')
        advance_code = icp.get_param(cr, uid,
                                        'hatta_hr_management.salary_advance_code',
                                        'False')
        move_ids = []
        for payroll in self.browse(cr, uid, ids, context=context):
            net_amount = 0.00
            net_account_id = False
            ctx = dict(context or {}, account_period_prefer_normal=True)
            search_periods = period_pool.find(cr, uid, payroll.date_end, context=ctx)
            period_id = search_periods[0]
            if payroll.payment_id:
                move_line_ids = [x.id for x in payroll.payment_id.line_id]
                move_line_pool.unlink(cr, uid, move_line_ids, context=context)
                move_id = payroll.payment_id.id
            else:
                move_vals = {
                             'journal_id': payroll.journal_id.id,
                             'ref': payroll.name or '',
                             'date': payroll.date_end,
                             'period_id': period_id
                             }
                move_id = move_pool.create(cr, uid, move_vals, context=context)
            lines = []
            date_from = payroll.date_start
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            month = date_from_obj.strftime("%B")
            year = str(date_from_obj.strftime("%Y"))
            for slip_line in payroll.slip_ids:
                slip_line.write({'move_id': move_id})
                for line in slip_line.line_ids:
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id
                    if debit_account_id and line.total != 0.00:
                        name = line.salary_rule_id.note or ''
                        if line.code == netsal_code:
                            net_amount += line.total
                            net_account_id = debit_account_id
                            continue
                        elif line.code == sal_earned_code:
                            name = "SALARY FOR THE MONTH OF %s-%s"%(month.upper(), str(year))
                        elif line.code == overtime_code or line.code == advance_code:
                            name = "%s FOR THE MONTH OF %s-%s"%(str(name or ''), month.upper(), str(year))
                        if line.code == allowance_code:
                            for allowance in slip_line.other_allow_ids:
                                if allowance.amount != 0.00:
                                    name = allowance.name.upper()
                                    vals = {
                                            'name': name,
                                            'date': payroll.date_end,
                                            'partner_id': line.employee_id.address_home_id.id,
                                            'account_id': debit_account_id,
                                            'journal_id': payroll.journal_id.id,
                                            'period_id': period_id,
                                            'debit': allowance.amount or 0.00,
                                            'credit': 0.00,
                                            'move_id': move_id
                                            }
                                    account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
                                                                                                         debit_account_id,
                                                                                                         context=context)
                                    vals.update(account_change_onchange_data.get('value', {}))
                                    move_line_pool.create(cr, uid, vals, context=context)
                        else:
                            vals = {
                                    'name': name,
                                    'date': payroll.date_end,
                                    'partner_id': line.employee_id.address_home_id.id,
                                    'account_id': debit_account_id,
                                    'journal_id': payroll.journal_id.id,
                                    'period_id': period_id,
                                    'debit': line.total or 0.00,
                                    'credit': 0.00,
                                    'move_id': move_id
                                    }
                            account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
                                                                                                 debit_account_id,
                                                                                                 context=context)
                            vals.update(account_change_onchange_data.get('value', {}))
                            move_line_pool.create(cr, uid, vals, context=context)
                    if credit_account_id and line.total != 0.00:
                        name = line.salary_rule_id.note or ''
                        if line.code == netsal_code:
                            net_amount += line.total
                            net_account_id = credit_account_id
                            continue
                        elif line.code == sal_earned_code:
                            name = "SALARY FOR THE MONTH OF %s-%s"%(month.upper(), str(year))
                        elif line.code == overtime_code or line.code == advance_code:
                            name = "%s FOR THE MONTH OF %s-%s"%(str(name or ''), month.upper(), str(year))
                        if line.code == allowance_code:
                            for allowance in slip_line.other_allow_ids:
                                if allowance.amount != 0.00:
                                    name = allowance.name.upper()
                                    vals = {
                                            'name': name,
                                            'date': payroll.date_end,
                                            'partner_id': line.employee_id.address_home_id.id,
                                            'account_id': credit_account_id,
                                            'journal_id': payroll.journal_id.id,
                                            'period_id': period_id,
                                            'debit': 0.00,
                                            'credit': allowance.amount or 0.00,
                                            'move_id': move_id
                                            }
                                    account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
                                                                                                         credit_account_id,
                                                                                                         context=context)
                                    vals.update(account_change_onchange_data.get('value', {}))
                                    move_line_pool.create(cr, uid, vals, context=context)
                        else:
                            vals = {
                                    'name': name,
                                    'date': payroll.date_end,
                                    'partner_id': line.employee_id.address_home_id.id,
                                    'account_id': credit_account_id,
                                    'journal_id': payroll.journal_id.id,
                                    'period_id': period_id,
                                    'debit': 0.00,
                                    'credit': line.total or 0.00,
                                    'move_id': move_id
                                    }
                            account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
                                                                                                 credit_account_id,
                                                                                                 context=context)
                            vals.update(account_change_onchange_data.get('value', {}))
                            move_line_pool.create(cr, uid, vals, context=context)
                slip_line.write({'paid': True, 'state': 'done'})
            vals = {
                    'name': payroll.name,
                    'date': payroll.date_end,
                    'account_id': net_account_id,
                    'journal_id': payroll.journal_id.id,
                    'period_id': period_id,
                    'debit': 0.00,
                    'credit': net_amount or 0.00,
                    'partner_id': False,
                    'move_id': move_id
                    }
            account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
                                                                                 net_account_id,
                                                                                 context=context)
            vals.update(account_change_onchange_data.get('value', {}))
            move_line_pool.create(cr, uid, vals, context=context)
            move_ids.append(move_id)
            payroll.write({'state': 'close', 'payment_id': move_id})
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_move_journal_line')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in',["+','.join(map(str, move_ids))+"])]"
        return result
    
    def draft_payslip_run(self, cr, uid, ids, context=None):
        for payroll in self.browse(cr, uid, ids, context=context):
            if payroll.payment_id and payroll.payment_id.state == 'posted':
                raise osv.except_osv(_("Error!!!"),
                                     _("Please unpost the related voucher..."))
            for line in payroll.slip_ids:
                line.write({'state': 'draft'})
        res = super(hr_payslip_run, self).draft_payslip_run(cr, uid, ids, context=context)
        return res
    
hr_payslip_run()

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    
    
    def _get_last_leave_date(self, cr, uid, ids, fields, args, context=None):
        res = {}
        payslip_pool = self.pool.get('hr.payslip')
        for contract in self.browse(cr, uid, ids, context=context):
            employee_id = contract.employee_id.id
            payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                                        ('leave_sal', '=', True),
                                                        ('state', 'not in', ['draft', 'cancel'])],
                                              order='leave_to desc', limit=1)
            if payslip_ids:
                payslip_obj = payslip_pool.browse(cr, uid, payslip_ids[0],
                                                  context=context)
                leave_date = payslip_obj.leave_to
            elif contract.date_start:
                leave_date = contract.date_start
            else:
                leave_date = contract.employee_id.join_date
            if contract.man_last_leave_date and leave_date < contract.man_last_leave_date:
                leave_date = contract.man_last_leave_date
            res[contract.id] = leave_date
        return res
    
    _columns = {
                'sal_ids': fields.one2many('employee.salary.structure', 'contract_id',
                                           'Salary Details'),
                'man_last_leave_date': fields.date('Manual Last Leave Date'),
                'last_leave_date': fields.function(_get_last_leave_date, type="date",
                                                   string="Last Leave Date")
                }
hr_contract()


class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'
    _columns = {
            'display_bold' : fields.boolean('Display in Bold')
                }
hr_salary_rule()


class payslip_payment_details(osv.osv):
    _name = 'payslip.payment.details'
    _description = 'Payslip Payment Details'
    _columns = {
                'voucher_id': fields.many2one('account.move', 'Related Voucher'),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'name': fields.char('Narration', size=256),
                'batch_id': fields.many2one('hr.payslip.run', 'Batch Ref')
                }
payslip_payment_details()

class employee_salary_structure(osv.osv):
    _name = 'employee.salary.structure'
    _description = 'Model to define employee salary amounts'
    _rec_name = 'name'
    
    _columns = {
                'name': fields.related('categ_id', 'name', type="char", relation='hr.salary.rule.category', string="Name"),
                'categ_id': fields.many2one('hr.salary.rule.category', 'Category'),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'contract_id': fields.many2one('hr.contract', 'Contract',
                                               ondelete="cascade"),
                }
employee_salary_structure()

class payslip_salary_structure(osv.osv):
    _name = 'payslip.salary.structure'
    _description = 'Model to define employee salary amounts'
    _columns = {
                'categ_id': fields.many2one('hr.salary.rule.category', 'Category'),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'payslip_id': fields.many2one('hr.payslip', 'Payslip',
                                              ondelete="cascade")
                }
employee_salary_structure()

class employee_sal_advances(osv.osv):
    _name = 'employee.sal.advances'
    _description = 'Employee Salary Advances'
    
    def onchange_voucher(self, cr, uid, uds, voucher_id, employee_id, context=None):
        res = {'value': {}}
        voucher_pool = self.pool.get('account.move')
        employee_pool = self.pool.get('hr.employee')
        if voucher_id and employee_id:
            voucher_obj = voucher_pool.browse(cr, uid, voucher_id, context=context)
            employee_obj = employee_pool.browse(cr, uid, employee_id, context=context)
            employee_partner_id = employee_obj.address_home_id.id
            amount = 0.00
            account_id = False
            for line in voucher_obj.line_id:
                if line.partner_id.id == employee_partner_id:
                    amount = line.debit - line.credit
                    account_id = line.account_id.id or False
            res['value'] = {
                            'name': voucher_obj.ref,
                            'account_id': account_id,
                            'amount': amount
                            }
        return res
    
    _columns = {
                'account_id': fields.many2one('account.account', 'Account',
                                              domain="[('type', '!=', 'view')]"),
                'name': fields.text('Narration'),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'payslip_id': fields.many2one('hr.payslip', 'Payslip'),
                'voucher_id': fields.many2one('account.move', 'Related Voucher')
                }
employee_sal_advances()

class employee_other_allowances(osv.osv):
    _name = 'employee.other.allowances'
    _description = 'Employee Other Allowances'
    _columns = {
                'name': fields.char('Narration', size=256),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'payslip_id': fields.many2one('hr.payslip', 'Payslip'),
                'general_all_id': fields.many2one('gen.employee.allowances',
                                                  'General Allowances Ref.'),
                'gen_allowance': fields.boolean('General Allowance?')
                }
employee_other_allowances()

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
		'mol_no':fields.char('MOL ID', size=64, help="Ministry Of Labour ID"),
                'comp_bank_number': fields.char('Company ID Number as per bank', size=128),
                'labor_number': fields.char('Company Labour Number', size=128)
#                 'agent_bank_id': fields.many2one('hr.employee.agent.bank', 'Agent Bank'),
#                 'agent_bank_ac_no': fields.char('Account No', size=32),
                }
res_company()

class payroll_emp_line(osv.osv):
    _name = 'payroll.emp.line'
    _description = 'Payroll Employee Line'
    
    def _get_total_days(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            payroll = line.payroll_id
            from_date = payroll.date_start
            to_date = payroll.date_end
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
            days = ((to_date - from_date).days) + 1
            res[line.id] = days
        return res
    
    def _get_advance_balance(self, cr, uid, ids, fields, args, context=None):
        res = {}
        icp = self.pool.get('ir.config_parameter')
        move_line_pool = self.pool.get('account.move.line')
        account_id = icp.get_param(cr, uid, 'hatta_hr_management.emp_adv_account_id', False)
        for line in self.browse(cr, uid, ids, context=context):
            amount = 0.00
            if account_id:
                domain = [('account_id', '=', int(account_id)),
                          ('partner_id', '=', line.employee_id.address_home_id.id),
                          ('date', '<=', line.payroll_id.date_end)]
                move_line_ids = move_line_pool.search(cr, uid, domain, context=context)
                for move_line_obj in move_line_pool.browse(cr, uid, move_line_ids, context=context):
                    balance = move_line_obj.debit - move_line_obj.credit
                    amount += balance
            res[line.id] = amount * -1.00
        return res
    
    _columns = {
                'employee_id': fields.many2one('hr.employee', 'Employee'),
                'total_days': fields.related('payslip_id', 'total_days', type="float",
                                             string="Total Days", store=True),
#                 'total_days': fields.function(_get_total_days, type="float",
#                                               string="Total Days",
#                                               store={
#                                                      'hr.payslip.run': (lambda self, cr, uid, ids, c={}: ids, ['date_start', 'date_end'], 20),
#                                                      }),
                'days_payable': fields.float('Days Payable'),
                'leave_days': fields.float('Days Leave'),
                'sick_leave': fields.float('Sick Leave'),
                'sal_advance': fields.float('Salary Advance', digits_compute=dp.get_precision('Account')),
                'overtime_normal': fields.float('Normal Overtime(Hours)'),
                'holiday_overtime': fields.float('Holiday Overtime(Hours)'),
                'holiday_worked': fields.float('Holiday Worked'),
#                 'advance_balance': fields.function(_get_advance_balance, type="float",
#                                                    digits_compute=dp.get_precision('Account'),
#                                                    string="Balance Advance"),
                'advance_balance': fields.related('payslip_id', 'advance_balance', type="float",
                                                  digits_compute=dp.get_precision('Account'),
                                                  string="Balance Advance"),
                'advance_ded': fields.float('Advance Deduction',
                                            digits_compute=dp.get_precision('Account')),
                'tel_deduction': fields.float('Telephone Deduction',
                                              digits_compute=dp.get_precision('Account')),
                'payroll_id': fields.many2one('hr.payslip.run', 'Payroll Ref', on_delete="cascade"),
                'payslip_id': fields.many2one('hr.payslip', 'Related Payslip', on_delete="cascade")
                }
    
payroll_emp_line()

class gen_employee_allowances(osv.osv):
    _name = 'gen.employee.allowances'
    _description = 'General Employee Allowances'
    _columns = {
                'name': fields.char('Narration', size=256),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'payroll_id': fields.many2one('hr.payslip.run', 'Payroll')
                }
gen_employee_allowances()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

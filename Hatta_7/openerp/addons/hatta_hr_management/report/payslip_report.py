# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 ZestyBeanz Technologies Pvt. Ltd.
#    (http://www.zbeanztech.com)
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

from hatta_rejection_management import JasperDataParser
from collections import defaultdict
from jasper_reports import jasper_report

from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator
from tools.translate import _


class hatta_report_payslip(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(hatta_report_payslip, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        user_pool = self.pool.get('res.users')
        payslip_pool = self.pool.get('hr.payslip')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        payslip_obj = payslip_pool.browse(cr, uid, ids[0], context=context)
        comp_obj = payslip_obj.payslip_run_id and payslip_obj.payslip_run_id.company_id or \
                            user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                }
        return vals
    
    def get_rate(self, cr, uid, payslip, context=None):
        hours, rate, value = 0, 0, 0
        if payslip.line_ids:
            hra_amount = 0.00
            basic_amount = payslip.contract_id.wage or 0.00
            for line in payslip.sal_ids:
                if line.categ_id.code == 'HRA':
                    hra_amount += line.amount
            basic_hra_amount = basic_amount + hra_amount
            basic_hra_sum_perhr = (basic_hra_amount / 30.00) / 8.00
            normal_overtime = basic_hra_sum_perhr * payslip.overtime_normal
            holiday_overtime = (basic_hra_sum_perhr * 1.5) * payslip.holiday_overtime
            value = normal_overtime + holiday_overtime
            hours = payslip.overtime_normal + payslip.holiday_overtime
            if hours != 0.00:
                rate = float(value) / float(hours)
        return hours, rate, round(value)
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        total_earnings = 0
        sal_rule_categ_pool = self.pool.get('hr.salary.rule.category')
        icp = self.pool.get('ir.config_parameter')
        ignore_code_list = []
        ignore_categ_ids = []
        earning_categ_id = icp.get_param(cr, uid,
                                         'hatta_hr_management.parent_earning_categ',
                                         False)
        deduction_categ_id = icp.get_param(cr, uid,
                                           'hatta_hr_management.parent_ded_categ',
                                           False)
        special_allowance_code = icp.get_param(cr, uid,
                                               'hatta_hr_management.allowance_code',
                                               'False')
        ignore_code_list.append(special_allowance_code)
        basic_code = icp.get_param(cr, uid,
                                   'hatta_hr_management.basic_salary_code',
                                   'False')
        ignore_code_list.append(basic_code)
        if not earning_categ_id or not deduction_categ_id:
            raise osv.except_osv(_("Error!!!"),
                                 _("Please configure salary deduction and earnings category..."))
        earning_categ_ids = sal_rule_categ_pool.search(cr, uid, [('parent_id', 'child_of', int(earning_categ_id))],
                                                       context=context)
        deduction_categ_ids = sal_rule_categ_pool.search(cr, uid, [('parent_id', 'child_of', int(deduction_categ_id))],
                                                         context=context)
        for payslip in self.pool.get('hr.payslip').browse(cr, uid, ids, context=context):
            month = datetime.strptime(payslip.date_from, "%Y-%m-%d").strftime("%B %Y")
            
            employee = payslip.employee_id.name
            emp_id = payslip.employee_id.emp_no or ''
            designation = payslip.employee_id.job_id and payslip.employee_id.job_id.name
            
            if payslip.employee_id.join_date:
                date = payslip.employee_id.join_date
                join_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                join_date = ''
                
            passport_no = payslip.employee_id.passport_id
            if payslip.employee_id.passport_expiry_date:
                valid = payslip.employee_id.passport_expiry_date
                passport_valid = datetime.strptime(valid, "%Y-%m-%d")
            else:
                passport_valid = ''
                
            work_permit = payslip.employee_id.labour_card_no
            if payslip.employee_id.labour_card_expiry_date:
                permit_valid = payslip.employee_id.labour_card_expiry_date
                work_permit_valid = datetime.strptime(permit_valid, "%Y-%m-%d")
            else:
                work_permit_valid = ''
                
            days_month = payslip.total_days
            days_payable = payslip.days_payable
            sick_leave = 0
            bank_name = payslip.employee_id.bank_account_id and payslip.employee_id.bank_account_id.bank and payslip.employee_id.bank_account_id.bank.name
            acc_no = payslip.employee_id.bank_account_id.acc_number
            
            
            advance = payslip.advance_ded
            telephone = payslip.tel_deduction
            
            
            
            
            
            
            
            
            hours, rate, value = self.get_rate(cr, uid, payslip, context=context)
#             value = payslip.overtime_normal * rate
            
            
            
            
            
            
            
            
            
            holiday_value = 25.00 * payslip.holiday_worked
            balance_outstanding = payslip.advance_balance - payslip.advance_ded
            
            vals = {
                'month' : month.upper(),
                'employee' : employee,
                'emp_id' : emp_id,
                'designation' : designation or '',
                'join_date' : join_date,
                'passport_no' : passport_no or '',
                'passport_valid' : passport_valid,
                'work_permit' : work_permit or '',
                'work_permit_valid' : work_permit_valid,
                'days_month' : days_month or "0.00",
                'days_payable' : days_payable or "0.00",
                'bank_name' : bank_name or '',
                'acc_no' : acc_no or '',
                'sub_report' : [],
                'sub_report_2': [],
                'sub_report_other' : [],
                'total_earnings' : 0.00,
                'advance' : advance,
                'telephone' : telephone,
                'total_deduction' : 0.00,
                'net_pay' : 0.00,
                'hours' : hours or "0.00",
                'sick_leave': payslip.sick_leave or "0.00",
                'holiday_hours': payslip.holiday_worked or "0.00",
                'rate' : rate or "0.00",
                'value' : round(value) or "0.00",
                'holiday_rate' : payslip.holiday_worked and 25.00 or '0.00',
                'holiday_value' : holiday_value or "0.00",
                'total_value' : round(value + holiday_value) or "0.00",
                'notes' : payslip.notes,
                'balance_outstanding' : balance_outstanding and "Balance Outstanding in Staff Advance A/c= AED. %s/-" %(format(balance_outstanding, '.2f')) or ''
                    }
            
            total_earning = 0.00
            total_deduction = 0.00
            if payslip.contract_id.wage != 0.00:
                base = payslip.contract_id.wage
                base_per_day = payslip.contract_id.wage / 30.00
                red = base_per_day * payslip.leave_days
                amount = round(base - red)
                line_vals = {
                             'name' : "Basic",
                             'total' : amount,
                             'display_bold' : False
                             }
                total_earning += base - red
                vals['sub_report'].append(line_vals)
            for sal_line in payslip.sal_ids:
                if sal_line.amount != 0.00 and payslip.days_payable != 0.00:
                    base = sal_line.amount
                    base_per_day = sal_line.amount / 30.00
                    red = base_per_day * payslip.leave_days
                    amount = round(base - red)
                    line_vals = {
                                 'name' : sal_line.categ_id.name or '',
                                 'total' : amount,
                                 'display_bold' : False
                                 }
                    total_earning += base - red
                    ignore_categ_ids.append(sal_line.categ_id.id)
                    vals['sub_report'].append(line_vals)
            
            if payslip.line_ids:
                for line in payslip.line_ids:
                    if line.total != 0.00 and line.code not in ignore_code_list and line.category_id.id not in ignore_categ_ids:
#                     if line.total and line.name not in ['Net Salary Paid', 'Total Deduction', 'Tel Charge Ded', 'Advance Deduction', 'Pending Advances', 'Total Income', 'Salary Earned']:
                        line_vals = {
                              'name' : line.name,
                              'total' : round(line.total),
                              'display_bold' : line.salary_rule_id.display_bold
                                     }
                        if line.category_id.id in earning_categ_ids:
                            vals['sub_report'].append(line_vals)
                            total_earning += line.total
                        elif line.category_id.id in deduction_categ_ids:
                            vals['sub_report_2'].append(line_vals)
                            total_deduction += line.total
            else:
                line_vals = {
                  'name' : '',
                  'total' : '',
                  'display_bold' : False
                         }
                vals['sub_report'].append(line_vals)
            if payslip.other_allow_ids:
                for other_allow in payslip.other_allow_ids:
                    other_vals = {
                          'other_name' : other_allow.name,
                          'other_total' : round(other_allow.amount),
                                  }
                    vals['sub_report_other'].append(other_vals)
                    total_earning += other_allow.amount
            else:
                other_vals = {
                  'other_name' : '',
                  'other_total' : '',
                          }
                vals['sub_report_other'].append(other_vals)
            vals['total_earnings'] = round(total_earning)
            vals['total_deduction'] = round(total_deduction)
            vals['net_pay'] = round(total_earning) - round(total_deduction)
            result.append(vals)
        return result
    
jasper_report.report_jasper('report.payslip_report_jasper', 'hr.payslip', parser=hatta_report_payslip)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

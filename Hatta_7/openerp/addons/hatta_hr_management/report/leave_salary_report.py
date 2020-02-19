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
import time
from datetime import datetime
from operator import itemgetter
import operator
from tools.translate import _


class leave_salary_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(leave_salary_report, self).__init__(cr, uid, ids, data, context)
        
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
        run_time = time.strftime("%d/%m/%Y")
        run_time = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        vals = {
                'company_name': comp_obj.name or '',
                'current_date_time': run_time,
                }
        return vals
    
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        for payslip in self.pool.get('hr.payslip').browse(cr, uid, ids, context=context):
            salary_details = ''
            status = ''
            basic = 0.0
            if payslip.leave_sal == True:
                for salry_struct in payslip.leave_sal_ids:
                    salary_details += salry_struct.name + ', '
                if payslip.date_of_rejoining:
                    date_of_rejoining = datetime.strptime(payslip.date_of_rejoining, "%Y-%m-%d")
                else:
                    date_of_rejoining = ''
                if payslip.leave_from:
                    leave_from = datetime.strptime(payslip.leave_from, "%Y-%m-%d").strftime('%d-%m-%Y')
                    leave_from_date = datetime.strptime(payslip.leave_from, "%Y-%m-%d")
                else:
                    leave_from = ''
                    leave_from_date = ''
                if payslip.leave_to:
                    leave_to = datetime.strptime(payslip.leave_to, "%Y-%m-%d")
                else:
                    leave_to = ''
                if payslip.date_from:
                    date_from = datetime.strptime(payslip.date_from, "%Y-%m-%d")
                    from_month = date_from.strftime("%B")
                else:
                    from_month = ''
                if payslip.state == 'draft':
                    status = 'Draft'
                elif payslip.state == 'done':
                    status = 'Confirmed'
                name = 'DETAILS OF LEAVE SALARY PAID TO ' + payslip.employee_id.name.upper() + \
                       ' WHILE PROCEEDING ON LEAVE FROM ' + str(leave_from)
                salary = 0.0
                for line in payslip.line_ids:
                    if line.code in ['BASIC','HRA','TA','OA','FA','PALW','SPI']:
                        salary += line.total
                    if line.code == 'BASIC':
                        basic = line.total
                leave_sal_amount = payslip.leave_base_amt/30 * payslip.actual_leave_days
                leave_encashment = (payslip.leave_base_amt * (payslip.leave_sal_eligible_for - payslip.actual_leave_days))/30 
                other_allowance = 0.0
                for other_allow in payslip.other_allow_ids:
                    other_allowance += other_allow.amount
                total_payable = salary + payslip.sal_advance + leave_sal_amount + leave_encashment + other_allowance
                less = payslip.advance_ded + payslip.tel_deduction
                leave_eligible_for_label = '[ 30/365*(' + str(int(payslip.days_after_leave)) + ')]'
                leave_sal_label = 'Leave Salary for ' + str(payslip.actual_leave_days) + ' days' + ' [' + \
                                  str(payslip.leave_base_amt) + '/30 * (' + str(payslip.actual_leave_days) + ')] ' + "[ "+  str(basic)
                if salary_details: 
                    leave_sal_label += " + " + salary_details + ']'
                else:
                    leave_sal_label += ']'
                leave_encashment_label = '[ ' + str(payslip.leave_base_amt) + '/30 * (' \
                                         + str(payslip.leave_sal_eligible_for) + ' - ' + str(payslip.actual_leave_days) + ')]'
                days_after_leave = payslip.days_after_leave
                if payslip.other_allow_ids:
                    for other_allow in payslip.other_allow_ids:
                        vals = {
                                'name': name,
                                'date_of_rejoining': date_of_rejoining,
                                'days_after_leave': payslip.days_after_leave or '0.0',
                                'leave_eligible_for': int((30*days_after_leave)/365) or '0',
                                'leave_eligible_for_label': leave_eligible_for_label or '',
                                'less_availed': payslip.less_availed or '0',
                                'leave_sal_eligible_for': int(payslip.leave_sal_eligible_for) or '0.0',
                                'actual_leave_days': payslip.actual_leave_days or '0',
                                'sal_advance': payslip.sal_advance or '0.0',
                                'status': status,
                                'salary': salary,
                                'leave_sal_label':  leave_sal_label or '',
                                'leave_sal_amount': leave_sal_amount or '0.0',
                                'leave_encashment': leave_encashment or '0.0',
                                'leave_encashment_label': leave_encashment_label or '',
                                'other_allow_name': other_allow.name or '',
                                'other_allow_amount': other_allow.amount or '',
                                'other_allow_ref': other_allow.general_all_id and other_allow.general_all_id.name  or '',
                                'other_allowance': other_allowance or '0.0',
                                'other_allowance_label': 'Other Allowances [Air Tickets + Other if any]' or '',
                                'total_payable': total_payable or '0.0',
                                'monthly_deduction': less or '0.0',
                                'net_amount_payable': total_payable - less or '0.0',
                                'leave_encashed': payslip.leave_encashed or '0',
                                'leave_from': leave_from_date,
                                'leave_to': leave_to,
                                'other_allow': True,
                                'leave_applied': abs((leave_to - leave_from_date).days) + 1,
                                'from_month': from_month or ''
                                }
                        result.append(vals)
                else:
                    vals = {
                            'name': name,
                            'date_of_rejoining': date_of_rejoining,
                            'days_after_leave': payslip.days_after_leave or '0.0',
                            'leave_eligible_for': int(30/365*(payslip.days_after_leave)) or '0',
                            'less_availed': payslip.less_availed or '0',
                            'leave_sal_eligible_for': int(payslip.leave_sal_eligible_for) or '0',
                            'leave_eligible_for_label': leave_eligible_for_label or '',
                            'actual_leave_days': payslip.actual_leave_days or '0',
                            'sal_advance': payslip.sal_advance or '0.0',
                            'status': status,
                            'salary': salary,
                            'leave_sal_label': leave_sal_label or '',
                            'leave_sal_amount': leave_sal_amount or '0.0',
                            'leave_encashment': leave_encashment or '0.0',
                            'leave_encashment_label': leave_encashment_label or '',
                            'other_allow_name': '',
                            'other_allow_amount': '',
                            'other_allow_ref':  '',
                            'other_allowance': other_allowance or '0.0',
                            'other_allowance_label': 'Other Allowances [Air Tickets + Other if any]' or '',
                            'total_payable': total_payable or '0.0',
                            'monthly_deduction': less or '0.0',
                            'net_amount_payable': total_payable - less or '0.0',
                            'leave_encashed': payslip.leave_encashed or '0',
                            'leave_from': leave_from_date,
                            'leave_to': leave_to,
                            'other_allow': False,
                            'leave_applied': abs((leave_to - leave_from_date).days) + 1,
                            'from_month': from_month or ''
                            }
                    result.append(vals)
        return result
    
jasper_report.report_jasper('report.leave_salary_report_jasper', 'hr.payslip', parser=leave_salary_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

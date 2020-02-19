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


class hr_salary_computation(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        data['report_type'] = 'xls'
        super(hr_salary_computation, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        if context is None:
            context = {}
        batch_pool = self.pool.get('hr.payslip.run')
        vals={}
        report_heading = ''
        active_id = context.get('active_id', False)
        pay_line_data = []
        notes = ''
        if active_id:
            batch_obj = batch_pool.browse(cr, uid, active_id, context=context)
            report_heading = batch_obj.name or ''
            notes = batch_obj.note or ''
        vals = {
                'report_heading': report_heading,
                'note': notes
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        if context is None:
            context = {}
        def unique(items):
            found = set([])
            keep = []
            for item in items:
                if item not in found:
                    found.add(item)
                    keep.append(item)
            return keep
        batch_pool = self.pool.get('hr.payslip.run')
        icp = self.pool.get('ir.config_parameter')
        batch_ids = context.get('active_ids', [])
        total_dict = {}
        final_key_list = []
        pay_line_data = []
        for batch_obj in batch_pool.browse(cr, uid, batch_ids, context=context):
            count = 0
            for payslip in batch_obj.slip_ids:
                key_list = []
                count += 1
                employee_ac_no = payslip.employee_id.bank_account_id and \
                                    payslip.employee_id.bank_account_id.acc_number or ''
                trans_mode = payslip.employee_id.sal_transfer_mode
                labor_no = payslip.employee_id.labour_card_no
                em_code = payslip.employee_id.emp_no
                vals = {
                        'employee_name': payslip.employee_id.name,
                        'line_name': 'Basic',
                        'amount': payslip.contract_id.wage or "0.00",
                        'emp_acc': employee_ac_no,
                        'trans_mode': trans_mode,
                        'labor_no': labor_no,
                        'si_no': count,
                        'em_code': em_code,
                        'sort_seq': 1.00,
                        }
                result.append(vals)
                if not total_dict.get('Basic', False):
                    total_dict['Basic'] = 0.00
                key_list.append('Basic')
                total_dict['Basic'] += payslip.contract_id.wage or 0.00
                amount_total = payslip.contract_id.wage or 0.00
                base_lines_categ = []
                j = 2.00
                for sal_line in payslip.sal_ids:
                    base_lines_categ.append(sal_line.categ_id.id)
                    print j
                    vals = {
                            'employee_name': payslip.employee_id.name,
                            'line_name': sal_line.categ_id.name or '',
                            'amount': sal_line.amount or "0.00",
                            'emp_acc': employee_ac_no,
                            'trans_mode': trans_mode,
                            'labor_no': labor_no,
                            'si_no': count,
                            'em_code': em_code,
                            'sort_seq': j,
                            }
                    j += 0.1
                    amount_total += sal_line.amount or 0.00
                    result.append(vals)
                    
                    if not total_dict.get(sal_line.categ_id.name, False):
                        total_dict[sal_line.categ_id.name] = 0.00
                    key_list.append(sal_line.categ_id.name)
                    total_dict[sal_line.categ_id.name] += sal_line.amount or 0.00
                    
                vals = {
                        'employee_name': payslip.employee_id.name,
                        'line_name': 'Total Income',
                        'amount': amount_total or "0.00",
                        'emp_acc': employee_ac_no,
                        'trans_mode': trans_mode,
                        'labor_no': labor_no,
                        'si_no': count,
                        'em_code': em_code,
                        'sort_seq': 4.00,
                        }
                result.append(vals)
                
                print 3.00
                if not total_dict.get('Total Income', False):
                    total_dict['Total Income'] = 0.00
                key_list.append('Total Income')
                total_dict['Total Income'] += amount_total or 0.00
                
                
                vals = {
                        'employee_name': payslip.employee_id.name,
                        'line_name': 'Days Worked',
                        'amount': payslip.days_payable or "0.00",
                        'emp_acc': employee_ac_no,
                        'trans_mode': trans_mode,
                        'labor_no': labor_no,
                        'si_no': count,
                        'em_code': em_code,
                        'sort_seq': 5.00
                        }
                result.append(vals)
                print 4.00
                j = 6.00
                allowance_code = icp.get_param(cr, uid, 'hatta_hr_management.allowance_code',
                                               'False')
                for pay_line in payslip.line_ids:
                    categ_id = pay_line.category_id.id
                    if categ_id not in base_lines_categ and pay_line.code != 'BASIC':
                        if pay_line.code != allowance_code:
                            name = pay_line.name
                            amount = pay_line.total
                            vals = {
                                    'employee_name': payslip.employee_id.name,
                                    'line_name': pay_line.name or '',
                                    'amount': pay_line.total or "0.00",
                                    'emp_acc': employee_ac_no,
                                    'trans_mode': trans_mode,
                                    'labor_no': labor_no,
                                    'si_no': count,
                                    'em_code': em_code,
                                    'sort_seq': j
                                    }
                            j += 0.10
                            result.append(vals)
                            if not total_dict.get(name, False):
                                total_dict[name] = 0.00
                            key_list.append(name)
                            total_dict[name] += amount or 0.00
                        else:
                            for allow in payslip.other_allow_ids:
                                name = allow.name
                                amount = allow.amount
                                vals = {
                                        'employee_name': payslip.employee_id.name,
                                        'line_name': allow.name or '',
                                        'amount': allow.amount or "0.00",
                                        'emp_acc': employee_ac_no,
                                        'trans_mode': trans_mode,
                                        'labor_no': labor_no,
                                        'si_no': count,
                                        'em_code': em_code,
                                        'sort_seq': j
                                        }
                                j += 0.10
                                result.append(vals)
                if len(key_list) > len(final_key_list):
                    final_key_list = key_list
#                                 if not total_dict.get(name, False):
#                                     total_dict[name] = 0.00
#                                     key_list.append(name)
#                                 total_dict[name] += amount or 0.00
            pay_line = batch_obj.payment_id or False
            amount = 0.00
            if pay_line:
                for line in pay_line.line_id:
                    amount += line.debit
                vals = {
                        'voucher_name': pay_line.name or '',
                        'ref': pay_line.name or '',
                        'amount': amount or "0.00"
                        }
                pay_line_data.append(vals)
        key_list = unique(final_key_list)
        for key in key_list:
#             print key,"------->",total_dict[key]
            vals = {
                    'employee_name': 'TOTAL',
                    'line_name': key,
                    'amount': total_dict.get(key, 0.00),
                    'emp_acc': '',
                    'trans_mode': '',
                    'labor_no': '',
                    'si_no': 0,
                    'em_code': '',
                    'sort_seq': 0,
                    'payline_data': pay_line_data
                    }
            result.append(vals)
#         result = sorted(result, key=operator.itemgetter('si_no', 'sort_seq'))
#         print result
        return result
    
jasper_report.report_jasper('report.sal_computation_batch_jasper', 'hr.payslip.run',
                            parser=hr_salary_computation)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

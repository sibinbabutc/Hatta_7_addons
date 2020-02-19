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

import JasperDataParser
from openerp.addons.jasper_reports import jasper_report

from osv import fields, osv
import time
import datetime
from datetime import datetime

import JasperDataParser
from openerp.addons.jasper_reports import jasper_report

from osv import fields, osv
import time
import datetime
from datetime import datetime

class telephone_expense_jasper(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        #print '1'*555
        super(telephone_expense_jasper, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context):
        vals = {} 
        if data['report_type']=='xls':
            vals.update({'IS_IGNORE_PAGINATION':True})
        run_time = time.strftime("%d/%m/%Y")
        expense_pool = self.pool.get('telephone.expense')
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        expense_ids = data.get('form',False)
#         report_header = ''
        report_header = str(user_obj.company_id.name) or ''
        run_time = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        for expense in expense_pool.browse(cr, uid, expense_ids, context=context):
            month = dict(self.pool.get('telephone.expense').fields_get(cr, uid, allfields=['month'], context=context)['month']['selection'])[expense.month]
            report_header += ' - ' + expense.service_provider_id.name + ' Bills For ' + month + ' - '+ str(expense.year)
            
        vals.update({
                'report_header': report_header,
                'current_date_time': run_time,
                })
        return vals

    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true'
            }
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        expense_pool = self.pool.get('telephone.expense')
        expense_ids = data.get('form',False)
        data_sub_exp_line = []
        data_sub_account_info = []
        data_sub_group_info = []
        for expense in expense_pool.browse(cr, uid, expense_ids, context=context):
            val={}
            for line in expense.expense_line_ids:
                res_sub_exp_line = {
                    'sl_no' : line.sl_no or '',
                    'directory_name' : line.directory_id and line.directory_id.name or '',
                    'mobile' : line.mobile or '',
                    'total_amt' : line.total_amount or '0.0',
                    'allowed_amount': line.allowed_amount or '0.0',
                    'deduction' : line.deduction or '0.0',
                    'balance' : line.balance or '0.0',
                    'remarks' : line.remarks or '',
                    'prev_month_balance' : line.prev_month_balance or '0.0',
                    'prev_month_increase' : line.prev_month_increase or '0.0',
                    'prev_month_decrease' : line.prev_month_decrease or '0.0',
                    'total_amount_exp': expense.total_amount  or '0.0',
                    'total_prev_month_balance': expense.total_prev_month_balance  or '0.0',
                    'total_prev_month_increase': expense.total_prev_month_increase  or '0.0',
                    'total_prev_month_decrease': expense.total_prev_month_decrease  or '0.0',
                    'net_prev_month_increase': expense.net_prev_month_increase  or '0.0',
                }
                data_sub_exp_line.append(res_sub_exp_line)
            for account_info in expense.account_allocation_ids:
                res_sub_accnt_info = {
                    'account' : account_info.account_id and account_info.account_id.name or '',
                    'analytic_account' : account_info.analytic_account_id and account_info.analytic_account_id.name or '',
                    'percentage': account_info.percentage or '0.0',
                    'value' : account_info.value or '0.0',
                    'account_total_value': expense.account_total_value or '0.0',
                }
                data_sub_account_info.append(res_sub_accnt_info)
            for group_info in expense.group_allocation_ids:
                res_sub_group_info = {
                    'group' : group_info.group_id and group_info.group_id.name or '',
                    'percentage': group_info.percentage or '0.0',
                    'value' : group_info.value or '0.0',
                    'group_total_value': expense.group_total_value or '0.0',
                }
                data_sub_group_info.append(res_sub_group_info)
            state = dict(self.pool.get('telephone.expense').fields_get(cr, uid, allfields=['state'], context=context)['state']['selection'])[expense.state]
            val.update({
                         'name': expense.name,
                         'post_voucher': expense.posted_move_id and expense.posted_move_id.name or '',
                         'payment_voucher': expense.payment_move_id and expense.payment_move_id.name or '',
                         'check_no': expense.check_no or '',
                         'bank': expense.bank_journal_id and expense.bank_journal_id.name or '',
                         'remarks': expense.remarks or '',
                         'notes': expense.notes or '',
                         'state': state or '',
                         'sub_expense_line': data_sub_exp_line or [],
                         'sub_account_info': data_sub_account_info or [],
                         'sub_group_info': data_sub_group_info or []
                        })
                #print 'val', val
            result.append(val)
        return result
        
        
jasper_report.report_jasper('report.telephone_expense_jasper', 'telephone.expense', 
                            parser=telephone_expense_jasper)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
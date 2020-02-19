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

from hatta_account import JasperDataParser
from collections import defaultdict
from jasper_reports import jasper_report
from account.report.account_financial_report import report_account_common

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime


class profit_and_loss(JasperDataParser.JasperDataParser, report_account_common):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(profit_and_loss, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        pool= pooler.get_pool(cr.dbname)
        user_pool = pool.get('res.users')
        ana_pool = pool.get('account.analytic.account')
        fin_pool = pool.get('account.financial.report')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)
        cost_center_ids = data['form']['cost_center_ids']
        report_id = data['form']['account_report_id'][0]
        report_obj = fin_pool.browse(cr, uid, report_id, context=context)
        cc_names = 'ALL'
        total_label = "TOTAL"
        if report_obj.total_label:
            total_label = report_obj.total_label or ''
        if cost_center_ids:
            cost_center_objs = ana_pool.browse(cr, uid, cost_center_ids, context=context)
            cc_list = [x.name for x in cost_center_objs]
            cc_names = ', '.join(cc_list)
        start_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
        end_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
        year = datetime.strptime(date_to, "%Y-%m-%d").strftime("%Y")
        account_report_name = data['form']['account_report_id'][1]
        grand_balance = 0.0
        total_profit = 0.0
        total_loss = 0.0
        child_accounts = self.cr.execute("""
                                                SELECT 
                                                    id
                                                FROM
                                                    account_account
                                                where 
                                                    code ilike '4%'
                                                """)
        child_ids = map(lambda x: x[0], self.cr.fetchall())
        if child_ids:
            balance_list = self._get_balance(data, child_ids)
            balance = balance_list and balance_list[0] or 0.0
            total_profit = abs(balance)
        child_accounts = self.cr.execute("""
                                            SELECT 
                                                id
                                            FROM
                                                account_account
                                            where 
                                                code ilike '5%' 
                                                    or 
                                                code ilike '6%'
                                            """)
        child_ids = map(lambda x: x[0], self.cr.fetchall())
        if child_ids:
            balance_list = self._get_balance(data, child_ids)
            balance = balance_list and balance_list[0] or 0.0
            total_loss = abs(balance)
        if account_report_name and account_report_name == 'PROFIT & LOSS':
            label = 'yes'
        else:
            label = 'no'
        if total_profit > total_loss:
            grand_balance = total_profit - total_loss
            grand_balance = -1 * grand_balance
        else:
            grand_balance = total_loss - total_profit
            grand_balance = 1 * grand_balance
        vals = {
                'company_name': comp_obj.name or '',
                'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                'curr': comp_obj.currency_id.name or '',
                'report_name': "%s AS ON %s"%(account_report_name, str(end_date)),
                'year': str(year),
                'cc_names': cc_names,
                'total_label': total_label,
                'grand_total': grand_balance,
                'label': label
                }
        return vals
    
    def _get_children_by_order(self, cr, uid, ids, context=None):
        '''returns a dictionary with the key= the ID of a record and value = all its children,
           computed recursively, and sorted by sequence. Ready for the printing'''
        res = []
        for id in ids:
            ids2 = self.pool.get('account.financial.report').search(cr, uid, [('parent_id', '=', id), ('id', '!=', id)], order='sequence ASC', context=context)
            res.extend(ids2)
        return res
    
    def _get_balance(self, data, child_ids):
        where_condition = """ where am.skip_check = 'false' and am.state = 'posted'"""
        if data['form'].get('date_from', False):
            where_condition += " and aml.date >= '%s'"%(str(data['form'].get('date_from', False)))
        if data['form'].get('date_from', False):
            where_condition += " and aml.date <= '%s'"%(str(data['form'].get('date_to', False)))
        if len(child_ids) == 1:
            where_condition += " and aml.account_id = %s"%(child_ids[0])
        else:
            where_condition += " and aml.account_id IN %s"%(tuple(child_ids), )
        if data['form'].get('cost_center_ids', False):
            cost_center_ids = data['form'].get('cost_center_ids', False)
            if len(cost_center_ids) > 1:
                where_condition += " and aml.analytic_account_id in %s"%(tuple(cost_center_ids), )
            else:
                where_condition += " and aml.analytic_account_id = %s"%(cost_center_ids[0])
        
        self.cr.execute("""
                            SELECT 
                                sum(aml.debit-aml.credit)
                            FROM
                                account_move_line aml
                            LEFT JOIN
                                account_move am 
                            on 
                                (am.id = aml.move_id)
                            %s
                            """%(where_condition))
        balance = self.cr.fetchall()
        balance = map(lambda x: x[0], balance)
        return balance
    
    def get_date(self, report, data):
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        fin_data = []
        balance = report.balance * report.sign or 0.0
        if report.name in ('REVENUE','INCOME'):
            child_accounts = self.cr.execute("""
                                                SELECT 
                                                    id
                                                FROM
                                                    account_account
                                                where 
                                                    code ilike '4%'
                                                """)
            child_ids = map(lambda x: x[0], self.cr.fetchall())
            if child_ids:
                balance_list = self._get_balance(data, child_ids)
                balance = balance_list and balance_list[0] or 0.0
                
        if report.name == 'EXPENSES' and report.type == 'sum':
            child_accounts = self.cr.execute("""
                                                SELECT 
                                                    id
                                                FROM
                                                    account_account
                                                where 
                                                    code ilike '5%' 
                                                        or 
                                                    code ilike '6%'
                                                """)
            child_ids = map(lambda x: x[0], self.cr.fetchall())
            if child_ids:
                balance_list = self._get_balance(data, child_ids)
                balance = balance_list and balance_list[0] or 0.0
        
        if report.name == 'COST OF SALES':
            child_accounts = self.cr.execute("""
                                                SELECT 
                                                    id
                                                FROM
                                                    account_account
                                                where 
                                                    code ilike '5%' 
                                                """)
            child_ids = map(lambda x: x[0], self.cr.fetchall())
            if child_ids:
                balance_list = self._get_balance(data, child_ids)
                balance = balance_list and balance_list[0] or 0.0
                
        if report.name == 'EXPENSES' and report.type == 'accounts':
            child_accounts = self.cr.execute("""
                                                SELECT 
                                                    id
                                                FROM
                                                    account_account
                                                where 
                                                    code ilike '6%' 
                                                """)
            child_ids = map(lambda x: x[0], self.cr.fetchall())
            if child_ids:
                balance_list = self._get_balance(data, child_ids)
                balance = balance_list and balance_list[0] or 0.0
        
        
        vals = {
                'name': report.name,
                'display_tot': report.display_total,
                'balance': balance,
                'type': 'report',
                'total': "false",
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
            }
        fin_data.append(vals)
        account_ids = []
        if report.display_detail == 'no_detail':
            return [vals]
        if report.type == 'accounts' and report.account_ids:
            account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
        elif report.type == 'account_type' and report.account_type_ids:
            account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
        if account_ids:
            for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                if report.display_detail == 'detail_flat' and account.type == 'view':
                    continue
                flag = False
                
                balance_list = self._get_balance(data, [account.id])
                balance = balance_list and balance_list[0] or 0.0
                
                vals = {
                    'name': account.code + ' ' + account.name,
                    'balance':  balance,
                    'type': 'account',
                    'total': "false",
                    'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                    'account_type': account.type,
                    'display_tot': False
                }

                if data['form']['view_all']:
                    flag = True
                elif not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                    flag = True
                if flag:
                    fin_data.append(vals)
                    
        child_ids = self._get_children_by_order(self.cr, self.uid, [report.id], context=data['form']['used_context'])
        for child_record in self.pool.get('account.financial.report').browse(self.cr, self.uid, child_ids, context=data['form']['used_context']):
            child_data = self.get_date(child_record, data)
            fin_data.extend(child_data)
        if report.display_total:
            
            if report.name in ('REVENUE','INCOME'):
                child_accounts = self.cr.execute("""
                                                    SELECT 
                                                        id
                                                    FROM
                                                        account_account
                                                    where 
                                                        code ilike '4%'
                                                    """)
                child_ids = map(lambda x: x[0], self.cr.fetchall())
                if child_ids:
                    balance_list = self._get_balance(data, child_ids)
                    balance = balance_list and balance_list[0] or 0.0
                    
            if report.name == 'EXPENSES' and report.type == 'sum':
                child_accounts = self.cr.execute("""
                                                    SELECT 
                                                        id
                                                    FROM
                                                        account_account
                                                    where 
                                                        code ilike '5%' 
                                                            or 
                                                        code ilike '6%'
                                                    """)
                child_ids = map(lambda x: x[0], self.cr.fetchall())
                if child_ids:
                    balance_list = self._get_balance(data, child_ids)
                    balance = balance_list and balance_list[0] or 0.0
            
            if report.name == 'COST OF SALES':
                child_accounts = self.cr.execute("""
                                                    SELECT 
                                                        id
                                                    FROM
                                                        account_account
                                                    where 
                                                        code ilike '5%' 
                                                    """)
                child_ids = map(lambda x: x[0], self.cr.fetchall())
                if child_ids:
                    balance_list = self._get_balance(data, child_ids)
                    balance = balance_list and balance_list[0] or 0.0
                    
            if report.name == 'EXPENSES' and report.type == 'accounts':
                child_accounts = self.cr.execute("""
                                                    SELECT 
                                                        id
                                                    FROM
                                                        account_account
                                                    where 
                                                        code ilike '6%' 
                                                    """)
                child_ids = map(lambda x: x[0], self.cr.fetchall())
                if child_ids:
                    balance_list = self._get_balance(data, child_ids)
                    balance = balance_list and balance_list[0] or 0.0
            
            vals = {
                    'name': "%s TOTAL"%(report.name),
                    'display_tot': False,
                    'total': "true",
                    'balance': balance or 0.0,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                    }
            fin_data.append(vals)
        return fin_data
    
    def get_lines(self, data):
        lines = []
        ids2 = self._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=data['form']['used_context'])
        for report in self.pool.get('account.financial.report').browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
            lines.extend(self.get_date(report, data))
        return lines
    
    def generate_records(self, cr, uid, ids, data, context):
        fin_report_pool = self.pool.get('accounting.report')
        result = []
        user_context = fin_report_pool._build_contexts(cr, uid, ids, data, context=context)
        data['form']['used_context'] = user_context
        lines = self.get_lines(data)
        final_data = []
        formating_dict = {
                          'main_title': "0",
                          'title_1': "0",
                          'title_2': "0",
                          'normal': "0",
                          'italic': "0",
                          'small': "0"
                          }
        tot_level = 0
        tot_dict = {}
        for line in lines:
            line_level = line['level']
            line['name'] = ' ' * line_level + line['name']
            temp_for = formating_dict.copy()
            if line.get('level', 0) == 1:
                temp_for['main_title'] = "1"
            elif line.get('level', 0) == 2:
                temp_for['title_1'] = "1"
            elif line.get('level', 0) == 3:
                temp_for['title_2'] = "1"
            elif line.get('level', 0) == 4:
                temp_for['normal'] = "1"
            elif line.get('level', 0) == 5:
                temp_for['italic'] = "1"
            elif line.get('level', 0) == 6:
                temp_for['small'] = "1"
            line.update(temp_for)
            if line.get('display_tot', False):
                tot_level = line_level
                tot_dict = line.copy()
            line['display_tot'] = line['display_tot'] and "true" or "false"
            final_data.append(line)
            tab_level = line_level
            if tab_level > 2:
                tab_level += 6
            line['name'] = ' ' * tab_level + line['name']
            if line['balance'] == 0.00:
                line['balance'] = "0.00"
        return final_data
    
jasper_report.report_jasper('report.balance_sheet_jasper', 'profit.loss.wizard', parser=profit_and_loss)
jasper_report.report_jasper('report.balance_sheet_jasper_xls', 'profit.loss.wizard', parser=profit_and_loss)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
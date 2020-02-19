# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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

from hatta_tb_report import JasperDataParser
from jasper_reports import jasper_report
import pooler
import time
from datetime import datetime as dt
from datetime import date, timedelta
import datetime as ti
import base64
import os
import sys
import math
from operator import itemgetter
import operator

# global prev_bal
# prev_bal = 0.0

def _convert_date(date):
    date = dt.strptime(str(date), '%Y-%m-%d').strftime('%d/%m/%Y')
    return date

class jasper_trial_balance(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(jasper_trial_balance, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    
    def generate_parameters(self, cr, uid, ids, data, context):
        if data['report_type']=='xls':
            return {'IS_IGNORE_PAGINATION':True}
        return {}

    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true'
            }
    def _get_sub_totals(self, cr, uid, data, context=None):
        debit_total = credit_total = balance_total = 0.0
        for dic in data['accounts']:
            if not dic['debit'] == '0.00':
                debit_total += dic['debit']
            if not dic['credit'] == '0.00':
                credit_total += dic['credit']
            if not dic['balance'] == '0.00':
                balance_total += dic['balance']
        for result in data['accounts']:
            result.update({
                'debit_total': debit_total or '0.00',
                'credit_total': credit_total or '0.00', 
                'balance_total': balance_total or '0.00',
                })
        return data
    
    def convert_name(self, cr, uid, ids, account, context=None):
        name = ''
        account_obj = self.pool.get('account.account')
        if account:
            context.update({'lang': 'ar_AR'})
            name = account_obj.browse(cr, uid, account.id, context=context).name
        return name
    
    def generate_records(self, cr, uid, ids, data, context=None):
        ar_name=''
        result = []
        accounts = []
        total_credit = 0.0
        total_debit = 0.0
        total_balance = 0.0
        if context is None:
            context = {}
            
        context['fiscalyear'] = data['fiscalyear']
        start_account_id = data['start_account_id']
        end_account_id = data['end_account_id']
        from_date = data['from_date']
        to_date = data['to_date']
        account_codes = data['account_codes']
        language = data['language']
        company_id = data['company_id']
        display_zero = data['display_zero']
        display_view = data['display_view']
        report_type = data['type']
        
        date_range = '[' + str(_convert_date(from_date)) + '-' + str(_convert_date(to_date)) + ']'
        if language == 'ar_AR':
            context.update({'lang': language})
        company = self.pool.get('res.company').browse(cr, uid, company_id).name
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscal_year = fiscalyear_obj.browse(cr, uid, data['fiscalyear'])
        cr.execute("SELECT id \
                    FROM account_move \
                    WHERE state='posted' AND skip_check is not true")
        move_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        cr.execute("SELECT id \
                    FROM account_period \
                    WHERE fiscalyear_id=%s AND special=True AND company_id=%s", (data['fiscalyear'], company_id))
        opening_period_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        cr.execute("SELECT id \
                    FROM account_period \
                    WHERE fiscalyear_id=%s AND special!=True AND company_id=%s", (data['fiscalyear'], company_id))
        other_period_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        print other_period_ids,"--------------->OTHER PERIOD IDS\n\n"
        acc_ids =[]
        account_obj = self.pool.get('account.account')
        ctx = context.copy()
        ctx['date_from'] = from_date
        ctx['date_to'] = to_date
#         if start_account_id and end_account_id:
#             for account in account_obj.browse(cr, uid, ids, context=ctx):
#                 total_credit += account.credit
#                 total_debit += account.debit
#             total_balance = round(total_debit, 2) - round(total_credit, 2)
#         else:
#             cr.execute("SELECT id FROM account_account where parent_id is NULL AND company_id=%s" % (company_id))
#             acc_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#             acc = account_obj.browse(cr, uid, acc_ids[0], context=ctx)
#             total_credit = acc.credit
#             total_debit = acc.debit
#             total_balance = round(total_debit, 2) - round(total_credit, 2)
        move_line_obj = self.pool.get('account.move.line')
        
        # To calculate opening balance of previous open fiscal years
        fiscal_date_start = fiscalyear_obj.browse(cr, uid, data['fiscalyear']).date_start
        prev_open_fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft'), ('date_start', '<', fiscal_date_start), ('company_id', '=', company_id)])
        print prev_open_fiscalyear_ids,">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n"
        prev_period_ids = []
        if len(prev_open_fiscalyear_ids) == 1:
            cr.execute("SELECT id \
                        FROM account_period \
                        WHERE fiscalyear_id =%s AND company_id=%s" % (prev_open_fiscalyear_ids[0], company_id))
        elif len(prev_open_fiscalyear_ids) > 1:
            cr.execute("SELECT id \
                        FROM account_period \
                        WHERE fiscalyear_id IN %s AND company_id=%s" , (tuple(prev_open_fiscalyear_ids), company_id))
        prev_period_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
        print prev_period_ids,"------------------------------------->\n\n"
#             self.pool.get('account.period').search(cr, uid, [('fiscalyear_id', 'in', prev_open_fiscalyear_ids)], context=context)
        for account in account_obj.browse(cr, uid, ids, context=context):
            if language == 'en_ar':
#                print "P"*100,account.name
                ar_name = self.convert_name(cr, uid, ids, account, context)
               
            ar_name = account.name +' '+ar_name
#            print ar_name
            open_balance = 0.0
            opening_debit = 0.0
            opening_credit = 0.0
            debit, credit, balance ,balance_debit, balance_credit = 0.0, 0.0, 0.0, 0.0, 0.0
            open_move_line_ids1, open_move_line_ids2, child_ids, move_line_ids, sum_list, prev_balance = [], [], [], [], [], []
            
            if account.type == 'view':
                child_ids = account_obj.search(cr, uid, [('parent_id','child_of', account.id)])
                open_move_line_ids1 = move_line_obj.search(cr, uid, [('period_id', 'in', opening_period_ids), ('account_id', 'in', child_ids), ('company_id', '=', company_id)])
                open_move_line_ids2 = move_line_obj.search(cr, uid, [('period_id', 'in', other_period_ids), ('date', '>=', fiscal_year.date_start), ('date', '<', from_date), ('account_id', 'in', child_ids), ('company_id', '=', company_id)])
                cr.execute("SELECT SUM(debit), SUM(credit) \
                            FROM account_move_line as move_line \
                            WHERE account_id IN %s AND period_id IN %s AND date>=%s AND date<=%s AND company_id=%s AND move_id IN \
                            (SELECT id FROM account_move WHERE state='posted' AND id=move_line.move_id AND skip_check is not true)", (tuple(child_ids), tuple(other_period_ids), from_date, to_date, company_id))
                sum_list = cr.fetchall()
                # For opening balances of previous open fiscal years
                if prev_period_ids:
                    cr.execute("SELECT SUM(debit), SUM(credit) \
                                FROM account_move_line AS move_line \
                                WHERE account_id IN %s AND period_id IN %s AND company_id=%s AND move_id IN \
                                (SELECT id FROM account_move WHERE state='posted' AND id=move_line.move_id AND skip_check is not true)", (tuple(child_ids), tuple(prev_period_ids), company_id))
                    prev_balance = cr.fetchall()
            else:
                open_move_line_ids1 = move_line_obj.search(cr, uid, [('period_id', 'in', opening_period_ids), ('account_id', '=', account.id), ('company_id', '=', company_id)])
                open_move_line_ids2 = move_line_obj.search(cr, uid, [('period_id', 'in', other_period_ids), ('date', '>=', fiscal_year.date_start), ('date', '<', from_date), ('account_id', '=', account.id), ('company_id', '=', company_id)])
                cr.execute("SELECT SUM(debit), SUM(credit) \
                            FROM account_move_line as move_line \
                            WHERE account_id=%s AND period_id IN %s AND date>=%s AND date<=%s AND company_id=%s AND move_id IN \
                            (SELECT id FROM account_move WHERE state='posted' AND id=move_line.move_id AND skip_check is not true)", (account.id, tuple(other_period_ids), from_date, to_date, company_id))
                sum_list = cr.fetchall()
                query = "SELECT SUM(debit), SUM(credit) \
                            FROM account_move_line as move_line \
                            WHERE account_id=%s AND period_id IN %s AND date>=%s AND date<=%s AND company_id=%s AND move_id IN \
                            (SELECT id FROM account_move WHERE state='posted' AND id=move_line.move_id AND skip_check is not true)"%(account.id, tuple(other_period_ids), from_date, to_date, company_id)
                print query
                print sum_list,"------------>SUM LIST"
                # For opening balances of previous open fiscal years
                if prev_period_ids:
                    cr.execute("SELECT SUM(debit),SUM(credit) \
                                FROM account_move_line AS move_line \
                                WHERE account_id=%s AND period_id IN %s AND company_id=%s AND move_id IN \
                                (SELECT id FROM account_move WHERE state='posted' AND id=move_line.move_id AND skip_check is not true)", (account.id, tuple(prev_period_ids), company_id))
                    prev_balance = cr.fetchall()
                    print prev_balance
            
#             if len(prev_balance) > 0:
            opening_debit += filter(None, map(lambda x:x[0], prev_balance)) and \
                                        filter(None, map(lambda x:x[0], prev_balance))[0] or 0.0
            opening_credit += filter(None, map(lambda x:x[1], prev_balance)) and \
                                        filter(None, map(lambda x:x[1], prev_balance))[0] or 0.0
            print opening_debit,"<------------->",opening_credit
            open_balance += opening_debit - opening_credit
            print open_balance
#                 global prev_bal
#                 prev_bal = open_balance
            
            for line in move_line_obj.browse(cr, uid, open_move_line_ids1):
                if line.move_id and line.move_id.state == 'posted':
                    print "\n\n", line.debit,"<<<>>>>", line.credit
                    opening_debit += line.debit
                    opening_credit += line.credit
                    open_balance += (line.debit - line.credit)
            for line in move_line_obj.browse(cr, uid, open_move_line_ids2):
                if line.move_id and line.move_id.state == 'posted':
                    print "\n\n", line.debit,"<<<>>>>", line.credit
                    opening_debit += line.debit
                    opening_credit += line.credit
                    open_balance += (line.debit - line.credit)
            debit = filter(None, map(lambda x:x[0], sum_list)) and filter(None, map(lambda x:x[0], sum_list))[0] or 0.0
            credit = filter(None, map(lambda x:x[1], sum_list)) and filter(None, map(lambda x:x[1], sum_list))[0] or 0.0
            if not account.parent_id:
                total_credit += credit
                total_debit += debit
            if (debit != 0.00 or credit != 0.00 or opening_debit != 0.00 or opening_credit != 0.00 or display_zero) and (account.type != 'view' or display_view):
                
                context.update({'from_date': from_date, 'to_date': to_date})
                balance = (opening_debit + debit) - (opening_credit + credit)
                if balance > 0.00:
                    balance_debit = balance
                elif balance < 0.00:
                    balance_credit = balance * -1
                account_level = account.level or 0
                account_name = account.name
#                 if account_level > 3:
                if report_type == 'summary':
                    account_name = "      " * (account_level) + account_name
                det_open_debit = det_open_credit = 0.00
                if open_balance > 0.00:
                    det_open_debit = open_balance
                elif open_balance < 0.00:
                    det_open_credit = open_balance * -1
                account_data = {
                    'code': account.code,
                    'name': account_name,
                    'debit': debit or '0.0',
                    'credit': credit or '0.0',
                    'balance': balance or '0.00',
                    'balance_debit': balance_debit or '0.00',
                    'balance_credit': balance_credit or '0.00',
                    'type': account.type,
                    'open_balance': open_balance or '0.0',
                    'opening_debit': det_open_debit or '0.0',
                    'opening_credit': det_open_credit or '0.0',
                    'total_credit': total_credit or '0.0',
                    'total_debit': total_debit or '0.0', 
                    'total_bal': round(total_debit, 2)-round(total_credit, 2) or '0.0',
                    'total_open_bal': '0.00',
                    'lang': language,
                    'translate' : ar_name,
                    'account_type': account.type
                    }
                accounts.append(account_data)
        accounts = sorted(accounts, key=operator.itemgetter('code'))
        report_data = {
            'accounts': accounts,
            'fiscal_year': fiscal_year.name,
            'date': date_range or '',
            'account': account_codes or '',
            'company': company or '',
            'type': data['type'],
            'lang': language
            }
        result.append(report_data)
#        self._get_sub_totals(cr, uid, data, context=context)
        return result
        
jasper_report.report_jasper('report.jasper_trial_balance', 'account.account', parser=jasper_trial_balance)
jasper_report.report_jasper('report.jasper_trial_balance_xls', 'account.account', parser=jasper_trial_balance)
jasper_report.report_jasper('report.jasper_trial_balance_detail', 'account.account', parser=jasper_trial_balance)
jasper_report.report_jasper('report.jasper_trial_balance_detail_xls', 'account.account', parser=jasper_trial_balance)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

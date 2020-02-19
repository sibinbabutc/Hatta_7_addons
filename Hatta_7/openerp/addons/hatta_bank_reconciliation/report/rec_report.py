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

from hatta_account import JasperDataParser
from jasper_reports import jasper_report

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator

class rec_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(rec_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        date_start = datetime.strptime(data['form']['from_date'], '%Y-%m-%d').strftime("%d/%m/%Y")
        date_end = datetime.strptime(data['form']['to_date'], '%Y-%m-%d').strftime("%d/%m/%Y")
        type = data['form']['type']
        starting_header = ''
        if type == 'reconciled':
            starting_header = 'RECONCILIATION'
        elif type == 'un_recon':
            starting_header = 'UNRECONCILED'
        else:
            starting_header = 'BANK RECONCILIATION'
        header = "%s REPORT AS ON %s"%(starting_header, str(date_end))
        run_date = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        vals = {
                'account_name': data['form']['bank_account_id'][1],
                'header': header,
                'company_name': user_obj.company_id.name or '',
                'run': run_date,
                'user_name': user_obj.name or ''
                }
        return vals
    
    def get_initial_balance(self, cr, uid, account_id, start_date, type):
        search_param = {
                'date_stop': start_date,
                'account_id': account_id,
            }
        sql = ("SELECT COALESCE(ml.amount_currency,0.0) as amount_currency, COALESCE(ml.debit,0.0) as debit, COALESCE(ml.credit,0.0) as credit, "
               "COALESCE(ml.bank_debit,0.0) as bank_debit, COALESCE(ml.bank_credit,0.0) as bank_credit, ml.rec_date as rec_date "
               "FROM account_move_line ml "
               "INNER JOIN account_account a "
               "ON a.id = ml.account_id "
               "WHERE ml.account_id = %(account_id)s and ml.date < %(date_stop)s")
#         if type == 'reconciled':
#             sql += (" and ml.rec_date is not null")
#         elif type == 'un_recon':
#             sql += (" and ml.rec_date is null")
        cr.execute(sql, search_param)
        return cr.dictfetchall()
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        move_line_pool = self.pool.get('account.move.line')
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        account_id = data['form']['bank_account_id'][0]
        type = data['form']['type']
        
        opening_bal_lines = self.get_initial_balance(cr, uid, account_id, from_date, type)
        opening_book_bal = 0.00
        opening_bank_bal = 0.00
        for line in opening_bal_lines:
            op_debit = 0.00
            op_credit = 0.00
            rec_date = line.get('rec_date', False)
            if rec_date and rec_date >= from_date:
                rec_date = False
            if line.get('amount_currency', False):
                if line['amount_currency'] < 0.00:
                    op_credit = line['amount_currency'] * -1
                else:
                    op_debit = line['amount_currency']
            else:
                op_credit = line.get('credit', 0.00)
                op_debit = line.get('debit', 0.00)
            op_bank_credit = 0.00
            op_bank_debit = 0.00
            if rec_date:
                op_bank_credit = line.get('bank_credit', 0.00)
                op_bank_debit = line.get('bank_debit', 0.00)
            balance = op_bank_debit - op_bank_credit
            op_proc = False
            if type == 'un_recon':
                op_proc = False
            elif type in ['all', 'reconciled']:
                op_proc = True
            if op_proc:
                opening_book_bal += (op_debit - op_credit)
                opening_bank_bal += (op_bank_debit - op_bank_credit)
        if opening_book_bal or opening_bank_bal:
            vals = {
                    'date': from_date and datetime.strptime(from_date, '%Y-%m-%d'),
                    'name': '',
                    'ref': '',
                    'book_bal': opening_book_bal,
                    'bank_bal': opening_bank_bal,
                    'remark': "OPENING BALANCE",
                    }
            result.append(vals)
        
        domain = [('move_id.state', '=', 'posted'),
                  ('account_id', '=', account_id),'|', '&',
                  ('date', '>=', from_date),
                  ('date', '<=', to_date), '&',
                  ('rec_date', '>=', from_date),
                  ('rec_date', '<=', to_date)]
#         if type == 'reconciled':
#             domain.append(('rec_date', '!=', False))
#         elif type == 'un_recon':
#             domain.append(('rec_date', '=', False))
        move_line_ids = move_line_pool.search(cr, uid, domain, order='date', context=context)
        for move_line_obj in move_line_pool.browse(cr, uid, move_line_ids, context=context):
            debit = 0.00
            credit = 0.00
            bank_credit = 0.00
            bank_debit = 0.00
            move_date = move_line_obj.date
            rec_date = move_line_obj.rec_date
            if rec_date and rec_date > to_date:
                rec_date = False
            if move_line_obj.amount_currency:
                if move_line_obj.amount_currency < 0.00:
                    credit = move_line_obj.amount_currency * -1
                else:
                    debit = move_line_obj.amount_currency
            else:
                debit = move_line_obj.debit or 0.00
                credit = move_line_obj.credit or 0.00
            if rec_date:
                bank_credit = move_line_obj.bank_credit
                bank_debit = move_line_obj.bank_debit
            bank_balance = bank_debit - bank_credit
            proceed = False
            if type == 'reconciled' and bank_balance != 0.00:
                proceed = True
            elif type == 'un_recon' and bank_balance == 0.00:
                proceed = True
            elif type == 'all':
                proceed = True
            if move_date < from_date:
                debit = 0.00
                credit = 0.00
            if proceed:
                vals = {
                        'date': move_line_obj.date and datetime.strptime(move_line_obj.date, '%Y-%m-%d'),
                        'name': move_line_obj.move_id.name or '',
                        'ref': move_line_obj.man_ref or move_line_obj.move_id.cheque_no or '',
                        'book_bal': debit - credit,
                        'bank_bal': bank_debit - bank_credit,
                        'remark': move_line_obj.name,
                        'bank_date': rec_date and datetime.strptime(rec_date, '%Y-%m-%d')
                        }
                result.append(vals)
        return result
    
jasper_report.report_jasper('report.bank.rec.jasper', 'rec.report.wizard', parser=rec_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

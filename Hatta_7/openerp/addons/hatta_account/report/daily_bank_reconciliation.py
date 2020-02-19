# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from hatta_account import JasperDataParser
from jasper_reports import jasper_report

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator


class daily_bank_reconciliation_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.balance_bank = 0.00
        self.dep_clear = 0.00
        self.balance_book = 0.00
        super(daily_bank_reconciliation_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        od_limit = 0.00
        bank_pool = self.pool.get('res.partner.bank')
        name = ''
        bank_id = data.get('bank_id', False)
        if bank_id:
            bank_obj = bank_pool.browse(cr, uid,bank_id, context=context)
            if bank_obj.account_type == 'od':
                od_limit = bank_obj.od_limit or 0.00
            acc_no = bank_obj.acc_number or ''
            name = acc_no[-4:]
        print self.balance_bank
        print self.balance_book
        print self.dep_clear,"::::::::::::::::"
        print od_limit
        return {
                'bank_bal': self.balance_bank or 0.00,
                'dep_clear': self.dep_clear or 0.00,
                'book_bal': self.balance_book or 0.00,
                'od_limit': od_limit or 0.00,
                'report' : "%s OD A/C RECONCILIATION AS ON %s"%(name, str(datetime.strptime(data['date'], '%Y-%m-%d').strftime("%d/%m/%Y"))),
                }
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
           'net.sf.jasperreports.export.xls.detect.cell.type' : 'true'
            }
        
#     def get_total_amt(self, cr, uid, move_clear_ids, context=None):
#         total_amt = 0
#         for move_clear in self.pool.get('account.move').browse(cr, uid, move_clear_ids, context=context):
#             total_amt+=move_clear.amount
#         return total_amt
#     
#     def get_od_limit(self, cr, uid, acc_bank, context=None):
#         od_limit = 0
#         comp_obj = self.pool.get('res.company').browse(cr, uid, uid, context=context)
#         for bank in comp_obj.bank_ids:
#             bank_acc = bank.bank_name + " " + bank.acc_number
#             if bank_acc == acc_bank:
#                 if bank.account_type == 'od':
#                     od_limit = bank.od_limit
#                 else:
#                     od_limit = 0.00
#         return od_limit
#     
#     def get_total_less(self, cr, uid, move_ids, account, context=None):
#         total_less = 0
#         move_pool = self.pool.get('account.move')
#         
#         for move_clear in move_pool.browse(cr, uid, move_ids, context=context):
#             for move_line in move_clear.line_id:
#                 if move_line.account_id.id == account:
#                     if not move_clear.cheque_no:
#                         less = move_line.debit-move_line.credit
#                         total_less+=less
#         return total_less
    
    def get_bank_accounts(self, cr, uid, ids, bank_id, context=None):
        res = []
        bank_pool = self.pool.get('res.partner.bank')
        if bank_id:
            bank_obj = bank_pool.browse(cr, uid,bank_id, context=context)
            if bank_obj.journal_id:
                if bank_obj.journal_id.default_debit_account_id:
                    res.append(bank_obj.journal_id.default_debit_account_id.id)
                if bank_obj.journal_id.default_credit_account_id:
                    res.append(bank_obj.journal_id.default_credit_account_id.id)
        return list(set(res))
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        move_line_pool = self.pool.get('account.move.line')
        total_amt, add_total, less_total, total_less, od_limit = 0,0,0,0,0
        sub_report = []
        bank_id = data.get('bank_id', False)
        bank_account_ids = self.get_bank_accounts(cr, uid, ids, bank_id, context=context)
        if bank_account_ids:
            move_line_ids = move_line_pool.search(cr, uid, [('account_id', 'in', bank_account_ids),
                                                            ('move_id.skip_check', '=', False),
                                                            ('date', '<=', data.get('date', False))],
                                                  context=context)
            for move_line in move_line_pool.browse(cr, uid, move_line_ids, context=context):
                balance = move_line.debit - move_line.credit
                self.balance_book += balance
                if move_line.move_id.check_cleared:
                    self.balance_bank += balance
                else:
                    if move_line.move_id.cheque_no:
                        vals = {
                                'cheque_no': move_line.move_id.cheque_no,
                                'amount': abs(balance)
                                }
                        if balance > 0.00:
                            vals['group'] = 'Add: Deposit O/S in Bank'
                        else:
                            vals['group'] = 'Less" Withdrawals O/S in Bank [Chqs]'
                        result.append(vals)
        
        
        
        
        
        
        
        
        
#         move_pool = self.pool.get('account.move')
#         
#         od_limit = self.get_od_limit(cr, uid, data.get('account_id'), context=context)
#         
#         move_clear_ids = move_pool.search(cr, uid, [('check_cleared', '=', True)], context=context)
#         if move_clear_ids:
#             total_amt = self.get_total_amt(cr, uid, move_clear_ids, context=context)
#             for move_clear in move_pool.browse(cr, uid, move_clear_ids, context=context):
#                 if move_clear.cheque_no:
#                     for move_line in move_clear.line_id:
#                         if move_line.account_id.id == data.get('account_id') :
#                             vals = {
#                                     'report' : "%s OD A/C RECONCILIATION AS ON %s"%(data.get('account_id'),datetime.strptime(data.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")),
#                                     'balance_bank' : total_amt or "0.00",
#                                     'balance_book' :  (total_amt + add_total) - less_total or "0.00",
#                                     'od_limit' : od_limit or "0.00",
#                                     'amt_available' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'net_funds' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'sub_report' : [],
#                                         }
#                             
#                             if move_line.debit: 
#                                 add_debit = move_line.debit
#                                 add_total += add_debit
#                                 vals.update({
#                                     'report' : "%s OD A/C RECONCILIATION AS ON %s"%(data.get('account_id'),datetime.strptime(data.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")),
#                                     'balance_bank' : total_amt or "0.00",
#                                     'cheque_no' : move_clear.cheque_no,
#                                     'add_debit' : add_debit or "0.00",
#                                     'less_total' : less_total or "0.00",
#                                     'balance_book' :  (total_amt + add_total) - less_total or "0.00",
#                                     'od_limit' : od_limit or "0.00",
#                                     'total_less' : total_less or "0.00",
#                                     'amt_available' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'net_funds' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                         })
#                                 
#                             else:
#                                 less_credit = move_line.credit
#                                 less_total+= less_credit
#                                 less_vals = {
#                                      'lcheque_no' : move_clear.cheque_no,
#                                      'less_credit' : less_credit or "0.00",
#                                      'less_total' : less_total or "0.00",
#                                              }
#                                 sub_report.append(less_vals)
#                             result.append(vals)  
#                                   
#                         else:
#                             vals = {
#                                     'report' : "%s OD A/C RECONCILIATION AS ON %s"%(data.get('account_id'),datetime.strptime(data.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")),
#                                     'balance_bank' : total_amt or "0.00",
#                                     'balance_book' :  (total_amt + add_total) - less_total or "0.00",
#                                     'od_limit' : od_limit or "0.00",
#                                     'less_total' : less_total or "0.00",
#                                     'amt_available' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'total_less' : total_less or "0.00",
#                                     'net_funds' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'total_less' : total_less,
#                                             }
#                             result.append(vals)
#                                 
#                 else:
#                     for move_line in move_clear.line_id:
#                         if move_line.account_id.id == data.get('account_id') :
#                             if not move_clear.cheque_no:
#                                 less = move_line.debit-move_line.credit
#                                 total_less+=less
#                                 vals = {
#                                     'report' : "%s OD A/C RECONCILIATION AS ON %s"%(data.get('account_id'),datetime.strptime(data.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")),
#                                     'balance_bank' : total_amt or "0.00",
#                                     'balance_book' :  (total_amt + add_total) - less_total or "0.00",
#                                     'od_limit' : od_limit or "0.00",
#                                     'less_total' : less_total or "0.00",
#                                     'amt_available' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'total_less' : total_less or "0.00",
#                                     'net_funds' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                                     'total_less' : total_less,
#                                             }
#                                 result.append(vals)
#         else:
#             vals = {
#                 'report' : "%s OD A/C RECONCILIATION AS ON %s"%(data.get('account_id'),datetime.strptime(data.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")),
#                 'balance_bank' : total_amt or "0.00",
#                 'balance_book' :  (total_amt + add_total) - less_total or "0.00",
#                 'less_total' : less_total or "0.00",
#                 'od_limit' : od_limit or "0.00",
#                 'total_less' : total_less or "0.00",
#                 'amt_available' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                 'net_funds' : ((total_amt + add_total) - less_total) + od_limit or "0.00",
#                         }
#             result.append(vals)
#         for r in result:
#             if r.get('sub_report'):
#                 r.update({
#                           'sub_report':sub_report
#                       })
        result = sorted(result, key=operator.itemgetter('group'))
        return result
    
jasper_report.report_jasper('report.daily_bank_reconciliation_jasper', 'daily.bank.reconciliation.wizard', parser=daily_bank_reconciliation_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
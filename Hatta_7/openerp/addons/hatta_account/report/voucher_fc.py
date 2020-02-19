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


class voucher_report_fc(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(voucher_report_fc, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        pool= pooler.get_pool(cr.dbname)
        user_pool = pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        return {
                'company_name': user_obj.company_id.name or '',
                'current_date_time': date_start
                }
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        pool= pooler.get_pool(cr.dbname)
        move_pool = pool.get('account.move')
        currency_pool = pool.get('res.currency')
        user_pool = pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_currency_obj = user_obj.company_id.currency_id
        for move_obj in move_pool.browse(cr, uid, ids, context=context):
            journal = move_obj.journal_id or False
#             journal_curr = journal.currency and journal.currency or company_currency_obj
            amount = 0.00
            tot_amount = 0.00
            lines = []
            reconsile_objs = []
            customer_list = []
            sett_lines = []
            curr_id = [x.currency_id for x in move_obj.line_id if x.currency_id]
            journal_curr = curr_id and curr_id[0] or company_currency_obj
            for line in move_obj.line_id:
                if line.partner_id:
                    customer_list.append(line.partner_id)
                sub_ledger = line.job_id and line.job_id.name or ''
                partner_name = line.partner_id and line.partner_id.name or False
                partner_code = line.partner_id and line.partner_id.partner_ac_code or False
                if line.partner_id:
                    sub_ledger = partner_name
                    if partner_code:
                        sub_ledger = "[%s] %s"%(partner_code, partner_name)
                cheque_no = move_obj.cheque_no or ''
                if move_obj.journal_id.voucher_no_as_ref:
                    cheque_no = move_obj.name or ''
                if line.man_ref:
                    cheque_no = line.man_ref or ''
                amount_currency = line.amount_fc_temp and line.amount_fc_temp or 0.00
                if line.debit != 0.00:
                    tot_amount += abs(amount_currency or 0.00)
                line_vals = {
                             'account_code': line.account_id.code or '',
                             'account_name': line.account_id.name.upper() or '',
                             'partner_code': line.partner_id and line.partner_id.partner_ac_code or '',
                             'partner_name': line.partner_id and line.partner_id.name or '',
                             'sub_ledger': sub_ledger,
                             'ref': cheque_no,
                             'debit': line.debit or 0.00,
                             'credit': line.credit or 0.00,
                             'fc_amount': amount_currency,
                             'remark': line.name or '',
                             'cc': line.analytic_account_id and line.analytic_account_id.code or ''
                             }
                lines.append(line_vals)
                if line.voucher_id:
                    line_cr = []
                    for vou_line in line.voucher_id.line_cr_ids:
                        if vou_line.move_line_id and vou_line.amount != 0.00 and vou_line.move_line_id.id != line.id:
                            rec_line = vou_line.move_line_id
                            invoice_date = False
                            if rec_line.invoice:
                                doc_no = rec_line.invoice and rec_line.invoice.number or ''
                            else:
                                doc_no = rec_line.doc_no
                            amount = vou_line.amount
                            print vou_line.type
                            if rec_line.invoice:
#                                 doc_no = ''
                                invoice_date = datetime.strptime(rec_line.invoice.date_invoice, '%Y-%m-%d')
                            rec_vals = {
                                        'date': rec_line.date and datetime.strptime(rec_line.date, '%Y-%m-%d'),
                                        'doc_no': doc_no,
                                        'amount': abs(amount),
                                        'amount_real': amount,
                                        'c_r': vou_line.type == 'cr' and 'C' or 'D',
                                        'remark': rec_line.name or '',
                                        'inv_no': rec_line.invoice and rec_line.invoice.number or '',
                                        'inv_date': invoice_date or '',
                                        }
                            line_cr.append(rec_vals)
                        if vou_line.move_line_id and vou_line.move_line_id.id == line.id:
                            line_cr = []
                            break
                    line_dr = []
                    for vou_line in line.voucher_id.line_dr_ids:
                        if vou_line.move_line_id and vou_line.amount != 0.00 and vou_line.move_line_id.id != line.id:
                            rec_line = vou_line.move_line_id
                            invoice_date = False
                            if rec_line.invoice:
                                doc_no = rec_line.invoice and rec_line.invoice.number or ''
                            else:
                                doc_no = rec_line.doc_no
                            amount = vou_line.amount
                            if rec_line.invoice:
#                                 doc_no = ''
                                invoice_date = datetime.strptime(rec_line.invoice.date_invoice, '%Y-%m-%d')
                            rec_vals = {
                                        'date': rec_line.date and datetime.strptime(rec_line.date, '%Y-%m-%d'),
                                        'doc_no': doc_no,
                                        'amount': abs(amount),
                                        'amount_real': amount,
                                        'c_r': vou_line.type == 'cr' and 'C' or 'D',
                                        'remark': rec_line.name or '',
                                        'inv_no': rec_line.invoice and rec_line.invoice.number or '',
                                        'inv_date': invoice_date or '',
                                        }
                            line_dr.append(rec_vals)
                        elif vou_line.move_line_id and vou_line.move_line_id.id == line.id:
                            line_dr = []
                            break
                    sett_lines.extend(line_cr)
                    sett_lines.extend(line_dr)
            sett_lines = [dict(t) for t in set([tuple(d.items()) for d in sett_lines])]
            sett_lines = sorted(sett_lines, key=operator.itemgetter('date'))
            amount_curr = currency_pool.amount_word(cr, uid, journal_curr, tot_amount or 0.00,
                                                    context=context)
            bank_name = move_obj.bank_details or ''
            vals = {
                    'journal_label': journal and journal.voucher_label or '',
                    'voucher_code': journal.code or '',
                    'voucher_name': move_obj.name or '',
                    'amount_total': tot_amount or "0.00",
                    'date': move_obj.date and datetime.strptime(move_obj.date, '%Y-%m-%d'),
                    'partner': move_obj.journal_partner_id and move_obj.journal_partner_id.name.upper() or '',
                    'ref': move_obj.ref or '',
                    'amount_in_words': amount_curr and amount_curr.upper() or '',
                    'bank': bank_name,
                    'check_no': move_obj.display_check_details and move_obj.cheque_no or '',
                    'check_date': move_obj.display_check_details and move_obj.cheque_date and datetime.strptime(move_obj.cheque_date, '%Y-%m-%d'),
                    'curr_name': journal_curr.name == 'AED' and "DIRHAMS" or journal_curr.name,
                    'user_name': user_obj.name.upper() or '',
                    'sett_lines': sett_lines
                    }
            
            vals['move_lines'] = lines
            result.append(vals)
        return result
    
jasper_report.report_jasper('report.voucher.report.jasper.fc', 'account.move', parser=voucher_report_fc)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

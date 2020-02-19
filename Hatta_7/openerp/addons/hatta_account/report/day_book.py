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


class day_book_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.credit_sum = 0.00
        self.debit_sum = 0.00
        super(day_book_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true',
            'net.sf.jasperreports.export.xls.detect.cell.type': 'true',
            'net.sf.jasperreports.export.xls.white.page.background': 'true',
            'net.sf.jasperreports.export.xls.show.gridlines': 'true',
            }
    
    def generate_parameters(self, cr, uid, ids, data, context):
        journal_pool = self.pool.get('account.journal')
        journal_id = data['form']['journal_id'][0]
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        journal_obj = journal_pool.browse(cr, uid, journal_id, context=context)
        voucher_label = journal_obj.voucher_label or journal_obj.name or ''
        date_list = []
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        vals = {
                'from_date': datetime.strptime(data['form']['from_date'], '%Y-%m-%d').strftime("%d/%m/%Y"),
                'to_date': datetime.strptime(data['form']['to_date'], '%Y-%m-%d').strftime("%d/%m/%Y"),
                'voucher_name': journal_obj.code + " - " + voucher_label,
                'voucher_label': voucher_label,
                'company_name': user_obj.company_id.name or '',
                'run': date_start,
                'debit_sum': self.debit_sum,
                'credit_sum': self.credit_sum
                }
        if data['report_type']=='xls':
            vals.update({'IS_IGNORE_PAGINATION':True})
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        if data is None:
            data = {}
        move_pool = self.pool.get('account.move')
        form_data = data['form']
        journal_id = form_data['journal_id'][0]
        print_opt = form_data['print_opt']
        domain = [('journal_id', '=', journal_id), ('skip_check', '=', False)]
        if form_data.get('from_date', False):
            domain.append(('date', '>=', form_data['from_date']))
        if form_data.get('to_date', False):
            domain.append(('date', '<=', form_data['to_date']))
        if print_opt == 'posted': 
            domain.append(('state', '=', 'posted'))
        elif print_opt == 'cancel':
            domain.append(('state', '=', 'draft'))
        move_ids = move_pool.search(cr, uid, domain, context=context)
        debit_sum = 0.00
        credit_sum = 0.00
        for move_obj in move_pool.browse(cr, uid, move_ids, context=context):
            lines = []
            for line in move_obj.line_id:
                job_no_obj = line.job_id or False
                debit_sum += line.debit or 0.00
                credit_sum += line.credit or 0.00
                line_vals = {
                             'account_code': line.account_id.code or '',
                             'account_name': line.account_id.name or '',
                             'job_no': job_no_obj and job_no_obj.name or '',
                             'job_desc': job_no_obj and job_no_obj.job_short_desc or '',
                             'debit': line.debit or 0.00,
                             'credit': line.credit or 0.00,
                             'narr': line.name or '',
                             'cost_center': line.analytic_account_id and line.analytic_account_id.code or '',
                             'voucher_code': move_obj.journal_id.code or ''
                             }
                lines.append(line_vals)
            write_uid = move_obj.write_uid
            write_date = move_obj.write_date
            w_uid = False
            w_date = False
            if write_date != move_obj.create_date or write_uid != move_obj.create_uid:
                w_uid = write_uid
                w_date = write_date
            vals = {
                    'name': move_obj.name or '',
                    'name_float': move_obj.int_seq or 0.00,
                    'date': move_obj.date and datetime.strptime(move_obj.date, '%Y-%m-%d'),
                    'user': move_obj.create_uid and move_obj.create_uid.name.upper() or '',
                    'cheque_no': move_obj.cheque_no or '',
                    'cheque_date': move_obj.cheque_date and datetime.strptime(move_obj.cheque_date, '%Y-%m-%d'),
                    'amount': move_obj.cheque_amt or "0.00",
                    'lines': lines,
                    'write_date': w_date and datetime.strptime(w_date, '%Y-%m-%d %H:%M:%S'),
                    'write_uid': w_uid and w_uid.name or '',
                    'debit_sum': debit_sum,
                    'credit_sum': credit_sum,
                    'voucher_code': move_obj.journal_id.code or ''
                    }
            result.append(vals)
        self.debit_sum = debit_sum
        self.credit_sum = credit_sum
        if data['form']['sort_based_on'] == 'date':
            result = sorted(result, key=operator.itemgetter('date','name'))
        elif data['form']['sort_based_on'] == 'seq':
            result = sorted(result, key=operator.itemgetter('name_float'))
        return result
    
jasper_report.report_jasper('report.day.book.jasper', 'day.book.wizard', parser=day_book_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

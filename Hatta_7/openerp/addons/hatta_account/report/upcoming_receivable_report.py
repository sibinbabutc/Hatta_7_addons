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
from collections import defaultdict
from jasper_reports import jasper_report

from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator

class upcoming_receivable_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(upcoming_receivable_report, self).__init__(cr, uid, ids, data, context)
        
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
    
    def generate_parameters(self, cr, uid, ids, data, context=None):
        vals={}
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        date_from = data['form']['from_date']
        from_date = date_from and datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y") or ''
        date_to = data['form']['to_date']
        to_date = date_to and datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y") or ''
        report_heading = "Upcoming Receivable Report (%s - %s)"%(from_date,to_date)
        vals = {
            'company_name': comp_obj.name or '',
            'company_address': address,
            'company_email': "E-mail: " + comp_obj.email or '',
            'report_heading': report_heading,
                }
        return vals
    
    def _get_total_amt_aed(self, cr, uid, move_line_ids, context=None):
        total_amt_aed = 0
        move_line_pool = self.pool.get('account.move.line')
        if move_line_ids:
            for move_line in move_line_pool.browse(cr, uid, move_line_ids, context=context):
                debit = move_line.debit or 0.00
                credit = move_line.credit or 0.00
                amt_aed = (debit - credit) or 0.00
                total_amt_aed += amt_aed or 0.00
        return total_amt_aed
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        move_line_pool = self.pool.get('account.move.line')
        if data:
            condition = []
            condition.append(('account_id.type','=','receivable'))
            condition.append(('reconcile_id','=',False))
            condition.append(('debit', '>', 0.00))
            condition.append(('partner_id', '!=', False))
            condition.append(('move_id.skip_check', '=', False))
            if data['form']['from_date']:
                condition.append(('date', '>=', data['form']['from_date']))
            if data['form']['to_date']:
                condition.append(('date', '<=', data['form']['to_date']))
            if data['form']['party_id']:
                condition.append(('partner_id.id', '=', data['form']['party_id'][0]))
            if data['form']['due_date_from']:
                condition.append(('date_maturity', '>=', data['form']['due_date_from']))
            if data['form']['due_date_to']:
                condition.append(('date_maturity', '<=', data['form']['due_date_to']))
            move_line_ids = move_line_pool.search(cr, uid, condition, context=context)
            if move_line_ids:
                for move_line in move_line_pool.browse(cr, uid, move_line_ids, context=context):
                    if move_line.date:
                        date = datetime.strptime(move_line.date, "%Y-%m-%d")
                    else:
                        date = ''
                    debit = move_line.debit or 0.00
                    credit = move_line.credit or 0.00
                    total_amt_aed = self._get_total_amt_aed(cr, uid, move_line_ids, context=context)
                    if move_line.date_maturity:
                        due_date = datetime.strptime(move_line.date_maturity, "%Y-%m-%d")
                    else:
                        due_date = ''
                    
                    vals = {
                        'voucher_no' : move_line.move_line_name or '',
                        'voucher_date' : date,
                        'party_name' : move_line.partner_id and move_line.partner_id.name or '',
                        'job_id' : move_line.job_id and move_line.job_id.name or '',
                        'narration' : move_line.name or '',
                        'currency' : move_line.currency_id and move_line.currency_id.name or '',
                        'amt_fc' : abs(move_line.amount_currency) or "0.00",
                        'amt_aed' : abs(debit - credit) or "0.00",
                        'due_date' : due_date,
                        'total_amt_aed' : abs(total_amt_aed)
                            }
                    result.append(vals)
        result = sorted(result, key=operator.itemgetter('voucher_date'))
        return result
    
    
    
jasper_report.report_jasper('report.upcoming_receivable_report.jasper', 'wizard.upcoming.receivable', parser=upcoming_receivable_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
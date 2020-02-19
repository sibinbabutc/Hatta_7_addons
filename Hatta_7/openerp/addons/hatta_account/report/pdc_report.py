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
from openerp.tools.safe_eval import safe_eval
import operator


class pdc_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(pdc_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context=None):
        vals={}
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        if data['form']['from_date']:
            date_from = data['form']['from_date']
            from_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            from_date = ''
        if data['form']['to_date']:
            date_to = data['form']['to_date']
            to_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:
            to_date = ''
        if data['form']['type']:
            if data['form']['type'] == 'receivable':
                header = "PDC Receivable Report"
            elif data['form']['type'] == 'payable':
                header = "PDC Payable Report"
        else:
            header = "PDC Report"
        report_heading = "%s (%s - %s)"%(header,from_date,to_date)
        report = 'PDC Report'
        if not (data['form']['to_clear'] and data['form']['cleared']):
            if data['form']['to_clear']:
                report = "PDC To Clear Report"
            if data['form']['cleared']:
                report = "PDC Cleared Report"
        else:
            report = "PDC Report"
        vals = {
            'company_name': comp_obj.name or '',
            'company_address': address,
            'company_email': "E-mail: " + comp_obj.email or '',
            'report_heading': report_heading,
            'report' : report or ''
                }
        return vals
    
    def _get_total_amount(self, cr, uid, move_list, context=None):
        total_amt = 0
        for move in self.pool.get('account.move').browse(cr, uid, move_list, context=context):
            amount = move.cheque_amt
            total_amt+=amount
        return total_amt
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        account_id = ''
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        icp = self.pool.get('ir.config_parameter')
        if data:
            
            condition = []
            condition.append(('journal_id.display_in_voucher','=',True))
            condition.append(('state','=','posted'))
            condition.append(('cheque_type','=','pdc'))
            condition.append(('skip_check','=',False))
            
            domain = []
            if data['form']['from_date']:
                domain.append(('date', '>=', data['form']['from_date']))
            if data['form']['to_date']:
                domain.append(('date', '<=', data['form']['to_date']))
                
            if not (data['form']['to_clear'] and data['form']['cleared']):
                if data['form']['to_clear']:
                    domain.append(('move_id.cheque_released', '=', False))
                if data['form']['cleared']:
                    domain.append(('move_id.cheque_released', '=', True))
                    
            if data['form']['type']:
                if data['form']['type'] == 'receivable':
                    account_id = safe_eval(icp.get_param(cr, uid,
                                         'hatta_account.pdc_rec_account', 'False'))
                elif data['form']['type'] == 'payable':
                    account_id = safe_eval(icp.get_param(cr, uid,
                                                         'hatta_account.pdc_issue_account', 'False'))
            domain.append(('account_id', '=', account_id))
            
            move_line_ids = move_line_pool.search(cr, uid, domain, context=context)
            move_ids = [move_lines.move_id.id for move_lines in move_line_pool.browse(cr, uid, move_line_ids, context=context) if move_line_ids]
            condition.append(('id','in', move_ids))
            move_list = move_pool.search(cr, uid, condition, context=context)
            if move_list:
                for mv in move_pool.browse(cr, uid, move_list, context=context):
                    if mv.date:
                        voucher_date = datetime.strptime(mv.date, "%Y-%m-%d")
                    else:
                        voucher_date = ''
                    if mv.cheque_date:
                        cheque_date = datetime.strptime(mv.cheque_date, "%Y-%m-%d")
                    else:
                        cheque_date = ''
                    if mv.journal_partner_id and mv.journal_partner_id.partner_ac_code:
                        party = "[" + mv.journal_partner_id.partner_ac_code + "] " + mv.journal_partner_id.name
                    elif mv.journal_partner_id:
                        party = mv.journal_partner_id.name
                    else:
                        party = ''
                    if mv.release_date:
                        release_date = datetime.strptime(mv.release_date, "%Y-%m-%d")
                    else:
                        release_date = ''
                    total_amt = self._get_total_amount(cr, uid, move_list)
                    vals = {
                        'voucher_no' : mv.name or '',
                        'voucher_date' : voucher_date,
                        'cheque_no' : mv.cheque_no or '',
                        'cheque_date' : cheque_date,
                        'party' : party,
                        'bank' : mv.bank_account_id and mv.bank_account_id.name,
                        'release_date' : release_date,
                        'amount' : mv.cheque_amt or "0.00",
                        'total_amt' : total_amt or "0.00"
                            }
                    result.append(vals)
        result = sorted(result, key=operator.itemgetter('voucher_date'))
        return result

jasper_report.report_jasper('report.pdc_report.jasper', 'wizard.pdc.report', parser=pdc_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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


class sale_purchase_analysis(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(sale_purchase_analysis, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)
        date_list = []
        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
            date_list.append(str(start_date))
        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
            date_list.append(str(end_date))
        report_name_sub = ""
        if date_list:
            report_name_sub = "(%s)"%(str(" - ".join(date_list)))
        vals = {
                'company_name': comp_obj.name or '',
                'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                'report_name': "SALES AND PURCHASES ANALYSIS %s"%(report_name_sub)
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        invoice_pool = self.pool.get('account.invoice')
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        job_id = data['form']['job_id']
        domain = [('state', 'not in', ['draft', 'cancel']), ('type', 'in', ('in_invoice','out_invoice'))]
        if job_id:
            domain.append(('job_id', '=', job_id[0]))
        if date_from:
            domain.append(('date_invoice', '>=', date_from))
        if date_to:
            domain.append(('date_invoice', '<=', date_to))
        invoice_ids = invoice_pool.search(cr, uid, domain, context=context)
        for invoice_obj in invoice_pool.browse(cr, uid, invoice_ids, context=context):
            partner_obj = invoice_obj.partner_id
            partner_code = invoice_obj.parent_partner_id.partner_ac_code or \
                                invoice_obj.partner_id.partner_ac_code or ''
            if invoice_obj.partner_id != invoice_obj.parent_partner_id:
                partner_name = "%s, %s"%(invoice_obj.partner_id.name, invoice_obj.parent_partner_id.name)
            else:
                partner_name = partner_obj.name or ''
#             partner = partner_code and "[%s] %s"%(partner_code, partner_name) or partner_name
            lpo = invoice_obj.purchase_id and invoice_obj.purchase_id.name or \
                        invoice_obj.name or ''
            if invoice_obj.self_billing_num:
                lpo = "%s[%s]"%(lpo, invoice_obj.self_billing_num)
            exchange_rate = invoice_obj.exchange_rate or 1.0000
            if invoice_obj.currency_id != invoice_obj.company_id.currency_id:
                fc_amount = invoice_obj.amount_total
                residual = 0.0
                net_so = 0.0
                debit = 0.0
                credit = 0.0
                if invoice_obj.move_id:
                    for move_line in invoice_obj.move_id.line_id:
                        if move_line.account_id.type in ['receivable','payable']:
                            debit += move_line.debit
                            credit += move_line.credit
                net_so = abs(debit - credit)
            else:
                net_so = invoice_obj.amount_total
            if invoice_obj.type == 'in_invoice': 
                vals = {
                        'transaction_type': invoice_obj.transaction_type_id and \
                                                invoice_obj.transaction_type_id.name or '',
                        'name': invoice_obj.number or invoice_obj.internal_number or '',
                        'date': invoice_obj.date_invoice and \
                                        datetime.strptime(invoice_obj.date_invoice, '%Y-%m-%d'),
                        'cost_center': invoice_obj.cost_center_id and invoice_obj.cost_center_id.code or '',
                        'suppl_code': partner_code or '',
                        'partner': partner_name or '',
                        'job': invoice_obj.job_id and invoice_obj.job_id.name or 'Job Undefined',
                        'lpo': lpo or '',
                        'curr': invoice_obj.currency_id and invoice_obj.currency_id.name or '',
                        'net': invoice_obj.amount_total or "0.00",
                        'balance': (invoice_obj.amount_total * exchange_rate) or "0.00",
                        'net_so': net_so or '0.00',
                        'type': 'Purchases',
                        }
                result.append(vals)
            if invoice_obj.type == 'out_invoice': 
                fc_amount = 0.0
                if invoice_obj.currency_id != invoice_obj.company_id.currency_id:
                    fc_amount = invoice_obj.amount_total
                vals = {
                        'transaction_type': invoice_obj.transaction_type_id and \
                                                invoice_obj.transaction_type_id.name or '',
                        'name': invoice_obj.number or invoice_obj.internal_number or '',
                        'date': invoice_obj.date_invoice and \
                                        datetime.strptime(invoice_obj.date_invoice, '%Y-%m-%d'),
                        'cost_center': invoice_obj.cost_center_id and invoice_obj.cost_center_id.code or '',
                        'suppl_code': partner_code or '',
                        'partner': partner_name or '',
                        'job': invoice_obj.job_id and invoice_obj.job_id.name or 'Job Undefined',
                        'lpo': lpo or '',
                        'curr': invoice_obj.currency_id and invoice_obj.currency_id.name or '',
                        'net': fc_amount or "0.00",
                        'balance': (invoice_obj.amount_total * exchange_rate) or "0.00",
                        'net_so': net_so or '0.00',
                        'type': 'Sales',
                        }
                result.append(vals)
        result = sorted(result, key=itemgetter('job','type','transaction_type','name'))
#         result = sorted(result, key=itemgetter('type'))
        return result
    
jasper_report.report_jasper('report.sale.purchase.analysis.jasper', 'sale.purchase.analysis', parser=sale_purchase_analysis)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

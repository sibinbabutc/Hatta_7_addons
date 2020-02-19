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


class inv_summary(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(inv_summary, self).__init__(cr, uid, ids, data, context)
        
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
                'report_name': "INVOICE SUMMARY %s"%(report_name_sub)
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        invoice_pool = self.pool.get('account.invoice')
        invoice_id = data['form']['inv_id']
        transaction_type_id = data['form']['transaction_type_id']
        partner_id = data['form']['partner_id']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        if invoice_id:
            invoice_ids = [invoice_id[0]]
        else:
            domain = [('state', 'not in', ['draft', 'cancel']), ('type', '=', 'out_invoice')]
            if transaction_type_id:
                domain.append(('transaction_type_id', '=', transaction_type_id[0]))
            if partner_id:
                domain.append('|', ('partner_id', '=', partner_id[0]), ('parent_partner_id', '=', partner_id[0]))
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
            partner = partner_code and "[%s] %s"%(partner_code, partner_name) or partner_name
            lpo = invoice_obj.name
            if invoice_obj.self_billing_num:
                lpo = "%s[%s]"%(lpo, invoice_obj.self_billing_num)
            fc_amount = 0.0
            if invoice_obj.currency_id != invoice_obj.company_id.currency_id:
                fc_amount = invoice_obj.amount_total
                residual = 0.0
                net = 0.0
                debit = 0.0
                credit = 0.0
                if invoice_obj.move_id:
                    for move_line in invoice_obj.move_id.line_id:
                        if move_line.account_id.type in ['receivable','payable']:
                            debit += move_line.debit
                            credit += move_line.credit
                net = abs(debit - credit)
                print("llll",fc_amount,net)
                [p]
                exchange_rate = net/fc_amount
                residual = exchange_rate * invoice_obj.residual
            else:
                net = invoice_obj.amount_total
                residual = invoice_obj.residual
            vals = {
                    'transaction_type': invoice_obj.transaction_type_id and \
                                            invoice_obj.transaction_type_id.name or '',
                    'name': invoice_obj.number or invoice_obj.internal_number or '',
                    'date': invoice_obj.date_invoice and \
                                    datetime.strptime(invoice_obj.date_invoice, '%Y-%m-%d'),
                    'cost_center': invoice_obj.cost_center_id and invoice_obj.cost_center_id.code or '',
                    'customer': partner,
                    'job': invoice_obj.job_id and invoice_obj.job_id.name or '',
                    'lpo': lpo or '',
                    'curr': invoice_obj.currency_id and invoice_obj.currency_id.name or '',
                    'net': net or "0.00",
                    'fc_amount': fc_amount or "0.00",
                    'balance': residual or "0.00"
                    }
            
            result.append(vals)
        result = sorted(result, key=itemgetter("transaction_type", "name"))
        return result
    
jasper_report.report_jasper('report.inv.summary.jasper', 'invoice.summary', parser=inv_summary)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

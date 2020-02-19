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


class purchase_inv_summary(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(purchase_inv_summary, self).__init__(cr, uid, ids, data, context)
        
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
                'report_name': "PURCHASE INVOICE SUMMARY %s"%(report_name_sub)
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        invoice_pool = self.pool.get('account.invoice')
        invoice_id = data['form']['inv_id']
#         transaction_type_id = data['form']['transaction_type_id']
        partner_id = data['form']['partner_id']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        sort_based_on = data['form']['sort_based_on']
        if invoice_id:
            invoice_ids = [invoice_id[0]]
        else:
            domain = [('state', 'not in', ['draft', 'cancel']), ('type', '=', 'in_invoice')]
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
#             partner = partner_code and "[%s] %s"%(partner_code, partner_name) or partner_name
            lpo = invoice_obj.purchase_id and invoice_obj.purchase_id.name or \
                        invoice_obj.name or ''
            if invoice_obj.self_billing_num:
                lpo = "%s[%s]"%(lpo, invoice_obj.self_billing_num)
            exchange_rate = invoice_obj.exchange_rate or 1.0000
            vals = {
                    'transaction_type': invoice_obj.transaction_type_id and \
                                            invoice_obj.transaction_type_id.name or '',
                    'name': invoice_obj.number or invoice_obj.internal_number or '',
                    'date': invoice_obj.date_invoice and \
                                    datetime.strptime(invoice_obj.date_invoice, '%Y-%m-%d'),
                    'cost_center': invoice_obj.cost_center_id and invoice_obj.cost_center_id.code or '',
                    'suppl_code': partner_code or '',
                    'customer': partner_name or '',
                    'job': invoice_obj.job_id and invoice_obj.job_id.name or '',
                    'lpo': lpo or '',
                    'curr': invoice_obj.currency_id and invoice_obj.currency_id.name or '',
                    'net': invoice_obj.amount_total or "0.00",
                    'balance': (invoice_obj.amount_total * exchange_rate) or "0.00"
                    }
            result.append(vals)
        if sort_based_on == 'seq': 
            result = sorted(result, key=itemgetter('name', 'transaction_type','name'))
        elif sort_based_on == 'date': 
            result = sorted(result, key=itemgetter('date', 'transaction_type','name'))
        elif sort_based_on == 'supplier': 
            result = sorted(result, key=itemgetter('customer', 'transaction_type','name'))
#         result = sorted(result, key=itemgetter("transaction_type", "name"))
        return result
    
jasper_report.report_jasper('report.purchase.inv.summary.jasper', 'purchase.invoice.summary', parser=purchase_inv_summary)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

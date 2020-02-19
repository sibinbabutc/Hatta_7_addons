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


class invoice_uploadation_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(invoice_uploadation_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        vals={}
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        
        date_from = data['form']['from_date']
        from_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
        date_to = data['form']['to_date']
        to_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
        report_heading = "Invoice Uploadation Status Report (%s - %s)"%(from_date,to_date)
        
        if data['form']['report_type'] == 'uploaded':
            report_type = "Uploaded"
        elif data['form']['report_type'] == 'to_upload':
            report_type = "To Upload"
        data['form']['report_type'] = 'pdf'
        vals = {
            'company_name': comp_obj.name or '',
            'company_address': address,
            'company_email': "E-mail :" + comp_obj.email or '',
            'report_heading': report_heading,
            'report_type' : "Report Type: %s"%(report_type),
                }
        return vals
    
    def _get_total_amt_fc(self, cr, uid, invoice_ids, context=None):
        total_amt_fc = 0
        invoice_pool = self.pool.get('account.invoice')
        for invoice in invoice_pool.browse(cr, uid, invoice_ids, context=context):
            if invoice.currency_id.name != 'AED':
                amount_fc = invoice.amount_total or 0.00
            else:
                amount_fc = invoice.amount_total or 0.00
            total_amt_fc+=amount_fc
        return total_amt_fc
    
    def _get_total_amt_aed(self,cr, uid, invoice_ids, currency_id, context=None):
        total_amt_aed = 0
        invoice_pool = self.pool.get('account.invoice')
        for invoice in invoice_pool.browse(cr, uid, invoice_ids, context=context):
            if invoice.currency_id.name != 'AED':
                amount_aed = self.pool.get('res.currency').compute(cr, uid, invoice.currency_id.id,
                                currency_id.id, invoice.amount_total, round=True, currency_rate_type_from=False,
                                currency_rate_type_to=False, context=context)
            else:
                amount_aed = invoice.amount_total or 0.00
            total_amt_aed+=amount_aed
        return total_amt_aed
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        total_amt_fc, total_amt_aed = 0, 0
       
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        invoice_pool = self.pool.get('account.invoice')
       
        if data:
            condition = []
            if data['form']['from_date']:
                condition.append(('date_invoice', '>=', data['form']['from_date']))
            if data['form']['to_date']:
                condition.append(('date_invoice', '<=', data['form']['to_date']))
            if data['form']['customer_id']:
                condition.append(('parent_partner_id.id', '=', data['form']['customer_id'][0]))
                
            if data['form']['report_type']:
                if data['form']['report_type'] == 'uploaded':
                    condition.append(('upload_inv', '=', True))
                    condition.append(('invoice_uploaded', '=', True))
                elif data['form']['report_type'] == 'to_upload':
                    condition.append(('upload_inv', '=', True))
                    condition.append(('invoice_uploaded', '=', False))
                
            condition.append(('type', '=', 'out_invoice'))
            condition.append(('state', 'not in', ['draft', 'cancel']))
            invoice_ids = invoice_pool.search(cr, uid, condition, context=context)
            if invoice_ids:
                for invoice in invoice_pool.browse(cr, uid, invoice_ids, context=context):
                    if invoice.date_invoice:
                        date = datetime.strptime(invoice.date_invoice, "%Y-%m-%d")
                    else:
                        date = ''
                        
                    if invoice.currency_id.name != 'AED':
                        amount_fc = invoice.amount_total or 0.00
                        amount_aed = self.pool.get('res.currency').compute(cr, uid, invoice.currency_id.id,
                            comp_obj.currency_id.id, amount_fc, round=True, currency_rate_type_from=False,
                            currency_rate_type_to=False, context=context)
                    else:
                        amount_fc = invoice.amount_total or 0.00
                        amount_aed = invoice.amount_total or 0.00
                        
                    total_amt_fc = self._get_total_amt_fc(cr, uid, invoice_ids)
                    total_amt_aed = self._get_total_amt_aed(cr, uid, invoice_ids, comp_obj.currency_id)
                    
                    vals = {
                        'customer' : invoice.parent_partner_id and invoice.parent_partner_id.name or '',
                        'customer_id' : invoice.parent_partner_id and invoice.parent_partner_id.id,
                        'invoice_date' : date,
                        'invoice_no' : invoice.internal_number,
                        'job_id' : invoice.job_id and invoice.job_id.name or '',
                        'currency' : invoice.currency_id.name or '',
                        'amount_fc' : amount_fc or "0.00",
                        'amount_aed' : amount_aed or "0.00",
                        'total_amt_fc' : total_amt_fc or "0.00",
                        'total_amt_aed' : total_amt_aed or "0.00"
                            }
                    result.append(vals)
        result = sorted(result, key=operator.itemgetter('customer_id','invoice_date'))
        return result


jasper_report.report_jasper('report.invoice_uploadation_report_jasper', 'invoice.uploadation.wizard', parser=invoice_uploadation_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
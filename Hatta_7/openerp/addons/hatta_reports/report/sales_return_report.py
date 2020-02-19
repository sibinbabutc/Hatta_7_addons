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
import time
from datetime import datetime
from operator import itemgetter

class sales_report_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.clo_month = {}
        super(sales_report_report, self).__init__(cr, uid, ids, data, context)

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
        date_list = []
        if data.get('from_data', False):
            from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
            date_list.append(from_date)
        if data.get('to_date', False):
            to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
            date_list.append(to_date)
        report ='SALES RETURN REPORT'
        if date_list:
            report = report + " (%s)"%(' - '.join(date_list))
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                'report_heading': report
                }
        if data['report_type'] == 'xls':
            vals['IS_IGNORE_PAGINATION'] = True
        return vals
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        invoice_pool = self.pool.get('account.invoice')
        domain = [('state', '!=', 'cancel'), ('type', '=', 'out_refund')]
        if data.get('from_date', False):
            domain.append(('date_invoice', '>=', data['from_date']))
        if data.get('to_date', False):
            domain.append(('date_invoice', '<=', data['to_date']))
        if data.get('partner_id', False):
            domain.append(('partner_id', '=', data['partner_id'][0]))
        invoice_ids = invoice_pool.search(cr, uid, domain, context=context)
        for invoice in invoice_pool.browse(cr, uid, invoice_ids, context=context):
            refund_invoice_id = invoice.refund_invoice_id
            del_no_list = refund_invoice_id and [x.name for x in refund_invoice_id.rel_picking_ids if refund_invoice_id.rel_picking_ids] or []
            vals = {
                    'doc_no': invoice.internal_number,
                    'sr_date': invoice.date_invoice and \
                               datetime.strptime(invoice.date_invoice, "%Y-%m-%d").strftime("%d/%m/%Y") or '',
                    'partner_name': invoice.partner_id.partner_nick_name or invoice.partner_id.name or '',
                    'del_name': ','.join(del_no_list),
                    'sales_inv_no': refund_invoice_id and refund_invoice_id.internal_number,
                    'job_no': refund_invoice_id and refund_invoice_id.job_id and \
                                    refund_invoice_id.job_id.name or '',
                    'value': invoice.amount_total,
                    'curr': invoice.currency_id.name or 'AED',
                    'reason': invoice.name or ''
                    }
            result.append(vals)
        if result:
            result = sorted(result, key=itemgetter('doc_no'))
        return result
    
    
jasper_report.report_jasper('report.sales_return_report_jasper', 'sales.return.report',
                            parser=sales_report_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
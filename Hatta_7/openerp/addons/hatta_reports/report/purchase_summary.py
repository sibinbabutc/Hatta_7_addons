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


class po_summary(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(po_summary, self).__init__(cr, uid, ids, data, context)
        
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
                'report_name': "PURCHASE ORDER SUMMARY REPORT %s"%(report_name_sub)
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        purchase_pool = self.pool.get('purchase.order')
        curr_pool = self.pool.get('res.currency')
        domain = [('state', 'not in', ['draft', 'sent', 'bid'])]
        po_id = data['form']['po_id']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        cost_center_id = data['form']['cost_center_id']
        job_id = data['form']['job_id']
        if po_id:
            po_ids = [po_id[0]]
        else:
            if date_from:
                domain.append(('date_order', '>=', date_from))
            if date_to:
                domain.append(('date_order', '<=', date_to))
            if cost_center_id:
                domain.append(('analytic_account_id', '=', cost_center_id[0]))
            if job_id:
                domain.append(('job_id', '=', job_id[0]))
            po_ids = purchase_pool.search(cr, uid, domain, context=context)
        count = 0
        for po_obj in purchase_pool.browse(cr, uid, po_ids, context=context):
            count += 1
            partner_obj = False
            if po_obj.lead_id:
                partner_obj = po_obj.lead_id.partner_id
            elif po_obj.direct_sale_id:
                partner_obj = po_obj.direct_sale_id.partner_id
            partner_name = partner_obj and partner_obj.partner_nick_name or \
                                partner_obj and partner_obj.name or ''
            exchange_rate = 0.00000
            picking_obj = [x for x in po_obj.picking_ids if x.state != 'cancel']
            if picking_obj:
                exchange_rate = picking_obj[0].invoice_id.exchange_rate or 0.0000
            else:
                purchase_curr = po_obj.currency_id
                comp_curr = po_obj.company_id.currency_id
                if purchase_curr != comp_curr:
                    exchange_rate = curr_pool._get_conversion_rate(cr, uid, purchase_curr,
                                                                   comp_curr,
                                                                   context=context)
                else:
                    exchange_rate = 1.0000
            vals = {
                    'si_no': count,
                    'name': po_obj.name or '',
                    'partner_name': partner_name,
                    'supplier_name': po_obj.partner_id.partner_nick_name or \
                                            po_obj.partner_id.name or '',
                    'date_order': po_obj.date_order and \
                                        datetime.strptime(po_obj.date_order, '%Y-%m-%d'),
                    'job_ac': po_obj.job_id and po_obj.job_id.name or '',
                    'curr': po_obj.currency_id and po_obj.currency_id.name or '',
                    'po_value': (po_obj.amount_total * exchange_rate) or "0.00",
                    'tran_type': po_obj.transaction_type_id and po_obj.transaction_type_id.name or '',
                    'customer_po_no': po_obj.job_id and po_obj.job_id.cust_po_num or ''
                    }
            result.append(vals)
        result = sorted(result, key=itemgetter("tran_type", "name"))
        return result
    
jasper_report.report_jasper('report.po.summary.jasper', 'po.summary', parser=po_summary)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

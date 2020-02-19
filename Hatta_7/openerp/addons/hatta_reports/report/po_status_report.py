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

class po_status_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.clo_month = {}
        data['report_type'] = 'xls'
        super(po_status_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
        to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
        report ='CLIENT PURCHASE ORDER RECEIVED FROM ' + from_date + ' TO ' + to_date
        return {
                'report': report,
                }
    
    def get_po_details(self, cr, uid, ids, sale_obj, context=None):
        supplier_ids = []
        purchase_pool = self.pool.get('purchase.order')
        domain = [('state', 'not in', ['draft', 'sent', 'bid', 'cancel'])]
        if sale_obj.lead_id:
            domain.append(('lead_id', '=', sale_obj.lead_id.id))
        else:
            domain.append(('direct_sale_id', '=', sale_obj.id))
        purchase_ids = purchase_pool.search(cr, uid, domain, context=context)
        po_num_list = []
        supp_list = []
        for po_obj in purchase_pool.browse(cr, uid, purchase_ids, context=context):
            po_num_list.append(po_obj.name)
            supp_name = po_obj.partner_id.partner_nick_name or \
                            po_obj.partner_id.name or ''
            supp_list.append(supp_name)
            supplier_ids.append(po_obj.partner_id.id)
        po_num_list = list(set(po_num_list))
        supp_list = list(set(supp_list))
        return ', '.join(po_num_list), ', '.join(supp_list), list(set(supplier_ids))
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        sale_pool = self.pool.get('sale.order')
        if data:
            condition = []
            if data.get('from_date'):
                condition.append(('date_order', '>=', data.get('from_date')))
            if data.get('to_date'):
                condition.append(('date_order', '<=', data.get('to_date')))
            if data.get('customer_id'):
                condition.append(('partner_id', '=', data.get('customer_id')))
            if data.get('job_id'):
                condition.append(('job_id', '=', data.get('job_id')))
            if data.get('rfq'):
                condition.append(('rfq', '=', data.get('rfq')))
            if data.get('closing_date_from', False):
                condition.append(('closing_date', '>=', data.get('closing_date_from')))
            if data.get('closing_date_to', False):
                condition.append(('closing_date', '<=', data.get('closing_date_to')))
            if data.get('transaction_type_id', False):
                condition.append(('transaction_type_id', '=', data['transaction_type_id']))
            so_record = sale_pool.search(cr, uid, condition, context=context)
            for so in sale_pool.browse(cr, uid, so_record, context=context):
                po_num_list, supp_list, supp_ids = self.get_po_details(cr, uid, ids,
                                                                       so, context=context)
                if data.get('supplier_id', False) and data['supplier_id'] not in supp_ids:
                    continue
                clo_month = 'UNKNOWN'
                if so.closing_date:
                    clo_month = datetime.strptime(so.closing_date, "%Y-%m-%d").strftime("%B")
                    clo_year = datetime.strptime(so.closing_date, "%Y-%m-%d").strftime("%Y")
                    clo_month = "%s - %s"%(clo_month, clo_year)
                if not self.clo_month.get(clo_month, False):
                    self.clo_month[clo_month] = 0
                self.clo_month[clo_month] += 1
                vals = {
                    'po_date': so.date_order and datetime.strptime(so.date_order, "%Y-%m-%d"),
                    'lpo':so.client_order_ref or '-',
                    'customer':so.partner_id.partner_nick_name or so.partner_id.name or '-',
                    'job_id':so.job_id.name or '-',
                    'curr': so.currency_id.name or 'AED',
                    'amt':so.amount_total or "0.00",
                    'rfq':so.rfq or '-',
                    'closing_date':so.closing_date and datetime.strptime(so.closing_date, "%Y-%m-%d"),
                    'status':so.status or '-',
                    'suppliers': supp_list,
                    'clo_list': []
                    }
                result.append(vals)
        result = sorted(result, key=itemgetter('curr', 'job_id'))
        clo_list = []
        for clo in self.clo_month:
            clo_list.append({
                             'month': clo,
                             'value': self.clo_month[clo]
                             })
        if result:
            result[-1]['clo_list'] = clo_list
        return result
    
    
jasper_report.report_jasper('report.purchase_order_status_jasper', 'purchase.order.status', parser=po_status_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
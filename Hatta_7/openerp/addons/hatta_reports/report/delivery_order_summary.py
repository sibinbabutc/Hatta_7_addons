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


class delivery_order_summary(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(delivery_order_summary, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context=None):
        vals={}
        date_list = []
        if data.get('from_data', False):
            from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
            date_list.append(from_date)
        if data.get('to_date', False):
            to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
            date_list.append(to_date)
        report ='DELIVERY NOTE SUMMARY'
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
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        picking_pool = self.pool.get('stock.picking')
        domain = [('state', '=', 'done'),
                  ('type', '=', 'out')]
        
        if data.get('from_date', False):
            domain.append(('date', '>=', data['from_date']))
        if data.get('to_date', False):
            domain.append(('date', '>=', data['to_date']))
        if data.get('partner_id', False):
            domain.append(('partner_id', '=', data['partner_id'][0]))
        sort_based_on = data['sort_based_on']
        picking_ids = picking_pool.search(cr, uid, domain, context=context)
        for picking in picking_pool.browse(cr, uid, picking_ids, context=context):
            partner = picking.real_customer_id or picking.partner_id
            vals = {
                    'doc_no': picking.name,
                    'date': picking.date and \
                                        datetime.strptime(picking.date, '%Y-%m-%d %H:%M:%S') or '',
                    'partner_name': partner.partner_nick_name or partner.name or '',
                    'job_id': picking.job_id and picking.job_id.name or ''
                    }
            result.append(vals)
        if sort_based_on == 'date': 
            result = sorted(result, key=itemgetter('date'))
        elif sort_based_on == 'cust': 
            result = sorted(result, key=itemgetter('partner_name'))
        elif sort_based_on == 'job': 
            result = sorted(result, key=itemgetter('job_id'))
        elif sort_based_on == 'seq': 
            result = sorted(result, key=itemgetter('doc_no'))
        return result
    
jasper_report.report_jasper('report.delivery_order_summary_jasper', 'delivery.order.summary',
                            parser=delivery_order_summary)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

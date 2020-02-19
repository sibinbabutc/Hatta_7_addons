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
from jasper_reports import jasper_report

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator


class consolidated_sale_order_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(consolidated_sale_order_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        return {}
    
    def get_month(self, cr, uid, month, context=None):
        num = 0
        m = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 
              'July': 7,'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
        if month == 'January':
            num = m['January']
        if month == 'February':
            num = m['February']
        if month == 'March':
            num = m['March']
        if month == 'April':
            num = m['April']
        if month == 'May':
            num = m['May']
        if month == 'June':
            num = m['June']
        if month == 'July':
            num = m['July']
        if month == 'August':
            num = m['August']
        if month == 'September':
            num = m['September']
        if month == 'October':
            num = m['October']
        if month == 'November':
            num = m['November']
        if month == 'December':
            num = m['December']
        return num
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        month_dict, num = {}, 0
        total_amt,month,amt= 0,'',0
        
        sale_pool = self.pool.get('sale.order')
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        company = comp_obj.name
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        email = "Email : "+ comp_obj.email
        
        if data:
            from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').strftime("%d/%m/%Y")
            to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').strftime("%d/%m/%Y")
            condition = []
            if data.get('from_date'):
                condition.append(('date_order', '>=', data.get('from_date')))
            if data.get('to_date'):
                condition.append(('date_order', '<=', data.get('to_date')))
            if data.get('customer_id'):
                condition.append(('partner_id.name', '<=', data.get('customer_id')))
            so_record = sale_pool.search(cr, uid, condition, context=context)
            if so_record:
                for so_obj in sale_pool.browse(cr, uid, so_record, context=context):
                    if so_obj.state not in ['cancel']:
                        
                        month_year = datetime.strptime(so_obj.date_order, '%Y-%m-%d').strftime("%B %Y")
                        if month == month_year:
                            amt+=so_obj.amount_total
                            month = month_year
                        else:
                            amt = 0
                            amt+=so_obj.amount_total
                            month = month_year
                            
                        month_dict.update({
                            month : amt
                             })
                        if month_dict[month] == month:
                            month_dict[month] = amt
                        else:
                            month_dict[month] = amt
                        total_amt+=amt
                    
                for key, value in month_dict.iteritems():
                    
                    num = self.get_month(cr, uid, key.split(' ')[0], context=context)
                    
                    vals = {
                            'company' : comp_obj.name,
                            'address' : address,
                            'email' : "Email : "+ comp_obj.email,
                            'report' : "SALE ORDER REPORT (%s - %s)"%(from_date,to_date),
                            'customer' : "Customer Name: %s"%(data.get('customer_id') or ''),
                            'month' : (key).upper(),
                            'amt' : value or "0.00",
                            'total_amt' : total_amt or "0.00",
                            'num' : num or "0",
                                }
                    result.append(vals)
            else:
                vals = {
                    'company' : comp_obj.name,
                    'address' : address,
                    'email' : "Email : "+ comp_obj.email,
                    'report' : "SALE ORDER REPORT (%s - %s)"%(from_date,to_date),
                    'customer' : "Customer Name: %s"%(data.get('customer_id') or ''),
                    'month' : '',
                    'num' : "0",
                        }
                
                result.append(vals)
        result = sorted(result, key=operator.itemgetter('num'))
        return result
    
jasper_report.report_jasper('report.consolidated_sale_order_jasper', 'wizard.consolidated.so', parser=consolidated_sale_order_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
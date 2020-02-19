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

from hatta_crm import JasperDataParser
from jasper_reports import jasper_report

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
import operator

class so_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(so_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        pool= pooler.get_pool(cr.dbname)
        sale_pool = pool.get('sale.order')
        partner_pool = pool.get('res.partner')
        currency_pool = self.pool.get('res.currency')
        for sale_obj in sale_pool.browse(cr, uid, ids, context=context):
            partner_address = partner_pool._display_address(cr, uid, sale_obj.partner_id,
                                                            context=context)
            lines = []
            for line in sale_obj.order_line:
                seq = 0.00
                try:
                    seq = float(line.sequence_no)
                except:
                    seq = 0.00
                vals = {
                        'float_seq': seq,
                        'si_no': line.sequence_no or '',
                        'product_name': line.product_id and line.product_id.name or '',
                        'desc': line.name and line.name.upper() or '',
                        'part_no': line.product_id and line.product_id.part_no or '',
                        'uom': line.product_uom and line.product_uom.name or '',
                        'qty': line.product_uom_qty or "0.00",
                        'amount': line.price_unit or "0.00",
                        'amount_total': line.price_subtotal or "0.00",
                        }
                lines.append(vals)
            if lines:
                lines = sorted(lines, key=operator.itemgetter('float_seq'))
            partner_code = sale_obj.partner_id.partner_code or ''
            amount_word = currency_pool.amount_word(cr, uid, sale_obj.currency_id, sale_obj.amount_total or 0.00,
                                                    context=context)
            data = {
                    'partner_code': sale_obj.partner_id and sale_obj.partner_id.partner_ac_code and \
                                           sale_obj.partner_id.partner_ac_code.upper() or '',
                    'partner_name': sale_obj.partner_id.name.upper() or '',
                    'partner_address': partner_address and partner_address.upper(),
                    'del_date': sale_obj.date_delivery and \
                                    datetime.strptime(sale_obj.date_delivery, '%Y-%m-%d') or '',
                    'name': sale_obj.name,
                    'date_order': sale_obj.date_order and \
                                    datetime.strptime(sale_obj.date_order, '%Y-%m-%d') or '',
                    'user': sale_obj.user_id and sale_obj.user_id.name.upper() or '',
                    'cust_ref': sale_obj.client_order_ref and sale_obj.client_order_ref.upper() or '',
                    'ac_no': sale_obj.job_id and sale_obj.job_id.name + " - " + partner_code or '',
                    'amount_total': sale_obj.amount_total or "0.00",
                    'curr_name': sale_obj.currency_id and sale_obj.currency_id.name or '',
                    'pay_term': sale_obj.payment_term and sale_obj.payment_term.name.upper() or '',
                    'lines': lines,
                    'amount_word': amount_word.upper(),
                    'discount': sale_obj.discount or 0.00
                    }
            result.append(data)
        return result
    
jasper_report.report_jasper('report.sale.order.inherit', 'sale.order', parser=so_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

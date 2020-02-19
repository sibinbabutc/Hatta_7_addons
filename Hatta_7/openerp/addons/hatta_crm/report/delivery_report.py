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


class delivery_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(delivery_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        picking_pool = self.pool.get('stock.picking.out')
        partner_pool = self.pool.get('res.partner')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for picking in picking_pool.browse(cr, uid, ids, context=context):
            partner_obj = picking.partner_id and picking.partner_id.parent_id or picking.partner_id
            partner_address = partner_pool._display_address(cr, uid, partner_obj, context=context)
            picking_data = {
                            'partner_name': partner_obj.name and partner_obj.name.upper(),
                            'partner_address': partner_address and partner_address.upper(),
                            'partner_code': partner_obj.partner_ac_code and partner_obj.partner_ac_code.upper(),
                            'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                            'name': picking.name and picking.name.upper(),
                            'shop': picking.sale_id and picking.sale_id.shop_id and \
                                            picking.sale_id.shop_id.name and 
                                            picking.sale_id.shop_id.name.upper() or 
                                            picking.shop_id and picking.shop_id.name.upper() or '',
                            'user': user_obj.name and user_obj.name.upper(),
                            'lpo': picking.sale_id and picking.sale_id.client_order_ref and \
                                            picking.sale_id.client_order_ref.upper() or \
                                            picking.client_order_ref and picking.client_order_ref.upper() or '',
                            'so_name': picking.sale_id and picking.sale_id.name and \
                                            picking.sale_id.name.upper() or \
                                            picking.origin and picking.origin.upper() or '',
                            'ac_no': picking.sale_id and picking.sale_id.job_id and \
                                            picking.sale_id.job_id.name and \
                                            picking.sale_id.job_id.name.upper() or \
                                            picking.job_id and picking.job_id.name.upper(),
                            'package': picking.package and picking.package.upper(),
                            'del_place': picking.partner_id and picking.partner_id.name.upper() or False,
                            'date': picking.date and datetime.strptime(picking.date, '%Y-%m-%d %H:%M:%S')
                            }
            lines = []
            for line in picking.move_lines:
                seq_no = 0
                try:
                    seq_no = float(line.sequence_no)
                except:
                    seq_no = 0
                line_data = {
                             'seq_no': line.sequence_no or '',
                             'seq_float': seq_no,
                             'product_name': line.product_id.name and line.product_id.name.upper() or '',
                             'name': line.name and line.name.upper() or '',
                             'uom': line.product_uom.name and line.product_uom.name.upper() or '',
                             'qty': line.product_qty or '0.00'
                             }
                lines.append(line_data)
            lines = sorted(lines, key=operator.itemgetter('seq_float'))
            picking_data['lines'] = lines
            result.append(picking_data)
        return result
    
jasper_report.report_jasper('report.delivery_report_jasper', 'stock.picking.out', parser=delivery_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from hatta_rejection_management import JasperDataParser
from collections import defaultdict
from jasper_reports import jasper_report

from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter


class rejection_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(rejection_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        report_heading = 'REJECTION REPORT'
        if data['form']['type'] == 'resupply':
            report_heading = 'REJECTION RE-SUPPLY REPORT'
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                'report_heading': report_heading,
                'run': date_start
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        domain = []
        sl_no, total_dr_qty, total_dn_qty, total_inv_amt = 0, 0.0, 0.0, 0.0
        rejection_line_pool = self.pool.get('rejection.line')
        domain = []
        if data['form']['type'] == 'reject':
            domain.append(('rem_qty_resupply', '>', 0.00))
            domain.append((('rej_id.state', 'not in', ['done', 'cancel'])))
        else:
            domain.append(('rem_qty_resupply', '=', 0.00))
            domain.append(('rej_id.state', 'not in', ['cancel']))
        if data['form'].get('from_date', False):
            domain.append(('rej_id.date', '>=', data['form']['from_date']))
        if data['form'].get('to_date', False):
            domain.append(('rej_id.date', '<=', data['form']['to_date']))
        if data['form'].get('rejection_id', False):
            domain.append(('rej_id.id', '=', data['form']['rejection_id'][0]))
        print domain
        re_suplier_name = ''
        rejection_line_ids = rejection_line_pool.search(cr, uid, domain,
                                                        context=context)
        for rej_line in rejection_line_pool.browse(cr, uid, rejection_line_ids,
                                                   context=context):
            rej = rej_line.rej_id or False
            supplier_list = [x.order_id.partner_id.name for x in rej.purchase_line_ids]
            supplier_list = list(set(supplier_list))
            invoice_amount = 0.00
            unit_price = 0.00
            invoice_name_list = []
            if rej_line.move_id and rej_line.move_id.sale_line_id:
                for invoice_line in rej_line.move_id.sale_line_id.invoice_lines:
                    if invoice_line.invoice_id.state != 'cancel':
                        invoice_amount += invoice_line.price_subtotal or 0.00
                        unit_price = invoice_line.price_unit or 0.00
                        invoice_name_list.append(invoice_line.invoice_id.number)
            new_del_list = [x.picking_id.name for x in rej_line.return_move_ids if x.picking_id.state != 'cancel']
            
            sl_no+=1
            total_dr_qty+= rej_line.qty or 0.0
            total_dn_qty+= rej_line.move_id and rej_line.move_id.product_qty or 0.0
            total_inv_amt+= invoice_amount or 0.0
            cust = rej.sale_id and rej.sale_id.partner_id.partner_nick_name or \
                                            rej.sale_id and rej.sale_id.partner_id.name or \
                                            rej.parent_partner_id and rej.parent_partner_id.partner_nick_name or \
                                            rej.parent_partner_id and rej.parent_partner_id.name or '',
            
            re_suplier_name = ', '.join(supplier_list)
            if cust:
                re_suplier_name += ' [' + str(cust and cust[0] or '') + ']'
            vals = {
                    'sl_no' : sl_no,
                    'dr_number': rej.delivery_return_id and \
                                    rej.delivery_return_id.name or '',
                    'date': rej and rej.date and datetime.strptime(rej.date, '%Y-%m-%d'),
                    'product': rej_line.product_id and rej_line.product_id.name or False,
                    'dr_qty': rej_line.qty or "0.00",
                    'dn_number': rej.picking_id and rej.picking_id.name or '',
                    'cust': rej.sale_id and rej.sale_id.partner_id.partner_nick_name or \
                                            rej.sale_id and rej.sale_id.partner_id.name or \
                                            rej.parent_partner_id and rej.parent_partner_id.partner_nick_name or \
                                            rej.parent_partner_id and rej.parent_partner_id.name or '',
                    'ac_no': rej.job_id and rej.job_id.name or '',
                    'dn_qty': rej_line.move_id and rej_line.move_id.product_qty or "0.00",
                    'supplier_name': ', '.join(supplier_list),
                    'invoice_amount': invoice_amount or "0.00",
                    'return_val': rej_line.qty * unit_price,
                    'remark': rej.note or '',
                    'new_dn_number': ', '.join(new_del_list),
                    'invoice_name': ', '.join(invoice_name_list),
                    'client_order_ref': rej.picking_id.client_order_ref or '',
                    'total_dr_qty' : total_dr_qty or 0.0,
                    'total_dn_qty' : total_dn_qty or 0.0,
                    'total_inv_amt' : total_inv_amt or 0.0,
                    're_suplier_name': re_suplier_name or ''
                    }
            result.append(vals)
        return result
    
jasper_report.report_jasper('report.rejection.report.jasper', 'rejection.report', parser=rejection_report)
jasper_report.report_jasper('report.rejection.redel.report.jasper', 'rejection.report', parser=rejection_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

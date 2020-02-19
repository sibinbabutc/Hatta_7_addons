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


class po_status(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(po_status, self).__init__(cr, uid, ids, data, context)
        
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
                'report_name': "PURCHASE ORDER STATUS REPORT %s"%(report_name_sub)
                }
        return vals
    
    def get_shipping_value(self, cr, uid, pol_obj, context=None):
        res = {
               'grn': 0.00,
               'cancel': 0.00,
               'pending': 0.00
               }
        for stock_move in pol_obj.move_ids:
            if stock_move.picking_id:
                done_moves = 0.00
                if stock_move.state == 'cancel':
                    res['cancel'] += stock_move.product_qty or 0.00
                elif stock_move.state == 'done':
                    res['grn'] += stock_move.product_qty or 0.00
                    done_moves += stock_move.product_qty or 0.00
                else:
                    res['pending'] += stock_move.product_qty or 0.00
        return res
    
    def get_pending_amount(self, cr, uid, pol_obj, context=None):
        amount = 0.00
        paid_amount = 0.00
        for invoice_line in pol_obj.invoice_lines:
            if invoice_line.invoice_id and invoice_line.invoice_id.state == 'paid':
                paid_amount += invoice_line.price_subtotal
        amount = round(pol_obj.price_subtotal,2) - round(paid_amount,2)
        return amount != 0.00 and amount or "0.00"
    
    def get_job_no(self, cr, uid, ids, po_obj, context=None):
        job_id = False
        if po_obj.manual_job_id:
            return po_obj.manual_job_id
        if po_obj.lead_id:
            job_id = po_obj.lead_id and po_obj.lead_id.sale_id and po_obj.lead_id.sale_id.job_id or False
        elif po_obj.direct_sale_id:
            job_id = po_obj.direct_sale_id.job_id and po_obj.direct_sale_id.job_id or False
        return job_id
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        po_pool = self.pool.get('purchase.order')
        po_data = data['form']['po_id']
        supplier_data = data['form']['partner_id']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        sort_supp_wise = data['form']['sort_supp']
        sort_supp_del = data['form']['sort_del_date']
        pending_only = data['form']['pending_only']
        disp_cust_del = data['form']['disp_cust_del_date']
        cost_center_id = data['form']['cost_center_id']
        job_id = data['form']['job_id']
        domain = [('state', 'not in', ['draft', 'cancel', 'sent', 'bid'])]
        if po_data:
            po_ids = [po_data[0]]
        else:
            if supplier_data:
                partner_id = supplier_data[0]
                domain.append(('partner_id', '=', partner_id))
            if date_from:
                domain.append(('date_order', '>=', date_from))
            if date_to:
                domain.append(('date_order', '<=', date_to))
            if cost_center_id:
                domain.append(('analytic_account_id', '=', cost_center_id[0]))
            if job_id:
                domain.append(('job_id', '=', job_id[0]))
            po_ids = po_pool.search(cr, uid, domain, context=context)
        for po_obj in po_pool.browse(cr, uid, po_ids, context=context):
            line_result = []
            job_id = self.get_job_no(cr, uid, ids, po_obj, context=context)
            cust_del_date = po_obj.lead_id and po_obj.lead_id.sale_id and \
                                po_obj.lead_id.sale_id.date_delivery or \
                                po_obj.direct_sale_id and po_obj.direct_sale_id.date_delivery or False
            for line in po_obj.order_line:
                shipping_data = {
                                 'grn': 0.00,
                                 'cancel': 0.00,
                                 'pending': line.product_qty or 0.00
                                 }
                if po_obj.state != 'validated':
                    shipping_data = self.get_shipping_value(cr, uid, line, context=context)
                grn_qty = shipping_data.get('grn', "0.00")
                cancel_qty = shipping_data.get('cancel', "0.00")
                pending_qty = shipping_data.get('pending', "0.00")
                pending_amount = self.get_pending_amount(cr, uid, line, context=context)
                if pending_only and pending_qty <= 0.00:
                    continue
                line_vals = {
                             'product_name': line.product_id and line.product_id.name or '',
                             'uom': line.product_uom and line.product_uom.name or '',
                             'qty': line.product_qty or "0.00",
                             'price_unit': line.price_unit or "0.00",
                             'price_subtotal': line.price_subtotal or "0.00",
                             'grn_qty': grn_qty == 0.00 and "0.00" or grn_qty,
                             'cancel_qty': cancel_qty == 0.00 and "0.00" or cancel_qty,
                             'pending_qty': pending_qty == 0.00 and "0.00" or pending_qty,
                             'pend_amount': (pending_qty * line.price_unit) == 0.00 and "0.00" or \
                                                    pending_qty * line.price_unit
                             }
                line_result.append(line_vals)
            if line_result:
                vals = {
                        'po_id': po_obj.id,
                        'po_number': po_obj.name or '',
                        'partner_name': po_obj.partner_id.partner_ac_code and \
                                            po_obj.partner_id.partner_ac_code + "  " + po_obj.partner_id.name or \
                                            po_obj.partner_id.name,
                        'date': po_obj.date_order and \
                                        datetime.strptime(po_obj.date_order, '%Y-%m-%d'),
                        'job_name': job_id and job_id.name or '',
                        'exp_del_date': po_obj.minimum_planned_date and \
                                            datetime.strptime(po_obj.minimum_planned_date, '%Y-%m-%d'),
                        'cust_del_date': cust_del_date and \
                                            datetime.strptime(cust_del_date, '%Y-%m-%d'),
                        'disp_cust_del': disp_cust_del and "true" or "false",
                        'po_lines': line_result,
                        'supp_sort': sort_supp_wise and "true" or "false",
                        'customer_po_no': po_obj.job_id and po_obj.job_id.cust_po_num or ''
                        }
                result.append(vals)
        if sort_supp_del or sort_supp_wise:
            sort_list = []
            if sort_supp_del and not sort_supp_wise:
                result = sorted(result, key=itemgetter("exp_del_date"))
            elif sort_supp_wise and not sort_supp_del:
                result = sorted(result, key=itemgetter("partner_name"))
            elif sort_supp_wise and sort_supp_del:
                result = sorted(result, key=itemgetter("partner_name", "exp_del_date"))
        return result
    
jasper_report.report_jasper('report.po.status.jasper', 'purchase.analysis.report', parser=po_status)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

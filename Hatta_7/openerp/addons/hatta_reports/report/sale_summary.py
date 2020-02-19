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


class sale_summary(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(sale_summary, self).__init__(cr, uid, ids, data, context)
        data['report_type'] = 'xls'
        
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
        if data['report_type']=='xls':
            vals.update({'IS_IGNORE_PAGINATION':True})
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
                'report_name': "SALES ORDER SUMMARY REPORT %s"%(report_name_sub)
                }
        return vals
    
#     def generate_properties(self, cr, uid, ids, data, context):
#         return {
#             'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
#             'net.sf.jasperreports.export.ignore.page.margins':'true',
#             'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true',
#             'net.sf.jasperreports.export.xls.detect.cell.type': 'true',
#             'net.sf.jasperreports.export.xls.white.page.background': 'true',
#             'net.sf.jasperreports.export.xls.show.gridlines': 'true',
#             }
    
    def get_cost_price(self, cr, uid, line, context=None):
        cost = 0.00
        purchase_pool = self.pool.get('purchase.order')
        line_pool = self.pool.get('purchase.order.line')
        if line.crm_line_id:
            
            cost = line.crm_line_id.selected_pol_id and \
                            line.crm_line_id.selected_pol_id.unit_price_lc * line.product_uom_qty or \
                            line.product_id.standard_price
        elif line.order_id:
            pur_ids = purchase_pool.search(cr, uid, [('direct_sale_id', '=', line.order_id.id)])
            proceed = False
            if pur_ids:
                line_ids = line_pool.search(cr, uid, [('order_id', 'in', pur_ids),
                                                      ('product_id', '=', line.product_id and line.product_id.id or False),
                                                      ('state', 'not in', ['draft', 'sent', 'bid', 'cancel'])])
                if line_ids:
                    proceed = True
                    line_obj = line_pool.browse(cr, uid, line_ids[0], context=context)
                    cost = line_obj.unit_price_lc * line.product_uom_qty
        return cost
    
    def get_del_amount(self, cr, uid, sale_obj, context=None):
        amount = 0.00
        for picking in sale_obj.picking_ids:
            if picking.state == 'done' and not picking.rej_parent_picking_id and \
                            picking.transaction_type_id.refund == False:
                for line in picking.move_lines:
                    if line.sale_line_id:
                        sale_price_unit = self.get_invoice_line_unit_price(cr, uid,
                                                                           line.sale_line_id,
                                                                           context=context)
#                         if line.sale_line_id.product_uom_qty != 0.00:
#                             sale_price_unit = line.sale_line_id.price_subtotal / line.sale_line_id.product_uom_qty
                        val = sale_price_unit * line.product_qty
                        amount += val
        return amount and amount or 0.00
    
    def get_invoice_line_unit_price(self, cr, uid, sale_line, context=None):
        line_invoice_amount = 0.00
        if sale_line:
            found = False
            for invoice_line in sale_line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    line_invoice_amount = invoice_line.price_unit
                    found = True
                    break
            if not found:
                line_invoice_amount = sale_line.price_unit or 0.00
        return line_invoice_amount
    
    def get_inv_amount(self, cr, uid, sale_obj, context=None):
        amount = 0.00
        for invoice in sale_obj.invoice_ids:
            if invoice.state not in ['draft', 'cancel']:
                for line in invoice.invoice_line:
                    amount += line.price_unit * line.quantity
        return amount and amount or 0.00
    
    def get_sale_amount(self, cr, uid, sale_obj, context=None):
        amount = 0.00
        for line in sale_obj.order_line:
            sale_price_unit = self.get_invoice_line_unit_price(cr, uid, line, context=context)
            amount += line.product_uom_qty * sale_price_unit
        return amount
    
    def get_del_cancel(self, cr, uid, sale_obj, context=None):
        amount = 0.00
        for line in sale_obj.order_line:
            sale_price_unit = self.get_invoice_line_unit_price(cr, uid, line, context=context)
            for move_line in line.move_ids:
                if move_line.picking_id and move_line.picking_id.type != 'out':
                    continue
                if move_line.picking_id and move_line.picking_id.state == 'cancel' and \
                        move_line.picking_id.perm_cancel:
                    amount += move_line.product_qty * sale_price_unit
#                 if move_line.picking_id and move_line.picking_id.unposted and \
#                             move_line.picking_id.state == 'cancel':
#                     amount += move_line.product_qty * sale_price_unit
        return amount
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        sale_order_pool = self.pool.get('sale.order')
        sale_line_pool = self.pool.get('sale.order.line')
        sale_id = data['form']['sale_id']
        transaction_type_id = data['form']['transaction_type_id']
        partner_id = data['form']['partner_id']
        product_id = data['form']['product_id']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        user_id = data['form']['user_id']
        filter_on = data['form']['filter_on']
        shop_id = data['form']['shop_id']
        del_but_not_inv = data['form']['del_but_not_inv']
        sale_cancelled = data['form']['sale_cancelled']
        sort_based_on = data['form']['sort_based_on']
        if filter_on == 'posted':
            domain = [('state', 'not in', ['draft'])]
        elif filter_on == 'unposted':
            domain = [('state', '=', 'draft')]
        elif filter_on == 'all':
            domain = []
        if transaction_type_id:
            domain.append(('transaction_type_id', '=', transaction_type_id[0]))
        if partner_id:
            domain.append(('partner_id', '=', partner_id[0]))
        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))
        if user_id:
            domain.append(('user_id', '=', user_id[0]))
        if shop_id:
            domain.append(('shop_id', '=', shop_id[0]))
        if sale_id:
            domain.append(('id', '=', sale_id[0]))
        sale_ids = sale_order_pool.search(cr, uid, domain, context=context)
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        for sale_obj in sale_order_pool.browse(cr, uid, sale_ids, context=context):
            net = self.get_sale_amount(cr, uid, sale_obj, context=context)
            
            cancel = sale_obj.state == 'cancel' and \
                                self.get_sale_amount(cr, uid, sale_obj, context=context) or 0.00
            del_cancel = sale_obj.state != 'cancel' and \
                                self.get_del_cancel(cr, uid, sale_obj, context=context) or 0.00
            cancel += del_cancel
            
            deliv = self.get_del_amount(cr, uid, sale_obj)
            
            inv = self.get_inv_amount(cr, uid, sale_obj)
            
            #KEPT FOR FUTURE USE IN CASE HATTA CHANGE THEIR MIND AGAIN :)
            
#             net = self.pool.get('res.currency').compute(cr, uid, sale_obj.currency_id.id,
#                                 user_obj.company_id.currency_id.id,
#                                 self.get_sale_amount(cr, uid, sale_obj, context=context),
#                                 round=True, currency_rate_type_from=False, currency_rate_type_to=False,
#                                 context=context)
#             
#             cancel = self.pool.get('res.currency').compute(cr, uid, sale_obj.currency_id.id,
#                                 user_obj.company_id.currency_id.id, 
#                                 sale_obj.state == 'cancel' and \
#                                     self.get_sale_amount(cr, uid, sale_obj, context=context),
#                                 round=True, currency_rate_type_from=False, currency_rate_type_to=False,
#                                 context=context)
#             
#             deliv = self.pool.get('res.currency').compute(cr, uid, sale_obj.currency_id.id,
#                                 user_obj.company_id.currency_id.id, self.get_del_amount(cr, uid, sale_obj),
#                                 round=True, currency_rate_type_from=False, currency_rate_type_to=False,
#                                 context=context)
#             
#             inv = self.pool.get('res.currency').compute(cr, uid, sale_obj.currency_id.id,
#                                 user_obj.company_id.currency_id.id, self.get_inv_amount(cr, uid, sale_obj),
#                                 round=True, currency_rate_type_from=False, currency_rate_type_to=False,
#                                 context=context)
            if del_but_not_inv and deliv <= inv:
                continue
            if sale_cancelled and cancel == 0.00:
                continue
            vals = {
                    'transaction_type': sale_obj.transaction_type_id and \
                                                sale_obj.transaction_type_id.name or '',
                    'shop': sale_obj.shop_id and sale_obj.shop_id.name.upper() or '',
                    'sale_no': sale_obj.name or '',
                    'date': sale_obj.date_order and \
                                    datetime.strptime(sale_obj.date_order, '%Y-%m-%d'),
                    'cc': sale_obj.cost_center_id and sale_obj.cost_center_id.id or False,
                    'partner': sale_obj.partner_id and sale_obj.partner_id.name or '',
                    'user': sale_obj.user_id.name or '',
                    'lpo': sale_obj.client_order_ref or '',
                    'job': sale_obj.job_id and sale_obj.job_id.name or '',
                    
                    'net': net,
                    'cancel': cancel or "0.00",
                    'del': deliv or "0.00",
                    'inv': inv or "0.00",
                    'curr': sale_obj.currency_id.name or ''
                    }
            result.append(vals)
            
        if sort_based_on == 'date':
            result = sorted(result, key=itemgetter('cc', 'curr', 'date'))
        elif sort_based_on == 'seq':
            result = sorted(result, key=itemgetter('cc', 'curr', 'sale_no'))
        elif sort_based_on == 'cust':
            result = sorted(result, key=itemgetter('cc', 'curr', 'partner'))
        return result

jasper_report.report_jasper('report.sale.summary.jasper', 'sale.summary', parser=sale_summary)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

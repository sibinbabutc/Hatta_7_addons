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


class cost_sheet_analysis(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        self.sale_purchases_map = {}
        self.purchase_ratio = {}
        self.purchase_amount = {}
        self.purchase_exchange_rate = {}
        super(cost_sheet_analysis, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_from = data['form'].get('from_date', False)
        date_to = data['form'].get('to_date', False)
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
                'report_name': "Cost Analysis %s"%(report_name_sub)
                }
        return vals
    
    def get_purchase_amount(self, cr, uid, po_obj, comp_curr_obj, context=None):
        currency_pool = self.pool.get('res.currency')
        po_curr_id = po_obj.currency_id.id
        if po_curr_id == comp_curr_obj.id:
            self.purchase_exchange_rate[po_obj.id] = 1.0000
            return po_obj.amount_total
        else:
            inv_found = False
            for invoice in po_obj.invoice_ids:
                if invoice.state not in ['draft', 'cancel']:
                    inv_found = True
                    exchange_rate = invoice.exchange_rate or 1.0000
            if not inv_found:
                exchange_rate = currency_pool.compute(cr, uid, po_curr_id, comp_curr_obj.id,
                                                      1.000)
                self.purchase_exchange_rate[po_obj.id] = exchange_rate or 1.0000
            return po_obj.amount_total * exchange_rate
    
    def get_sale_purchases(self, cr, uid, sale_ids, context=None):
        sale_pool = self.pool.get('sale.order')
        purchase_pool = self.pool.get('purchase.order')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for sale_obj in sale_pool.browse(cr, uid, sale_ids, context=context):
            if sale_obj.lead_id:
                purchase_ids = purchase_pool.search(cr, uid, [('lead_id', '=', sale_obj.lead_id.id),
                                                              ('state', 'not in', ['draft', 'sent', 'bid', 'cancel'])],
                                                    context=context)
                self.sale_purchases_map[sale_obj.id] = purchase_ids
            else:
                purchase_ids = purchase_pool.search(cr, uid, [('direct_sale_id', '=', sale_obj.id),
                                                              ('state', '!=', 'cancel')],
                                                    context=context)
                self.sale_purchases_map[sale_obj.id] = purchase_ids
            sale_total_purchase = 0.00
            for purchase in purchase_pool.browse(cr, uid, purchase_ids, context=context):
                purchase_amount = self.get_purchase_amount(cr, uid, purchase,
                                                          user_obj.company_id.currency_id,
                                                          context=context)
                self.purchase_amount[purchase.id] = purchase_amount
                sale_total_purchase += purchase_amount
            for purchase in purchase_pool.browse(cr, uid, purchase_ids, context=context):
                purchase_amount = self.purchase_amount[purchase.id]
                if purchase_amount != 0.00:
                    purchase_ratio = float(float(purchase_amount) / float(sale_total_purchase))
                else:
                    purchase_ratio = 1.000
                self.purchase_ratio[purchase.id] = purchase_ratio
        return True
    
    def get_sale_invoice_details(self, cr, uid, sale_obj, product_ids, context=None):
        invoice_line_pool = self.pool.get('account.invoice.line')
        invoice_name_list = []
        invoice_ids = []
        for invoice in sale_obj.invoice_ids:
            invoice_ids.append(invoice.id)
        invoice_line_ids = invoice_line_pool.search(cr, uid, [('product_id', 'in', product_ids),
                                                              ('invoice_id', 'in', invoice_ids)],
                                                    context=context)
        invoice_amount = 0.00
        for invoice_line in invoice_line_pool.browse(cr, uid, invoice_line_ids, context=context):
            invoice_amount += invoice_line.price_subtotal or 0.00
            invoice_name_list.append(invoice_line.invoice_id.number or '')
        print invoice_name_list
        print invoice_amount
        return ", ".join(list(set(invoice_name_list))), invoice_amount
    
    def get_other_costs(self, cr, uid, data, job_id, context=None):
        account_move_line_pool = self.pool.get('account.move.line')
        duty_account_id = date.get('duty_account_id', False)[0]
        bank_int_account_id = date.get('bank_int_account_id', False)[0]
        insu_account_id = date.get('insu_account_id', False)[0]
        tel_account_id = date.get('tel_account_id', False)[0]
        freight_account_id = date.get('freight_account_id', False)[0]
        
        return True
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        sale_pool = self.pool.get('sale.order')
        purchase_pool = self.pool.get('purchase.order')
        print data,"--------->DATA\n\n"
        sale_domain = [('state', '!=', 'cancel')]
        if data['form'].get('from_date', False):
            sale_domain.append(('date_order', '=', data['form']['from_date']))
        if data['form'].get('to_date', False):
            sale_domain.append(('date_order', '=', data['form']['to_date']))
        if data['form'].get('job_id', False):
            sale_domain.append(('job_id', '=', data['form']['job_id'][0]))
        if data['form'].get('partner_id', False):
            sale_domain.append(('partner_id', '=', data['form']['partner_id'][0]))
        if data['form'].get('transaction_type_id', False):
            sale_domain.append(('transaction_type_id', '=', data['form']['transaction_type_id'][0]))
        sale_ids = sale_pool.search(cr, uid, sale_domain, context=context)
        self.get_sale_purchases(cr, uid, sale_ids, context=context)
#         result = sorted(result, key=itemgetter("transaction_type", "name"))
        for sale_obj in sale_pool.browse(cr, uid, sale_ids, context=context):
            purchase_ids = self.sale_purchases_map[sale_obj.id]
            other_cost = {}
            if sale_obj.job_id:
                other_cost = self.get_other_costs(cr, uid, data, sale_obj.job_id, context=context)
            for purchase in purchase_pool.browse(cr, uid, purchase_ids, context=context):
                purchase_product_ids = [x.product_id.id for x in purchase.order_line if x.product_id]
                sale_invoice_numbers, sale_invoice_amt = self.get_sale_invoice_details(cr, uid, sale_obj,
                                                                                       purchase_product_ids,
                                                                                       context=context)
                print sale_invoice_numbers
                print sale_invoice_amt,"----------->Sales Invoice Amount"
                vals = {
                        'sale_invoice_number': sale_invoice_numbers,
                        'job_no': sale_obj.job_id and sale_obj.job_id.name or '',
                        'sale_amount': sale_invoice_amt or "0.00",
                        'sale_no': sale_obj.name or '',
                        'mat_cost': self.purchase_amount[purchase.id] or "0.00"
                        }
        return result
    
jasper_report.report_jasper('report.cost.sheet.analysis.jasper', 'cost.sheet.analysis',
                            parser=cost_sheet_analysis)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class supplier_invoice_details_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(supplier_invoice_details_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        return {}
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
           'net.sf.jasperreports.export.xls.detect.cell.type' : 'true'
            }
    
    def get_from_country(self, cr, uid, po_obj, context=None):
        country = ''
        if po_obj.supplier_country_id:
            for i in po_obj.supplier_country_id:
                country = country + ' ' + i.name
            return country
        else:
            return country
        
    def get_cargo_comp(self, cr, uid, cargo_id, context=None):
        cargo, policy_no, max_value, turn_over = '', '', '', ''
        cargo_comp = self.pool.get('cargo.company').browse(cr, uid, cargo_id, context=context)
        res = {
               'cargo' : cargo_comp.cargo_company,
               'policy_no' : cargo_comp.policy_no,
               'max_value' : str("{:0,.2f}".format(cargo_comp.max_value) or "0.00"),
               'turn_over' : str("{:0,.2f}".format(cargo_comp.turn_over) or "0.00"),
               }
        return res
        
    def get_order_no(self, cr, uid, po_obj, context=None):
        order_no = ''
        if po_obj.invoice_ids:
            for i in po_obj.invoice_ids:
                order_no = i.supplier_invoice_number
            return order_no
        else:
            return order_no
         
    def get_curr(self, cr, uid, po_obj, context=None):
        curr = ''
        if po_obj.invoice_ids:
            for i in po_obj.invoice_ids:
                curr = i.currency_id.name
            return curr
        else:
            return curr
         
    def get_inv_total(self, cr, uid, po_obj, context=None):
        inv_total = ''
        if po_obj.invoice_ids:
            for i in po_obj.invoice_ids:
                inv_total = str(i.amount_total)
            return inv_total
        else:
            return inv_total
    
#     def get_invoice_details(self, cr, uid, ids, quotation, purchase_id, context=None):
#         result = []
#         picking_pool = self.pool.get('stock.picking')
#         print quotation.id
#         print purchase_id
#         picking_ids = picking_pool.search(cr, uid, [('shipping_ids', 'in', [quotation.id]),
#                                                     ('purchase_id', '!=', purchase_id),
#                                                     ('type', '=', 'in'),
#                                                     ('state', '=', 'done')],
#                                           context=context)
#         for picking in picking_pool.browse(cr, uid, picking_ids, context=context):
#             picking_invoice = picking.invoice_id or False
#             if picking_invoice and not picking.purchase_id.collected_by_hatta and not picking.purchase_id.delivered_by_supplier:
#                 supplier_country_list = [x.name for x in picking.purchase_id.supplier_country_id and \
#                                                     picking.purchase_id.supplier_country_id or '']
#                 vals = {
#                         'picking_id': picking.id,
#                         'purchase_id': picking.purchase_id or False,
#                         'coutry_id': ', '.join(supplier_country_list),
#                         'supp_invoice_no': picking_invoice.supplier_invoice_number or '',
#                         'curr': picking_invoice.currency_id.name or '',
#                         'invoice_amount': picking_invoice.amount_total or "0.00"
#                         }
#                 result.append(vals)
#         return result
    
    def get_shipping_details(self, cr, uid, ids, picking_obj, context=None):
        lines = {}
        if not picking_obj.purchase_id.collected_by_hatta and \
                    not picking_obj.purchase_id.delivered_by_supplier:
            shipping_lines = picking_obj.shipping_ids or \
                                picking_obj.purchase_id.shipping_ids or []
            for shipping in shipping_lines:
                if shipping.state == 'selected':
                    return {
                            'vessel_name': shipping.carrier_id.name,
                            'awb': shipping.awb
                            }
        if picking_obj.purchase_id.collected_by_hatta:
            return {
                    'vessel_name': "COLLECTED BY HATTA",
                    'awb': ' - '
                    }
        if picking_obj.purchase_id.delivered_by_supplier:
            return {
                    'vessel_name': "DELIVERED BY SUPPLIER",
                    'awb': ' - '
                    }
        return lines
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        picking_pool = self.pool.get('stock.picking')
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = user_obj.company_id.name
        comp_curr = user_obj.company_id.currency_id.name
        
        shipping_pool = self.pool.get('shipping.quotation')
        if data:
            condition = []
            if data.get('from_date'):
                condition.append(('awb_date', '>=', data.get('from_date')))
            if data.get('to_date'):
                condition.append(('awb_date', '<=', data.get('to_date')))
#             done_purchase_ids = []
#             done_incoming_ids = []
            shipping = shipping_pool.search(cr, uid, condition, context=context)
            sl_no = 0
            res = self.get_cargo_comp(cr, uid, data['cargo_company_id'], context=context)
            month = datetime.strptime(data['from_date'], '%Y-%m-%d').strftime("%B %Y")
#             for quotation in shipping_pool.browse(cr, uid, shipping, context=context):
#                 quotation_purchase = quotation.purchase_id or False
#                 invoice_details = self.get_invoice_details(cr, uid, ids, quotation,
#                                                            quotation_purchase.id, context=context)
#                 for invoice in invoice_details:
#                     purchase_obj = invoice['purchase_id']
#                     picking_id = invoice['picking_id']
#                     done_purchase_ids.append(purchase_obj.id)
#                     done_incoming_ids.append(picking_id)
#                     vals = {
#                             'company' : "M/s %s"%(company),
#                             'cargo' : "%s - POLICY NO. %s"%(res['cargo'].upper(),res['policy_no']),
#                             'month' : "MARINE DECLARATIONS FOR THE MONTH OF %s"%(month.upper()),
#                             'value_annual' : "(Maximum value any one shipment is %s %s/-) (Estimated Annual Turnover - %s %s/-)" %(comp_curr,res['max_value'],comp_curr,res['turn_over']),
#                             'date' : quotation.awb_date and datetime.strptime(quotation.awb_date, "%Y-%m-%d"),
#                             'order_no' : invoice['supp_invoice_no'],
#                             'bank_lc_no' : '-',
#                             'bill_no' : quotation.awb,
#                             'product' : purchase_obj and purchase_obj.product_id.name or '',
#                             'method' : purchase_obj and purchase_obj.shipment_method_id and \
#                                                 purchase_obj.shipment_method_id.name or '',
#                             'vessel_name' : quotation.carrier_id.name,
#                             'voyage_from' : invoice['coutry_id'],
#                             'voyage_auh' : "AUH",
#                             'curr' : invoice['curr'],
#                             'invoice_value' : invoice['invoice_amount'] or "0.00",
#                             'delivery_term' : purchase_obj and purchase_obj.incoterm_id and \
#                                                     purchase_obj.incoterm_id.name or '',
#                             'exchange_rate' : '-',
#                             'sum_insured' : '-',
#                             'supplier' : purchase_obj and purchase_obj.partner_id and \
#                                                 purchase_obj.partner_id.name or '',
#                             'po_acc_no' : purchase_obj and purchase_obj.job_id.name or '',
#                             }
#                     result.append(vals)
#                 if quotation_purchase.id not in done_purchase_ids:
#                     done_purchase_ids.append(quotation_purchase.id)
#                     country = self.get_from_country(cr, uid, quotation.purchase_id, context=context)
#                     for picking in quotation_purchase.picking_ids:
#                         picking_invoice = picking.invoice_id or False
#                         if picking.id not in done_incoming_ids:
#                             direct_del = quotation_purchase.collected_by_hatta or quotation_purchase.delivered_by_supplier or False
#                             vessel_name = quotation.carrier_id.name
#                             if quotation_purchase.collected_by_hatta:
#                                 vessel_name = 'COLLECTED BY HATTA'
#                             if quotation_purchase.delivered_by_supplier:
#                                 vessel_name = 'DELIVERED BY SUPPLIER'
#                             done_incoming_ids.append(picking.id)
#                             vals = {
#                                     'company' : "M/s %s"%(company),
#                                     'cargo' : "%s - POLICY NO. %s"%(res['cargo'].upper(),res['policy_no']),
#                                     'month' : "MARINE DECLARATIONS FOR THE MONTH OF %s"%(month.upper()),
#                                     'value_annual' : "(Maximum value any one shipment is %s %s/-) (Estimated Annual Turnover - %s %s/-)" %(comp_curr,res['max_value'],comp_curr,res['turn_over']),
#                                     'date' : direct_del and quotation.awb_date and datetime.strptime(quotation.awb_date, "%Y-%m-%d") or \
#                                                     picking_invoice.date_invoice and datetime.strptime(picking_invoice.date_invoice, "%Y-%m-%d"),
#                                     'order_no' : picking_invoice.supplier_invoice_number or '',
#                                     'bank_lc_no' : '-',
#                                     'bill_no' : direct_del and "-" or quotation.awb,
#                                     'product' : quotation.purchase_id and quotation.purchase_id.product_id.name or '',
#                                     'method' : quotation.purchase_id and quotation.purchase_id.shipment_method_id and quotation.purchase_id.shipment_method_id.name or '',
#                                     'vessel_name' : vessel_name,
#                                     'voyage_from' : country,
#                                     'voyage_auh' : "AUH",
#                                     'curr' : picking_invoice.currency_id.name or '',
#                                     'invoice_value' : picking_invoice.amount_total or "0.00",
#                                     'delivery_term' : quotation.purchase_id and quotation.purchase_id.incoterm_id and quotation.purchase_id.incoterm_id.name or '',
#                                     'exchange_rate' : '-',
#                                     'sum_insured' : '-',
#                                     'supplier' : quotation.purchase_id and quotation.purchase_id.partner_id and quotation.purchase_id.partner_id.name or '',
#                                     'po_acc_no' : quotation.purchase_id and quotation.purchase_id.job_id.name or '',
#                                     }
#                             result.append(vals)
            picking_ids = picking_pool.search(cr, uid, [('invoice_date', '>=', data.get('from_date')),
                                                        ('invoice_date', '<=', data.get('to_date')),
                                                        ('state', '=', 'done'),
                                                        ('type', '=', 'in'),
                                                        ('invoice_id', '!=', False)])
            for picking in picking_pool.browse(cr, uid, picking_ids, context=context):
                picking_invoice = picking.invoice_id or False
                country = self.get_from_country(cr, uid, picking.purchase_id, context=context)
                shipping_line = self.get_shipping_details(cr, uid, ids, picking, context=context)
                vessel_name = shipping_line.get('vessel_name', '-')
                awb_no = shipping_line.get('awb', '-')
                vals = {
                        'company' : "M/s %s"%(company),
                        'cargo' : "%s - POLICY NO. %s"%(res['cargo'].upper(),res['policy_no']),
                        'month' : "MARINE DECLARATIONS FOR THE MONTH OF %s"%(month.upper()),
                        'value_annual' : "(Maximum value any one shipment is %s %s/-) (Estimated Annual Turnover - %s %s/-)" %(comp_curr,res['max_value'],comp_curr,res['turn_over']),
                        'date' : picking_invoice and \
                                        datetime.strptime(picking_invoice.date_invoice, "%Y-%m-%d"),
                        'order_no' : picking_invoice and picking_invoice.supplier_invoice_number or '',
                        'bank_lc_no' : '- ',
                        'bill_no' : awb_no,
                        'product' : picking.purchase_id and picking.purchase_id.product_id.name or '',
                        'method' : picking.purchase_id and picking.purchase_id.shipment_method_id and picking.purchase_id.shipment_method_id.name or '',
                        'vessel_name' : vessel_name,
                        'voyage_from' : country,
                        'voyage_auh' : "AUH",
                        'curr' : picking_invoice and picking_invoice.currency_id.name or '',
                        'invoice_value' : picking_invoice and picking_invoice.amount_total or "0.00",
                        'delivery_term' : picking.purchase_id and picking.purchase_id.incoterm_id and picking.purchase_id.incoterm_id.name or '',
                        'exchange_rate' : '-',
                        'sum_insured' : '-',
                        'supplier' : picking.purchase_id and picking.purchase_id.partner_id and picking.purchase_id.partner_id.name or '',
                        'po_acc_no' : picking.purchase_id and picking.purchase_id.job_id.name or '',
                        }
                result.append(vals)
            result = sorted(result, key=operator.itemgetter('date'))
            return result

jasper_report.report_jasper('report.supplier_invoice_details_jasper', 'wizard.supplier.invoice', parser=supplier_invoice_details_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator

class payment_details_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        data['report_type'] = 'xls'
        super(payment_details_report, self).__init__(cr, uid, ids, data, context)
                        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context=None):
        
        return {}
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result= []
        inv_no = ' '
        sl_no = 0
        carrier_freight_total, cost_freight_total = 0.0, 0.0
        quote_total, cost_total = 0.0, 0.0
        extra_cost, net_extra_cost = 0.0, 0.0
        
        invoice_pool = self.pool.get('shipping.invoice')
        quotation_pool = self.pool.get('shipping.quotation')
        payment_pool = self.pool.get('account.move')
        
        inv_ids = invoice_pool.browse(cr, uid, ids, context=context)
        for inv in inv_ids:
            for quota in inv.quotation_ids:
                quota_invoice_number = quota.invoice_number or ''
                inv_no=inv_no + " " + quota_invoice_number
                date = datetime.strptime(inv.date, '%Y-%m-%d').strftime("%B %Y")
                report = (inv.carrier_id.name).upper() + " INVOICE %s"%(inv_no) + " - " + date.upper() + " - PAYMENT DETAILS [A/C# %s"%(inv.acc_no)+ "]"
                quote_total+= quota.carrier_freight or 0.0
                carrier_freight_total+= quota.carrier_freight
                cost_freight_total += quota.costsheet_freight_charge
#                 cost_total = quota.costsheet_freight_charge + quota.costsheet_duty or 0.0
                extra_cost = quota.costsheet_freight_charge - quota.invoice_freight or 0.0
                net_extra_cost += extra_cost
                sl_no+=1
                vals = {
                    'sl_no' : sl_no,
                    'report': report,
                    'carrier' : inv.carrier_id.name,
                    'acc_no' : inv.acc_no,
                    'total' : inv.total or "0.00",
                    'rounding' : inv.rounding_off or "0.00",
                    'total_amt' : (quote_total - inv.rounding_off) or "0.00",
                    'notes'  : inv.notes and "NOTES: %s"%(inv.notes),
                    'awb' : quota.awb and (quota.awb).upper() or '',
                    'awb_date' : quota.awb_date and datetime.strptime(quota.awb_date, '%Y-%m-%d'),
                    'inv_no' : quota.invoice_number,
                    'suppiler' : quota.purchase_id and (quota.purchase_id.partner_id.name).upper(),
                    'po_acc_no' : quota.purchase_id and quota.purchase_id.job_id.name or ' ',
                    'dimension' : quota.purchase_id and quota.purchase_id.dimension,
                    'quote_text' : "Actual %s"%(inv.carrier_id.name) + " Quote",
                    'quote_freight' : quota.carrier_freight or "0.00",
                    'quote_total' : quote_total or "0.00",  
                    'carrier_charges' : "%s Charges"%(inv.carrier_id.name),
                    'carrier_freight' : quota.invoice_freight or "0.00",
                    'carrier_freight_total' : carrier_freight_total or "0.00",
                    'cost_freight' : quota.costsheet_freight_charge or "0.00",
                    'cost_freight_total' : cost_freight_total or "0.00",
                    'extra_cost' : extra_cost or "0.00",
                    'net_extra_cost' : net_extra_cost or "0.00",
                    'po_code' : inv.purchase_others and inv.purchase_others.journal_id.code,
                    'po_name' : inv.purchase_others and inv.purchase_others.name,
                    'sub_report' : []
                            }
                
                for payment in inv.payments_ids:
                    pay_vals = {
                        'cheque_no' : payment.cheque_no and "CH: %s"%(payment.cheque_no),
                        'cheque_date' : payment.cheque_date and "DT: %s"%(datetime.strptime(payment.cheque_date, '%Y-%m-%d').strftime("%d.%m.%Y")),
                        'bank_details' : payment.bank_details,
                        'pay_code' : payment.journal_id.code,
                        'pay_name' : payment.name
                                 }
                    vals['sub_report'].append(pay_vals)
                result.append(vals)
        return result

    
jasper_report.report_jasper('report.payment_details_jasper', 'shipping.invoice', parser=payment_details_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
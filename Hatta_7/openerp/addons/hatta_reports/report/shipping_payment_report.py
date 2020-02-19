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


class shipping_payment_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(shipping_payment_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        return {}
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
           'net.sf.jasperreports.export.xls.detect.cell.type' : 'true'
            }

    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        sl_no, notes = 0, ''
        total_inv, total_quote, total_cost = 0.0, 0.0, 0.0
        invoice_pool = self.pool.get('shipping.invoice')
        if data:
            condition = []
            if data.get('from_date'):
                condition.append(('date', '>=', data.get('from_date')))
            if data.get('to_date'):
                condition.append(('date', '<=', data.get('to_date')))
            if data.get('carrier_id'):
                condition.append(('carrier_id', '=', data.get('carrier_id')))
            invoice = invoice_pool.search(cr, uid, condition, context=context)
            for inv in invoice_pool.browse(cr, uid, invoice, context=context):
                inv_notes = inv.notes or ' '
                notes = notes + inv_notes + "\n"
                for quotation in inv.quotation_ids:
                    sl_no+=1
                    date = datetime.strptime(inv.date, '%Y-%m-%d').strftime("%B %Y")
                    report = (data.get('carrier_id')).upper() + " INVOICE - " + date.upper() + " - PAYMENT DETAILS [A/C# %s"%(inv.acc_no)+ "]"
                    
                    total_inv+= quotation.invoice_freight or 0.0
                    total_quote+= quotation.carrier_freight or 0.0
                    total_cost+= quotation.costsheet_freight_charge or 0.0
                    extra_cost = quotation.costsheet_freight_charge - quotation.invoice_freight
                    vals = {
                        'sl_no' : sl_no,
                        'report' : report,
                        'awb_date' : quotation.awb_date and datetime.strptime(quotation.awb_date, "%Y-%m-%d"),
                        'awb' : quotation.awb and (quotation.awb).upper() or '',
                        'inv_no' : quotation.invoice_number,
                        'suppiler' : quotation.purchase_id and (quotation.purchase_id.partner_id.name).upper(),
                        'po_acc_no' : quotation.purchase_id and quotation.purchase_id.job_id.name,
                        'weight' : quotation.purchase_id and quotation.purchase_id.weight,
                        'dimension' : quotation.purchase_id and quotation.purchase_id.dimension,
                        'inv_text' : "AS PER %s"%((data.get('carrier_id')).upper()) + " INVOICE",
                        'inv_freight' : quotation.invoice_freight or "0.00",
                        'total_inv' : total_inv or "0.00",
                        'quote_text' : "AS PER %s"%((data.get('carrier_id')).upper()) + " QUOTE",
                        'quote_freight' : quotation.carrier_freight or "0.00",
                        'total_quote' : format(total_quote, '.2f') or "0.00",
                        'cost_freight' : quotation.costsheet_freight_charge or "0.00",
                        'total_cost' : total_cost or "0.00",
                        'extra_cost' : extra_cost or "0.00",
                        'rounding_off' : inv.rounding_off or "0.00",
                        'total_amt' : (total_inv - inv.rounding_off) or "0.00",
                        'remarks' : quotation.remarks,
                        'courier_company' : (data.get('carrier_id')),
                        'notes' : "NOTE: %s"%(notes)
                            }
                    result.append(vals)
            return result


jasper_report.report_jasper('report.shipping_payment_details_jasper', 'wizard.shipping.payment.details', parser=shipping_payment_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
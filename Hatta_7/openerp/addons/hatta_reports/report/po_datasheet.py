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


class po_datasheet(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(po_datasheet, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        return vals
    
    def get_total_po(self, cr, uid, po_obj, context=None):
        po_pool = self.pool.get('purchase.order')
        lead_id = po_obj.lead_id and po_obj.lead_id.id or False
        if lead_id:
            po_ids = po_pool.search(cr, uid, [('lead_id', '=', lead_id),
                                              ('state', 'not in', ['draft', 'bid', 'cancel', 'sent'])])
            return po_ids and len(po_ids) or 1
        elif po_obj.direct_sale_id:
            po_ids = po_pool.search(cr, uid, [('direct_sale_id', '=', po_obj.direct_sale_id.id),
                                              ('state', 'not in', ['draft', 'bid', 'cancel', 'sent'])],
                                    context=context)
            return po_ids and len(po_ids) or 1
        else:
            return 1
    
    def check_cert_req(self, cr, uid, ids, po_obj, context=None):
        for line in po_obj.order_line:
            if line.certificate_ids:
                return True
        return False
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        purchase_pool = self.pool.get('purchase.order')
        for purchase_obj in purchase_pool.browse(cr, uid, ids, context=context):
            line_order = self.get_total_po(cr, uid, purchase_obj, context=context)
            po_sale = purchase_obj.lead_id and purchase_obj.lead_id.sale_id or \
                        purchase_obj.direct_sale_id or False
            sale_del_date = po_sale and po_sale.date_delivery or ''
            cust_name = po_sale and po_sale.partner_id.name or ''
            cert_req = self.check_cert_req(cr, uid, ids, purchase_obj, context=context)
            partner_code = po_sale and po_sale.partner_id.partner_code or ''
            vals = {
                    'po_id': purchase_obj.id,
                    'job': purchase_obj.job_id and purchase_obj.job_id.name + " - " + partner_code or False,
                    'line_order': str(purchase_obj.line_of_order) + " / " + str(line_order),
                    'item_no': purchase_obj.item or '',
                    'date': datetime.now(),
                    'supp_name': purchase_obj.partner_id and purchase_obj.partner_id.name or '',
                    'mrp_name': ','.join([x.name for x in purchase_obj.manufacturer]),
                    'po_name': purchase_obj.name or '',
                    'order_date': purchase_obj.date_order and \
                                        datetime.strptime(purchase_obj.date_order, '%Y-%m-%d') or '',
                    'supp_del_date': purchase_obj.minimum_planned_date and \
                                        datetime.strptime(purchase_obj.minimum_planned_date, '%Y-%m-%d') or '',
                    'sale_del_date': sale_del_date and \
                                            datetime.strptime(sale_del_date, '%Y-%m-%d') or '',
                    'cust_name': cust_name,
                    'rfq_no': purchase_obj.lead_id and purchase_obj.lead_id.customer_rfq or '',
                    'client_po_no': po_sale and po_sale.client_order_ref or '',
                    'order_receiv':po_sale and  po_sale.date_order and \
                                        datetime.strptime(po_sale.date_order, '%Y-%m-%d') or '',
                    'cust_del_date': po_sale and po_sale.date_delivery and \
                                        datetime.strptime(po_sale.date_delivery, '%Y-%m-%d') or '',
                    'currency_name': purchase_obj.currency_id.name or '',
                    'total_cost': purchase_obj.amount_total or "0.00",
                    'pay_term': purchase_obj.payment_term_id and purchase_obj.payment_term_id.name or '',
                    'duty_expt': purchase_obj.duty_required,
                    'cour_detail': purchase_obj.shipment_method_id and \
                                        purchase_obj.shipment_method_id.name or '',
                    'incoterm': purchase_obj.incoterm_id and purchase_obj.incoterm_id.name or '',
                    'duty_expt_note': purchase_obj.sp_note_duty_exemption or '',
                    'cert_req': cert_req and "YES" or "NO",
                    'sp_note': purchase_obj.special_notes or '',
                    'remark': purchase_obj.datasheet_remark or ''
                    }
            result.append(vals)
        return result
    
jasper_report.report_jasper('report.datasheet.jasper', 'purchase.order', parser=po_datasheet)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

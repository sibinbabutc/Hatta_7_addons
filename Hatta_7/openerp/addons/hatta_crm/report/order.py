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


class po_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(po_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        pool= pooler.get_pool(cr.dbname)
        user_pool = pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ",Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                'user_name': user_obj.login.upper() or ''
                }
        return vals
    
    def get_total_po(self, cr, uid, po_obj, context=None):
        pool= pooler.get_pool(cr.dbname)
        po_pool = pool.get('purchase.order')
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
    
    def get_cert_obj(self, cr, uid, line, context=None):
        cert_obj = []
        if line.charge_ids and line.certificate_ids:
            cerificate_obj = line.certificate_ids
            charge_cert_objs = [x.charge_id.related_cert_id for x in line.charge_ids if x.charge_id and x.charge_id.related_cert_id and x.pay_to_cust]
            for cert in cerificate_obj:
                if cert not in charge_cert_objs:
                    cert_obj.append(cert)
            return cert_obj
        else:
            return line.certificate_ids
    
    def _get_sheet_name(self, cr, uid, po_boj, context=None):
        curr_id = False
        curr_obj = False
        line_string_list = []
        line_string = ""
        temp_list = []
        seq_data = {}
        seq_list = []
        for line in po_boj.order_line:
            if line.select_line:
                ref_id = line.id
                if line.lead_product_id:
                    ref_id = line.lead_product_id.id
                seq_list.append(ref_id)
                seq_data[ref_id] = line.sequence_no
        for id in seq_list:
            if not curr_id:
                curr_id = id
                temp_list.append(seq_data.get(id, ''))
            else:
                if id != curr_id + 1:
                    temp_list = self.sort(temp_list)
                    if len(temp_list) > 1:
                        line_string = str(temp_list[0]) + " - "  + str(temp_list[-1])
                        line_string_list.append(line_string)
                    elif len(temp_list) == 1:
                        line_string = str(temp_list[0])
                        line_string_list.append(line_string)
                    temp_list = [seq_data.get(id, '')]
                    curr_id = id
                else:
                    temp_list.append(seq_data.get(id, ''))
                    curr_id = id
        if seq_list:
            temp_list.append(seq_data.get(id, ''))
        temp_list = self.sort(temp_list)
        if len(temp_list) > 1:
            line_string = str(temp_list[0]) + " - " + str(temp_list[-1])
            line_string_list.append(line_string)
        elif len(temp_list) == 1:
            line_string = str(temp_list[0])
            line_string_list.append(line_string)
        return ','.join(line_string_list)
    
    def sort(self, data):
        new_data = []
        for i in data:
            if i not in new_data:
                new_data.append(i)
        return new_data
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        pool= pooler.get_pool(cr.dbname)
        purchase_pool = pool.get('purchase.order')
        partner_pool = pool.get('res.partner')
        currency_pool = pool.get('res.currency')
        count = 0
        for purchase_obj in purchase_pool.browse(cr, uid, ids, context=context):
            po_lines = []
            for line in purchase_obj.order_line:
                count += 1
                description = line.name and line.name.upper() or ''
                product_code = line.product_id and line.product_id.default_code or ''
                if product_code:
                    description = "%s\n%s"%(product_code.upper(), description)
                line_vals = ({
                              'si_no': count,
                              'product_name': line.product_id and line.product_id.name or '',
                              'desc': description,
                              'qty': line.product_qty or "0.00",
                              'uom': line.product_uom and line.product_uom.name or '',
                              'price': line.price_unit or "0.00",
                              'price_subtotal': line.price_subtotal or "0.00",
                              'curr_name': purchase_obj.currency_id and purchase_obj.currency_id.name or '',
                              'curr_sym': purchase_obj.currency_id and purchase_obj.currency_id.symbol or '',
#                               'supp_shipping': purchase_obj.supplier_shipping and "True" or "False"
                              })
                cert_charge_lines = []
                for charge in line.charge_ids:
                    if charge.pay_to_cust:
                        count += 1
                        charge_name = charge.charge_id and charge.charge_id.name or ''
                        if charge.info:
                            charge_name += "\n" + charge.info
                        charge_vals = {
                                       'si_no': count,
                                       'charge_name': charge_name,
                                       'charge_amount': charge.amount_fc or 0.00,
                                       'certi': "False",
                                       'curr_name': purchase_obj.currency_id and purchase_obj.currency_id.name or '',
                                       'curr_sym': purchase_obj.currency_id and purchase_obj.currency_id.symbol or '',
                                       }
                        cert_charge_lines.append(charge_vals)
                po_lines.append(line_vals)
            po_charge_lines = []
#             if purchase_obj.supplier_shipping:
            for charge in purchase_obj.charge_ids:
                if charge.pay_to_cust:
                    count += 1
                    charge_name = charge.charge_id and charge.charge_id.name or ''
                    if charge.info:
                        charge_name += "\n" + charge.info.upper()
                    charge_vals = {
                                   'si_no': count,
                                   'charge_name': charge_name,
                                   'charge_amount': charge.amount_fc or "0.00",
                                   'certi': "False",
                                   'curr_name': purchase_obj.currency_id and purchase_obj.currency_id.name or '',
                                   'curr_sym': purchase_obj.currency_id and purchase_obj.currency_id.symbol or '',
                                   }
                    po_charge_lines.append(charge_vals)
            cert_list = []
            for line in purchase_obj.order_line:
                for cert in self.get_cert_obj(cr, uid, line, context=context):
                    if cert.id not in cert_list:
                        count += 1
                        cert_list.append(cert.id)
                        cert_vals = {
                                     'si_no': count,
                                     'charge_name': cert.name or '',
                                     'charge_amount': 0.00,
                                     'certi': "True",
                                     'curr_name': '',
                                     'curr_sym': ''
                                     }
                        po_charge_lines.append(cert_vals)
            quote_date = ''
            if purchase_obj.quote_date:
                quote_date = purchase_obj.quote_date and \
                                    datetime.strptime(purchase_obj.quote_date, '%Y-%m-%d')
                day = quote_date.day
                if day < 10:
                    day = "0"+str(day)
                else:
                    day = str(day)
                month = quote_date.month
                if month < 10:
                    month = "0"+str(month)
                else:
                    month = str(month)
                quote_date = str(day) + "/" + str(month) + "/" + str(quote_date.year)
            del_address = ''
            if purchase_obj.direct_delivery:
                del_address = purchase_obj.direct_del_address or ''
            elif not purchase_obj.direct_delivery and purchase_obj.warehouse_id.partner_id:
                del_address = partner_pool._display_address(cr, uid, purchase_obj.warehouse_id.partner_id,
                                                            context=context)
            del_address = del_address.upper()
            acc_no = purchase_obj.job_id and purchase_obj.job_id.name or purchase_obj.lead_id and \
                            purchase_obj.lead_id.sale_id and purchase_obj.lead_id.sale_id.job_id and \
                            purchase_obj.lead_id.sale_id.job_id.name or purchase_obj.manual_job_id and \
                            purchase_obj.manual_job_id.name or ''
#             acc_no = purchase_obj.job_id and purchase_obj.job_id.name or ''
            partner_code = purchase_obj.customer_id and purchase_obj.customer_id.partner_code or ''
            amount_total = purchase_obj.amount_total or 0.00
            amount_word = currency_pool.amount_word(cr, uid, purchase_obj.currency_id, amount_total,
                                                    context=context)
            
            partner_address = partner_pool._display_address(cr, uid, purchase_obj.partner_id,
                                                            context=context)
            payment_term_note = purchase_obj.payment_term_id and purchase_obj.payment_term_id.note and \
                                    purchase_obj.payment_term_id.note.upper() or False
            line_order = self.get_total_po(cr, uid, purchase_obj, context=context)
            item_no = ''
            item_no = self._get_sheet_name(cr, uid, purchase_obj, context=context)
            delivery_schedule = purchase_obj.delivery_term and purchase_obj.delivery_term.upper() or ''
            incorterm = purchase_obj.incoterm_id and purchase_obj.incoterm_id.name or ''
            if purchase_obj.del_term_place and incorterm:
                incorterm += ", %s"%(purchase_obj.del_term_place and purchase_obj.del_term_place.upper() or '')
            if incorterm:
                delivery_schedule += " / " + incorterm
            partner_contact = ''
            for partner_con in purchase_obj.partner_id.child_ids:
                if partner_con.type == 'procure':
                    partner_contact = partner_con.name
            account_number = ''
            if acc_no:
                account_number = acc_no + " - " + partner_code
            payterm = purchase_obj.payment_term_id and purchase_obj.payment_term_id.name.upper() or ''
            print payterm
            if payment_term_note:
                payterm = "%s\n%s"%(payterm, payment_term_note)
            vals = {
                    'report_name': purchase_obj.state in ['draft', 'sent', 'bid'] and 'DRAFT PURCHASE ORDER' or \
                                                'PURCHASE ORDER',
                    'partner_code': purchase_obj.partner_id and purchase_obj.partner_id.partner_ac_code or '',
                    'title': purchase_obj.partner_id.title and purchase_obj.partner_id.title.name and \
                                    purchase_obj.partner_id.title.name.upper() or '',
                    'partner_name': purchase_obj.partner_id.name and purchase_obj.partner_id.name.upper() or '',
                    'partner_address': partner_address and partner_address.upper(),
                    'partner_phone': purchase_obj.partner_id.phone or '',
                    'partner_fax': purchase_obj.partner_id.fax or '',
                    'po_no': purchase_obj.name or '',
                    'ac_no': account_number,
                    'date_order': purchase_obj.date_order and \
                                        datetime.strptime(purchase_obj.date_order, '%Y-%m-%d') or '',
                    'line_of_order': str(purchase_obj.line_of_order) + " / " + str(line_order),
                    'po_contact': purchase_obj.quote_send_by and purchase_obj.quote_send_by.upper() or '',
                    'supplier_quote_ref': purchase_obj.partner_ref or '',
                    'supplier_quote_date': quote_date,
                    'curr_name': purchase_obj.currency_id and purchase_obj.currency_id.name or '',
                    'curr_sym': purchase_obj.currency_id and purchase_obj.currency_id.symbol or '',
                    'attn': partner_contact and partner_contact.upper(),
#                     'supp_shipping': purchase_obj.supplier_shipping and "True" or "False",
                    'po_lines': po_lines,
                    'note_line': [{'junk': 'junk'}],
                    'po_charge_lines': po_charge_lines,
                    'amount_total': purchase_obj.amount_total or "0.00",
                    'note': purchase_obj.po_notes or '',
                    'special_note': purchase_obj.special_notes or '',
                    'sp_note_duty_exemption': purchase_obj.sp_note_duty_exemption or '',
                    'liquid_damage_note': purchase_obj.liquid_damage_note or '',
                    'end_user': purchase_obj.display_end_user_name and purchase_obj.customer_id and \
                                    purchase_obj.customer_id.name.upper() or purchase_obj.direct_sale_id and\
                                    purchase_obj.direct_sale_id.partner_id.name.upper() or '',
                    'pay_term': payterm,
                    'del_date': purchase_obj.minimum_planned_date and \
                                        datetime.strptime(purchase_obj.minimum_planned_date, '%Y-%m-%d') or '',
                    'del_schedule': delivery_schedule,
                    'delivery_mode': purchase_obj.shipment_method_id and purchase_obj.shipment_method_id.name.upper() or '',
                    'del_address': del_address,
                    'amount_word': amount_word.upper(),
                    'payment_term_note': payment_term_note,
                    'item_no': purchase_obj.item,
                    'discount': purchase_obj.discount or '0.00',
                    'rounding': purchase_obj.rounding or '0.00',
                    'display_del_address': purchase_obj.display_del_address and "true" or "false",
                    'direct_delivery': purchase_obj.direct_purchase and "true" or "false",
                    'lpo': purchase_obj.lpo_no or '',
                    }
            result.append(vals)
        return result
    
jasper_report.report_jasper('report.po.report.jasper', 'purchase.order', parser=po_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

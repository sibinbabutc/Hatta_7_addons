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


class invoice_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(invoice_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        invoice_pool = self.pool.get('account.invoice')
        invoice_obj = invoice_pool.browse(cr, uid, ids[0], context=context)
        label = 'INVOICE'
        if invoice_obj.cash_invoice:
            label = 'CASH INVOICE'
        if invoice_obj.type == 'out_refund':
            label = 'SALES RETURN'
        if invoice_obj.state == 'draft':
            label = 'DRAFT %s'%(label)
        vals={
              'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
              'label': label
              }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        partner_pool = self.pool.get('res.partner')
        user_pool = self.pool.get('res.users')
        invoice_pool = self.pool.get('account.invoice')
        currency_pool = self.pool.get('res.currency')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for inv_obj in invoice_pool.browse(cr, uid, ids, context=context):
            attn = ''
            if inv_obj.parent_partner_id and inv_obj.parent_partner_id != inv_obj.partner_id:
                attn = inv_obj.partner_id.name or ''
            partner_obj = inv_obj.partner_id and inv_obj.partner_id.parent_id or inv_obj.partner_id
            partner_address = partner_pool._display_address(cr, uid, partner_obj, context=context)
            del_list = [x.name for x in inv_obj.rel_picking_ids]
            sale_list = []
            ac_list = []
            shop = 'Hatta AUH'
            if inv_obj.sale_id:
                for picking in inv_obj.sale_id.picking_ids:
                    if picking.state == 'done':
                        if picking.sale_id:
                            sale_list.append(picking.sale_id.name)
                            ac_list.append(picking.sale_id.job_id.name)
                            shop = picking.sale_id.shop_id.name
            sale_list = list(set(sale_list))
            ac_list = list(set(ac_list))
            del_names = '/'.join(del_list)
            sale_names = ' '.join(sale_list)
            ac_names = ' '.join(ac_list)
            if not ac_list:
                ac_names = inv_obj.job_id and inv_obj.job_id.name or ''
            bank_obj = inv_obj.partner_bank_id or False
            if not bank_obj:
                bank_objs = user_obj.company_id and user_obj.company_id.bank_ids and \
                                user_obj.company_id.bank_ids or []
                bank_obj = False
                for bank in bank_objs:
                    if bank.footer:
                        bank_obj = bank
                        break
            bank_details = ''
            shift_code = ''
            iban = ''
            if bank_obj:
                bank_name = bank_obj.bank and bank_obj.bank.name or ''
                bank_street = bank_obj.bank and bank_obj.bank.street or ''
                bank_city = bank_obj.bank and bank_obj.bank.city or ''
                bank_details = bank_name + " " + bank_street + " " + bank_city
                shift_code = bank_obj.bank_bic or ''
                iban = bank_obj.acc_number or ''
            amount_word = currency_pool.amount_word(cr, uid, inv_obj.currency_id, inv_obj.amount_total or 0.00,
                                                    context=context)
            invoice_data = {
                            'attn': attn and attn.upper() or '',
                            'partner_name': partner_obj.name and partner_obj.name.upper() or '',
                            'partner_code': partner_obj.partner_ac_code and partner_obj.partner_ac_code.upper(),
                            'partner_address': partner_address and partner_address.upper(),
                            'inv_no': inv_obj.internal_number,
                            'date': inv_obj.date_invoice and datetime.strptime(inv_obj.date_invoice, '%Y-%m-%d'),
                            'lpo_no': inv_obj.name and inv_obj.name.upper(),
                            'del_no': del_names,
                            'sale_no': sale_names,
                            'currency': inv_obj.currency_id.name,
                            'ac_code': ac_names,
                            'location': shop and shop.upper(),
                            'user': inv_obj.user_id.name.upper(),
                            'total': (inv_obj.amount_total + inv_obj.discount) or '0.00',
                            'bank_details': bank_details and bank_details.upper(),
                            'shift_code': shift_code and shift_code.upper(),
                            'iban': iban and iban.upper(),
                            'amount_word': amount_word.upper(),
                            'show_bal': inv_obj.reg_pay_invoice and "true" or "false",
                            'balance': inv_obj.residual,
                            'paid': (inv_obj.amount_total - inv_obj.residual) or "0.00",
                            'cash_invoice': inv_obj.cash_invoice and "true" or "false",
                            'display_bank_details': inv_obj.display_bank_details and "true" or "false",
                            'discount': inv_obj.discount or 0.00,
                            'net_balance': inv_obj.amount_total,
                            'invoice_type': inv_obj.type,
                            'refund_invoice_no': inv_obj.refund_invoice_id and \
                                                    inv_obj.refund_invoice_id.number or ''
                            }
            lines = []
            for line in inv_obj.invoice_line:
                line_data = {
                             'si_no': line.sequence_no,
                             'product_name': line.product_id and line.product_id.name.upper() or '',
                             'desc': line.name and line.name.upper(),
                             'uom': line.uos_id and line.uos_id.name.upper(),
                             'qty': line.quantity or '0.00',
                             'price_unit': line.price_unit or '0.00',
                             'total': line.price_subtotal or '0.00'
                             }
                lines.append(line_data)
            invoice_data['lines'] = lines
            result.append(invoice_data)
        return result
    
jasper_report.report_jasper('report.invoice_report_jasper', 'stock.picking.out', parser=invoice_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

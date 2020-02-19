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
import itertools
import operator


class crm_sale_quote(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(crm_sale_quote, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        if context is None:
            context = {}
        pool= pooler.get_pool(cr.dbname)
        user_pool = pool.get('res.users')
        claim_pool = pool.get('crm.lead')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ",Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        active_id = context.get('active_id', False)
        currency_code = 'AED'
        if active_id:
            claim_obj = claim_pool.browse(cr, uid, active_id, context=context)
            currency_code = claim_obj.currency_id.name or 'AED'
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                'currency_code': currency_code
                }
        return vals
    
    def get_contact(self, cr, uid, partner_obj, context=None):
        if not partner_obj:
            return ''
        for contact in partner_obj.child_ids:
            if contact.type == 'contact':
                return contact.name
        return ''
    
    def get_opt_seq(self, count):
        seq = ''
        a = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P',
             'Q','R','S','T','U','V','W','X','Y','Z']
        if count < 26:
            seq = a[count]
        return seq
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        crm_pool = self.pool.get('crm.lead')
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for crm_obj in crm_pool.browse(cr, uid, ids, context=context):
            currency_obj = crm_obj.currency_id
            supplier_list = []
            lines = []
            amount_total = 0.00
            gen_lines = []
            option_lines = []
            temp_list = []
            gen_lines = []
            for line in crm_obj.product_lines:
                if not line.selected_pol_id and line.pol_ids and line.overide_sale_price == 0.00:
                    temp_list = []
                    for pol in line.pol_ids:
                        if pol.select_line:
                            net_amount = pol.sale_price * line.product_uom_qty
                            try:
                                sequence = float(line.sequence_no)
                            except:
                                sequence = line.sequence_no
                            line_data = {
                                         'float_seq': sequence or '',
                                         'seq': line.sequence_no or '',
                                         'product_name': line.product_id and line.product_id.name or '',
                                         'product_desc': line.description and line.description.upper() or '',
                                         'qty': line.product_uom_qty or "0.00",
                                         'unit_price': pol.sale_price or 0.00,
                                         'amount_total': net_amount,
                                         'total': 'False',
                                         'lead_line_id': line.id,
                                         'uom_name': line.uom_id and line.uom_id.name or ''
                                          }
                            temp_list.append(line_data)
                    if temp_list:
                        option_lines.append(temp_list)
                else:
                    net_amount = line.price_unit * line.product_uom_qty
                    try:
                        sequence = float(line.sequence_no)
                    except:
                        sequence = line.sequence_no
                    gen_lines.append({
                                     'float_seq': sequence or '',
                                     'seq': line.sequence_no or '',
                                     'product_name': line.product_id and line.product_id.name or '',
                                     'product_desc': line.description and line.description.upper() or '',
                                     'qty': line.product_uom_qty or "0.00",
                                     'unit_price': line.price_unit or 0.00,
                                     'amount_total': net_amount,
                                     'total': 'False',
                                     'lead_line_id': line.id,
                                     'uom_name': line.uom_id and line.uom_id.name or ''
                                      })
            temp_list = sorted(temp_list, key=operator.itemgetter('seq'))
            gen_lines = sorted(gen_lines, key=operator.itemgetter('seq'))
            final_list = []
            if option_lines:
                comb = list(itertools.product(*option_lines))
                count = 0
                for ele in comb:
                    amount_total = 0.00
                    seq_alp = self.get_opt_seq(count)
                    count += 1
                    for main_data in ele:
                        data = main_data.copy()
                        data['option'] = count
                        data['seq'] = "%s (OPTION %s)"%(data['seq'], seq_alp)
                        amount_total += data['amount_total']
                        final_list.append(data)
                    for main_gen in gen_lines:
                        gen = main_gen.copy()
                        amount_total += data['amount_total']
                        gen['option'] = count
                        final_list.append(gen)
                    amount_words = currency_pool.amount_word(cr, uid, currency_obj, amount_total,
                                                             context=context)
                    final_list.append({
                                       'float_seq': 99999999999.00,
                                       'seq': '',
                                       'product_name': amount_words.upper(),
                                       'product_desc': '',
                                       'qty': "0.00",
                                       'unit_price': 0.00,
                                       'amount_total': amount_total or "0.00",
                                       'total': "True",
                                       'option': count,
                                       'lead_line_id': 99999999999,
                                       'uom_name': ''
                                        })
            else:
                amount_total = 0.00
                for main_gen in gen_lines:
                    print main_gen
                    gen = main_gen.copy()
                    amount_total += gen['amount_total']
                    gen['option'] = 0
                    final_list.append(gen)
                amount_words = currency_pool.amount_word(cr, uid, currency_obj, amount_total,
                                                         context=context)
                final_list.append({
                                   'float_seq': 9999999999999999999.00,
                                   'seq': '',
                                   'product_name': amount_words.upper(),
                                   'product_desc': '',
                                   'qty': "0.00",
                                   'unit_price': 0.00,
                                   'amount_total': amount_total or "0.00",
                                   'total': "True",
                                   'option': 0,
                                   'lead_line_id': 9999999999999999999,
                                   'uom_name': '',
                                   'cust_remarks': crm_obj.cust_remark or ''
                                    })
            
            final_list = sorted(final_list, key=operator.itemgetter('option','float_seq'))
            partner_obj = crm_obj.partner_id
            contact_name = crm_obj.contact_id and crm_obj.contact_id.name or ''
            contact = crm_obj.contact_id or partner_obj or ''
            our_ref = crm_obj.reference or ''
            if crm_obj.track_revision and crm_obj.revision_number:
                our_ref = "%s( %s )"%(our_ref, str(crm_obj.revision_number))
            data = {
                    'partner_name': partner_obj and partner_obj.name or '',
                    'contact_name': contact_name,
                    'phone': contact.phone or crm_obj.phone or '',
                    'email': contact.email or crm_obj.email_from or '',
                    'cust_ref': crm_obj.customer_rfq or '',
                    'our_ref': our_ref or '',
                    'product_type': crm_obj.product_type or '',
                    'suppliers': crm_obj.supplier_id and crm_obj.supplier_id.name or '',
                    'lines': final_list,
                    'del_term': crm_obj.delivery_terms,
                    'quote_validity': crm_obj.quote_validity,
                    'pay_term': crm_obj.payment_term_id and crm_obj.payment_term_id.name or False,
                    'amount_total': amount_total,
                    'amount_words': amount_words.upper(),
                    'description': crm_obj.description,
                    'user_name': crm_obj.user_id and crm_obj.user_id.name.upper() or ''
                    }
            result.append(data)
        return result
    
jasper_report.report_jasper('report.crm.sale.quote.wo.header', 'crm.lead', parser=crm_sale_quote)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

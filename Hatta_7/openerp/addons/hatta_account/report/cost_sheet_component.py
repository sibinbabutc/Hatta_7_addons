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


class cost_sheet_component_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(cost_sheet_component_report, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'records'

    def generate_parameters(self, cr, uid, ids, data, context=None):
        return {}
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        curr_pool = self.pool.get('res.currency')
        from_date, to_date = '', ''
        component, po_number, currency, amount, total, amt_total='', '', '', 0.0, 0.0, 0.0
        data = data.get('form', {})
        if data.get('from_date', False):
            from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d')
        if data.get('to_date', False):
            to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d')
            
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        user_name = user_obj.name
        comp_obj = user_obj.company_id
        comp_curr_obj = comp_obj.currency_id
        company = comp_obj.name
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        email = "Email : "+ comp_obj.email
        date_today = datetime.today().strftime("%d/%m/%Y")
        purchase_pool = self.pool.get('purchase.order')
        
        if data:
            search_condition = [('state', 'not in', ('draft', 'sent', 'bid', 'cancel'))]
            if data.get('from_date'):
                search_condition.append(('date_order', '>=', data.get('from_date')))
            if data.get('to_date'):
                search_condition.append(('date_order', '<=', data.get('to_date')))
            if data.get('tran_type_id', False):
                search_condition.append(('transaction_type_id', '=', data['tran_type_id'][0]))
            po_record = purchase_pool.search(cr, uid, search_condition, context=context)
            for po_obj in purchase_pool.browse(cr, uid, po_record, context=context):
                po_number = po_obj.name
                currency = po_obj.foreign_currency.name
                coeff = 1.00000
                if comp_curr_obj.id != po_obj.foreign_currency.id:
                    coeff = curr_pool._get_conversion_rate(cr, uid, po_obj.foreign_currency,
                                                           comp_curr_obj, context=context)
                amount_fc = 0.00
                if data['component'] == 'communication':
                    amount_fc = po_obj.communication_charges
                    component = 'Communication Charges :'
                elif data['component'] == 'bank':
                    amount_fc = po_obj.bank_charges
                    component = 'Bank Charges :'
                elif data['component'] == 'freight':
                    amount_fc = po_obj.freight_charges_lc
                    component = 'Freight Charge :'
                elif data['component'] == 'fob':
                    amount_fc = po_obj.fob_charges_lc
                    component = 'FOB Charge :'
                elif data['component'] == 'other':
                    amount_fc = po_obj.other_charges_lc
                    component = 'Other Charge :'
                elif data['component'] == 'bank_int':
                    amount_fc = po_obj.bank_interest
                    component = 'Bank Interest :'
                elif data['component'] == 'insu':
                    amount_fc = po_obj.insurance_charges
                    component = 'Insurance Charges :'
                elif data['component'] == 'custom_duty':
                    amount_fc = po_obj.customs_duty
                    component = 'Customs Duty :'
                elif data['component'] == 'clearing':
                    amount_fc = po_obj.clg_agent_charges
                    component = 'Clearing Agent Charges :'
                elif data['component'] == 'port_clearance':
                    amount_fc = po_obj.clearing_expenses
                    component = 'Clearing Expenses at Port :'
                elif data['component'] == 'trans_del':
                    amount_fc = po_obj.transport_delivery_expenses
                    component = 'Transport and Delivery Expenses :'
                elif data['component'] == 'misc':
                    amount_fc = po_obj.misc_expenses
                    component = 'Misc Expenses :'
                amount_lc = amount_fc * coeff
                partner_name = po_obj.partner_id.partner_nick_name or po_obj.partner_id.name or ''
                if data.get('exclude_zero', False) and amount_lc == 0.00:
                    continue
                vals = {
                    'company':company,
                    'address':address,
                    'email':email,
                    'user_name' : user_name,
                    'today':date_today,
                    'from_date': from_date,
                    'to_date': to_date,
                    'component':component,
                    'po_number':po_number,
                    'partner_name': partner_name,
                    'job_id': po_obj.job_id and po_obj.job_id.name or '',
                    'currency':currency,
                    'amount_fc':amount_fc or "0.00",
                    'amount_lc': amount_lc or "0.00",
                    }
                result.append(vals)    
        return result

    
jasper_report.report_jasper('report.cost_sheet_component_jasper', 'cost.sheet.component', parser=cost_sheet_component_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
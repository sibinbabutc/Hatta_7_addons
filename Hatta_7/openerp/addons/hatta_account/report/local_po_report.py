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

class local_po_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(local_po_report, self).__init__(cr, uid, ids, data, context)
    
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        return {}
    
    def get_sup_name(self, cr, uid, purchase, context=None):
        sup_name = ''
        for picking in purchase.picking_ids:
            sup_name = picking.partner_id and picking.partner_id.name
        return sup_name
    
    def get_sup_inv_no(self, cr, uid, purchase, context=None):
        sup_inv_no = ''
        for picking in purchase.picking_ids:
            sup_inv_no = picking.invoice_num
        return sup_inv_no
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        total_credit, total_debit = 0, 0 
        balance = 0
        
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        date_from = data['form']['from_date']
        from_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
        date_to = data['form']['to_date']
        to_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
        report_heading = "LPO PROFIT & LOSS (%s - %s)"%(from_date,to_date)
        
        purchase_pool = self.pool.get('purchase.order')
        invoice_pool = self.pool.get('account.invoice')
        
        if data:
            condition = []
            if data['form']['from_date']:
                condition.append(('date_order', '>=', data['form']['from_date']))
            if data['form']['to_date']:
                condition.append(('date_order', '<=', data['form']['to_date']))
            if data['form']['lpo_id'][1]:
                name = data['form']['lpo_id'][1].split(' ')
                condition.append(('name', '=', name[0]))
                
            purchase_ids = purchase_pool.search(cr, uid, condition, context=context)
            if purchase_ids:
                for purchase in purchase_pool.browse(cr, uid, purchase_ids, context=context):
                    lpo_number = purchase.name
                    sup_name = self.get_sup_name(cr, uid, purchase, context=context)
                    sup_inv_no = self.get_sup_inv_no(cr, uid, purchase, context=context)
                    doc_no = purchase.name
                    if purchase.picking_ids:
                        for picking in purchase.picking_ids:
                            if picking.invoice_id.date_invoice:
                                date =  datetime.strptime(picking.invoice_id.date_invoice, "%Y-%m-%d")
                            else:
                                date = ''
                            
                            curr = purchase.foreign_currency.name
                            exchange_rate = picking.invoice_id.exchange_rate
                            if curr != 'AED':
                                amt = picking.invoice_id.amount_total
                                credit = picking.invoice_id.amount_total * exchange_rate
                            else:
                                amt = "0.00"
                                credit = picking.invoice_id.amount_total
                            
                            debit = 0.00
                            total_debit += debit
                            total_credit += credit
                            balance += (debit - credit)
                            
                            vals = {
                                    'company_name': comp_obj.name or '',
                                    'company_address': address,
                                    'company_email': "E-mail :" + comp_obj.email or '',
                                    'report_heading': report_heading,
                                    'lpo_number' : lpo_number,
                                    'supplier_name' : "%s : %s"%(sup_name.upper(),sup_inv_no),
                                    'date' : date,
                                    'doc_no' : doc_no,
                                    'curr' : curr,
                                    'amount' : amt,
                                    'debit' : "0.00",
                                    'credit' : credit or "0.00",
                                    'balance' : balance or "0.00",
                                    'remarks' : "PURCHASE #: %s, SUPPLIER : %s"%(purchase.name, purchase.partner_id.name),
                                    'total_debit' : total_debit or "0.00",
                                    'total_credit' : total_credit or "0.00",
                                    'total_balance' : balance or "0.00",
                                    'profit_loss' : balance or "0.00"
                                    }
                            result.append(vals)
                            
                    else:
                        vals = {
                            'company_name': comp_obj.name or '',
                            'company_address': address,
                            'company_email': "E-mail :" + comp_obj.email or '',
                            'report_heading': report_heading,
                            'lpo_number' : lpo_number,
                            'supplier_name' : "%s : %s"%(sup_name.upper(),sup_inv_no),
                                    }
                        result.append(vals)
                        
                            
                    invoice_ids = invoice_pool.search(cr, uid, [], context=context)
                    for invoice in invoice_pool.browse(cr, uid, invoice_ids, context=context):
                        doc_no = invoice.internal_number
                        for invoice_line in invoice.invoice_line:
                            price = invoice_line.price_unit or 0.00
                            for lpo in invoice_line.lpo_ids:
                                if lpo.purchase_id.id == data['form']['lpo_id'][0]:
                                    remark = "SALES# %s, CUSTOMER: %s"%(doc_no, invoice.parent_partner_id and \
                                                                        invoice.parent_partner_id.name.upper() or \
                                                                        invoice.partner_id.name.upper())
                                    if invoice.date_invoice:
                                        date = datetime.strptime(invoice.date_invoice, "%Y-%m-%d")
                                    else:
                                        date = ''
                                        
                                        
                                    curr = invoice.currency_id.name
                                    if curr != 'AED':
                                        amt = lpo.quantity * price
                                        debit = self.pool.get('res.currency').compute(cr, uid, invoice.currency_id.id,
                                                    comp_obj.currency_id.id, amt, round=True, currency_rate_type_from=False,
                                                    currency_rate_type_to=False, context=context)
                                    else:
                                        amt = "0.00"
                                        debit = lpo.quantity * price
                                        
                                        
                                    credit = 0.00
                                    total_credit += credit
                                    total_debit += debit
                                    balance += (debit - credit)
                                                                        
                                    vals = {
                                        'date' : date,
                                        'doc_no' : doc_no,
                                        'curr' : curr,
                                        'amount' : amt,
                                        'debit' : debit or "0.00",
                                        'credit' : credit or "0.00",
                                        'balance' : balance or "0.00",
                                        'remarks' : remark,
                                        'total_debit' : total_debit or "0.00",
                                        'total_credit' : total_credit or "0.00",
                                        'total_balance' : balance or "0.00",
                                        'profit_loss' : balance or "0.00"
                                            }
                                    result.append(vals)
            else:
                vals = {
                    'company_name': comp_obj.name or '',
                    'company_address': address,
                    'company_email': "E-mail :" + comp_obj.email or '',
                    'report_heading': report_heading,
                        }
                result.append(vals)
                
        return result
    
    
jasper_report.report_jasper('report.local_po_report.jasper', 'local.po.report', parser=local_po_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
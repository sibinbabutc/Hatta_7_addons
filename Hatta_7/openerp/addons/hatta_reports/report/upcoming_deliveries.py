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
from dateutil.relativedelta import relativedelta

from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter


class upcoming_deliveries(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        self.del_done = 0
        self.del_past = 0
        self.del_one = 0
        self.del_fut = 0
        self.del_with_rej = 0
        super(upcoming_deliveries, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_list = []
        rep_type = data['form']['type']
        report_name = ''
        if rep_type == 'upcoming':
            report_name = "UPCOMING DELIVERIES"
        else:
            report_name = "COMPLETED DELIVERIES"
        date_list = []
        if data['form'].get('from_date', False):
            date = datetime.strptime(data['form'].get('from_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
            date_list.append(date)
        if data['form'].get('to_date', False):
            date = datetime.strptime(data['form'].get('to_date'), '%Y-%m-%d').strftime('%d/%m/%Y')
            date_list.append(date)
        if date_list:
            report_name = report_name + " (%s)"%(' - '.join(date_list))
        vals = {
                'company_name': comp_obj.name or '',
                'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                'report_name': report_name,
                'del_done': self.del_done,
                'del_past': self.del_past,
                'del_one': self.del_one,
                'del_fut': self.del_fut,
                'del_with_rej': self.del_with_rej
                }
        return vals
    
    def get_po_details(self, cr, uid, ids, sale_obj, context=None):
        supplier_ids = []
        supp_del_list = []
        purchase_pool = self.pool.get('purchase.order')
        domain = [('state', 'not in', ['draft', 'sent', 'bid', 'cancel'])]
        if sale_obj.lead_id:
            domain.append(('lead_id', '=', sale_obj.lead_id.id))
        else:
            domain.append(('direct_sale_id', '=', sale_obj.id))
        purchase_ids = purchase_pool.search(cr, uid, domain, context=context)
        po_num_list = []
        supp_list = []
        for po_obj in purchase_pool.browse(cr, uid, purchase_ids, context=context):
            po_num_list.append(po_obj.name)
            supp_name = po_obj.partner_id.partner_nick_name or \
                            po_obj.partner_id.name or ''
            supp_list.append(supp_name)
            supplier_ids.append(po_obj.partner_id.id)
            del_date = po_obj.minimum_planned_date
            if del_date:
                del_date = datetime.strptime(del_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                supp_del_list.append(str(del_date))
        po_num_list = list(set(po_num_list))
        supp_list = list(set(supp_list))
        return ', '.join(po_num_list), ', '.join(supp_list), list(set(supplier_ids)), ', '.join(supp_del_list)
    
    def get_delivery_return(self, cr, uid, sale_obj, context=None):
        picking_name = [x.name for x in sale_obj.picking_ids if x.type == 'in']
        return ', '.join(picking_name)
    
    def get_rej_sale_ids(self, cr, uid, ids, cust_id, context=None):
        rej_pool = self.pool.get('rejection.model')
        rej_ids = rej_pool.search(cr, uid, [('state', 'not in', ['draft', 'done', 'cancel'])],
                                  context=context)
        sale_ids = []
        for rej_obj in rej_pool.browse(cr, uid, rej_ids, context=context):
            if rej_obj.picking_id and rej_obj.picking_id.sale_id:
                if cust_id and cust_id[0] != rej_obj.picking_id.sale_id.partner_id.id:
                    continue
                sale_ids.append(rej_obj.picking_id.sale_id.id)
        sale_ids = list(set(sale_ids))
        return sale_ids
    
    def get_dn_details(self, cr, uid, sale_obj, context=None):
        del_list = []
        for picking in sale_obj.picking_ids:
            if picking.state != 'cancel':
                del_list.append(picking.name)
        return ', '.join(del_list)
    
    def get_invoice_details(self, cr, uid, sale_obj, context=None):
        inv_list = []
        for inv in sale_obj.invoice_ids:
            if inv.state != 'cancel':
                inv_list.append(inv.number)
        return ', '.join(inv_list)
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        sale_pool = self.pool.get('sale.order')
        to_date = data['form']['to_date']
        from_date = data['form']['from_date']
        type = data['form']['type']
        cust_id = data['form']['cust_id']
        supp_id = data['form']['supp_id']
        sort_based_on = data['form']['sort_based_on']
        supplier_id = False
        if supp_id:
            supplier_id = supp_id[0]
        rej_sale_ids = self.get_rej_sale_ids(cr, uid, ids, cust_id, context=context)
        domain = [('state', '!=', 'cancel')]
        if type == 'upcoming':
            domain.extend([('shipped', '=', False), ('id', 'not in', rej_sale_ids)])
        else:
            domain.extend([('shipped', '=', True), ('id', 'not in', rej_sale_ids)])
        if to_date:
            domain.append(('date_delivery', '<=', to_date))
        if from_date:
            domain.append(('date_delivery', '>=', from_date))
        if cust_id:
            domain.append(('partner_id', '=', cust_id[0]))
        print domain
        sale_ids = sale_pool.search(cr, uid, domain, context=context)
        if type == 'upcoming':
            sale_ids.extend(rej_sale_ids)
        count = 0
        today = fields.date.today()
        next_month_date = datetime.strptime(today, '%Y-%m-%d') + relativedelta(months=1)
        next_month_date = next_month_date.strftime('%Y-%m-%d')
        for sale_obj in sale_pool.browse(cr, uid, sale_ids, context=context):
            count += 1
            partner_name = sale_obj.partner_id and sale_obj.partner_id.partner_nick_name or \
                                sale_obj.partner_id.name or ''
            po_numbers, supp_names, sale_supp_ids, supp_del_date = self.get_po_details(cr, uid, ids, sale_obj, context=context)
            if supplier_id and supplier_id not in sale_supp_ids:
                continue
            dn_details = self.get_dn_details(cr, uid, sale_obj, context=context)
            inv_details = ''
            if type == 'del_done':
                inv_details = self.get_invoice_details(cr, uid, sale_obj, context=context)
            if sale_obj.date_delivery:
                del_date = datetime.strptime(sale_obj.date_delivery, '%Y-%m-%d')
            else:
                del_date = datetime.strptime(sale_obj.create_date, '%Y-%m-%d %H:%M:%S')
            vals = {
                    'si_no': count,
                    'dn_numbers': dn_details,
                    'invoice_numbers': inv_details,
                    'sale_no': sale_obj.name or '',
                    'partner_name': partner_name,
                    'job_number': sale_obj.job_id and sale_obj.job_id.name or '',
                    'cust_po_number': sale_obj.client_order_ref or '',
                    'del_date': del_date,
                    'po_number': po_numbers,
                    'supp_number': supp_names,
                    'supp_del': supp_del_date,
                    'rejections': self.get_delivery_return(cr, uid, sale_obj, context=context),
                    'color': 'black'
                    }
            if sale_obj.date_delivery:
                if vals.get('rejections', False):
                    self.del_with_rej += 1
                    vals['color'] = 'blue'
                elif type == 'del_done':
                    self.del_done += 1
                    vals['color'] = 'black'
                elif sale_obj.date_delivery <= today:
                    self.del_past += 1
                    vals['color'] = 'red'
                elif sale_obj.date_delivery <= next_month_date:
                    self.del_one += 1
                    vals['color'] = 'pink'
                else:
                    self.del_fut += 1
                    vals['color'] = 'green'
            result.append(vals)
        if sort_based_on == 'date': 
            result = sorted(result, key=itemgetter('del_date'))
        elif sort_based_on == 'cust': 
            result = sorted(result, key=itemgetter('partner_name'))
        elif sort_based_on == 'job': 
            result = sorted(result, key=itemgetter('job_number'))
        return result
    
jasper_report.report_jasper('report.upcoming.delivery.jasper', 'upcoming.delivery.wizard',
                            parser=upcoming_deliveries)
jasper_report.report_jasper('report.delivery.done.jasper', 'upcoming.delivery.wizard',
                            parser=upcoming_deliveries)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

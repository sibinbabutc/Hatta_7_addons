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


class quo_send_status(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(quo_send_status, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)
        date_list = []
        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
            date_list.append(str(start_date))
        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
            date_list.append(str(end_date))
        report_name_sub = ""
        if date_list:
            report_name_sub = "(%s)"%(str(" - ".join(date_list)))
        vals = {
                'company_name': comp_obj.name or '',
                'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                'report_name': "QUOTATION SUBMISSION REPORT %s"%(report_name_sub)
                }
        return vals
    
    def get_value(self,cr, uid, ids, lead_obj, context=None):
        amount = 0.00
        if lead_obj:
            for line in lead_obj.product_lines:
                amount += line.price_unit * line.product_uom_qty
        return amount
    
    def get_supplier_details(self, cr, uid, lead, context=None):
        res = []
        po_pool = self.pool.get('purchase.order')
        po_ids = po_pool.search(cr, uid, [('lead_id', '=', lead.id),
                                          ('state', 'not in', ['draft', 'cancel', 'sent'])],
                                context=context)
        for po_obj in po_pool.browse(cr, uid, po_ids, context=context):
            supplier_name = po_obj.partner_id.partner_nick_name or po_obj.partner_id.name or ''
            res.append(supplier_name)
        return ','.join(list(set(res)))
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        done_qu = []
        status_line_pool = self.pool.get('quotation.status.line')
        claim_pool = self.pool.get('crm.lead')
        line_domain = []
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)
        domain = []
        claim_domain = [('type','=','opportunity')]
        if date_from:
            domain.append(('status_id.date', '>=', str(date_from)))
            claim_domain.append(('date_deadline', '>=', str(date_from)))
        if date_to:
            domain.append(('status_id.date', '<=', str(date_to)))
            claim_domain.append(('date_deadline', '<=', str(date_to)))
        partner_data = data['form'].get('partner_id', False)
        if partner_data:
            domain.append(('partner_id', '=', partner_data[0]))
            claim_domain.append(('partner_id', '=', partner_data[0]))
        line_ids = status_line_pool.search(cr, uid, domain, context=context)
        count = 0
        for line in status_line_pool.browse(cr, uid, line_ids, context=context):
            count += 1
            type = line.submission_type
            remark = line.remark
            all_remark = ''
            if type != 'other':
                all_remark = dict(status_line_pool._columns['submission_type'].selection).get(type)
            if remark:
                all_remark += " - %s"%(remark)
            done_qu.append(line.lead_id.id)
            partner_name = line.partner_id and line.partner_id.partner_nick_name or \
                                line.partner_id.name or ''
            supplier_details = self.get_supplier_details(cr, uid, line.lead_id, context=context)
            vals = {
                    'si_no': count,
                    'date_received': line.received_date and \
                                        datetime.strptime(line.received_date, '%Y-%m-%d') or '',
                    'our_ref': line.lead_id and line.lead_id.reference or '',
                    'client_ref': line.client_ref_no or '',
                    'partner_name': partner_name,
                    'supplier_name': supplier_details,
                    'cl_date': line.closing_date and \
                                        datetime.strptime(line.closing_date, '%Y-%m-%d') or '',
                    'remark': all_remark,
                    'submission_date': line.status_id and \
                                        datetime.strptime(line.status_id.date, '%Y-%m-%d') or '',
                    'submitted_by': line.status_id and line.status_id.user_id and line.status_id.user_id.login or '',
                    'value': line.lead_id and self.get_value(cr, uid, ids, line.lead_id) or "0.00"
                    }
            result.append(vals)
        claim_domain.append(('id', 'not in', done_qu))
        claim_ids = claim_pool.search(cr, uid, claim_domain, context=context)
        result = sorted(result, key=itemgetter("submission_date", "cl_date"))
        claim_lines = []
        for claim_obj in claim_pool.browse(cr, uid, claim_ids, context=context):
            count += 1
            vals = {
                    'si_no': count,
                    'date_received': claim_obj.creation_date and \
                                        datetime.strptime(claim_obj.creation_date, '%Y-%m-%d') or '',
                    'our_ref': claim_obj.reference or '',
                    'client_ref': claim_obj.customer_rfq or '',
                    'partner_name': claim_obj.partner_id and claim_obj.partner_id.name or '',
                    'cl_date': claim_obj.date_deadline and \
                                        datetime.strptime(claim_obj.date_deadline, '%Y-%m-%d') or '',
                    'remark': '',
                    'submission_date': '',
                    'value': claim_obj.amount_total or "0.00"
                    }
            claim_lines.append(vals)
        claim_lines = sorted(claim_lines, key=itemgetter("cl_date"))
        result.extend(claim_lines)
        return result
    
jasper_report.report_jasper('report.quo.send.status.jasper', 'quotation.send.status.report', parser=quo_send_status)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

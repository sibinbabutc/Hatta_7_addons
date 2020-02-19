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


class qotation_status(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(qotation_status, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
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
        stat_pool = self.pool.get('quotation.status')
        stat_line_pool = self.pool.get('quotation.status.line')
        for stat_obj in stat_pool.browse(cr, uid, ids, context=context):
            count = 0
            for line in stat_obj.line_ids:
                count += 1
                type = line.submission_type
                remark = line.remark
                all_remark = ''
                if type != 'other':
                    all_remark = dict(stat_line_pool._columns['submission_type'].selection).get(type)
                if remark:
                    all_remark += " - %s"%(remark)
                partner_name = line.partner_id and line.partner_id.partner_nick_name or \
                                    line.partner_id.name or ''
                supplier_details = self.get_supplier_details(cr, uid, line.lead_id, context=context)
                vals = {
                        'stat_id': stat_obj.id,
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
                        'submitted_by': stat_obj.user_id.login,
                        'value': line.lead_id and self.get_value(cr, uid, ids, line.lead_id) or '0.00'
                        }
                result.append(vals)
        return result
    
jasper_report.report_jasper('report.quotation.status.jasper', 'quotation.status', parser=qotation_status)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

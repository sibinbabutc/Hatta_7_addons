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


class upcoming_quo(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(upcoming_quo, self).__init__(cr, uid, ids, data, context)
        
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
                'report_name': "UPCOMING QUOTATION SUBMISSION %s"%(report_name_sub)
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        claim_pool = self.pool.get('crm.lead')
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)
        claim_domain = [('type','=','opportunity')]
        if date_from:
            claim_domain.append(('date_deadline', '>=', str(date_from)))
        if date_to:
            claim_domain.append(('date_deadline', '<=', str(date_to)))
        partner_data = data['form'].get('partner_id', False)
        if partner_data:
            claim_domain.append(('partner_id', '=', partner_data[0]))
        count = 0
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
                    'created_by': claim_obj.user_id and claim_obj.user_id.name or ''
                    }
            result.append(vals)
        result = sorted(result, key=itemgetter("cl_date"))
        return result
    
jasper_report.report_jasper('report.quo.upcoming.jasper', 'quotation.upcoming.report', parser=upcoming_quo)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

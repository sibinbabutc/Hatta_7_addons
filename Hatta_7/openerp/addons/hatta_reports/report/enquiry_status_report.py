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


class enq_status(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(enq_status, self).__init__(cr, uid, ids, data, context)
        
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
                'report_name': "PURCHASE ORDER SUMMARY REPORT %s"%(report_name_sub)
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        return result
    
jasper_report.report_jasper('report.enq.status.jasper', 'crm.lead', parser=enq_status)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

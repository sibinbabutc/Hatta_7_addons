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


class user_login_log_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(user_login_log_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        if data is None:
            data = {}
        if not data.get('form', False):
            data = {'form': {}}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_from = data['form'].get('from_date', False)
        date_to = data['form'].get('to_date', False)
        start_date = ''
        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
        end_date = ''
        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
        user_data = data['form'].get('user_id', False)
        user_name = ''
        if user_data:
            user_name = user_data[1]
        vals = {
                'company_name': comp_obj.name or '',
                'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                'from_date': start_date,
                'to_date': end_date,
                'user': user_name
                }
        return vals
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        if data is None:
            data = {}
        if not data.get('form', False):
            data = {'form': {}}
        log_pool = self.pool.get('login.log.view')
        date_from = data['form'].get('from_date', False)
        date_to = data['form'].get('to_date', False)
        domain = []
        if date_from:
            domain.append(('login_date', '>=', str(date_from)+" 00:00:00"))
        if date_to:
            domain.append(('logout_date', '<=', str(date_to)+" 23:59:59"))
        user_data = data['form'].get('user_id', False)
        if user_data:
            domain.append(('user_id', '=', user_data[0]))
        if not date_from and not date_to:
            now = datetime.today()
            date_from = str(now.strftime("%Y/%m/%d")) + " 00:00:00"
            date_to = str(now.strftime("%Y/%m/%d")) + " 23:59:59"
            domain.append(('login_date', '>=', date_from))
            domain.extend(['|',('logout_date', '<=', date_to),('logout_date', '=', False)])
        log_ids = log_pool.search(cr, uid, domain, context=context)
        for log_obj in log_pool.browse(cr, uid, log_ids, context=context):
            login = log_obj.login_date and datetime.strptime(log_obj.login_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
            vals = {
                    'user_id': log_obj.user_id and log_obj.user_id.name or '',
                    'date': log_obj.login_date and datetime.strptime(log_obj.login_date.split(".")[0], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y"),
                    'login_date': fields.datetime.context_timestamp(cr, uid, login, context=context),
#                     'logout_date': fields.datetime.context_timestamp(cr, uid, logout, context=context) or '',
                    'state': log_obj.status == 'im_proper' and 'SYSTEM LOGOUT' or log_obj.status == 'proper' and 'USER LOGOUT' or log_obj.status == 'in_use' and 'In Use' or 'PENDING'
                    }
            if log_obj.logout_date:
                logout = log_obj.logout_date and datetime.strptime(log_obj.logout_date.split(".")[0], "%Y-%m-%d %H:%M:%S")
                vals.update({'logout_date': fields.datetime.context_timestamp(cr, uid, logout, context=context)})
            result.append(vals)
            
        result = sorted(result, key=itemgetter("user_id"))
        return result
    
jasper_report.report_jasper('report.user.login.jasper', 'login.log.view', parser=user_login_log_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

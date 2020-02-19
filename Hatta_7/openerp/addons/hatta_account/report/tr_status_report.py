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
from tools.translate import _


class tr_status_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(tr_status_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        tr_pool = self.pool.get('tr.details')
        user_pool = self.pool.get('res.users')
        tr_model_pool = self.pool.get('tr.model')
        tr_pool = self.pool.get('tr.details')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        tr_obj = tr_model_pool.browse(cr, uid, data['form']['tr_model_id'][0], context=context)
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        tr_no = data['form']['tr_model_id'][1]
        domain = ['|', ('start_date', '<=', from_date),
#                   ('settle_date', '<=', from_date),
                  ('tr_model_id.id', '=', data['form']['tr_model_id'][0]),
                  ('state', 'not in', ['draft', 'cancel'])]
        tr_ids = tr_pool.search(cr, uid, domain, context=context)
        used = 0.00
        cleared = 0.00
        for tr in tr_pool.browse(cr, uid, tr_ids, context=context):
            if tr.start_date <= from_date:
                used += tr.amount
#             if tr.state == 'settle' and tr.settle_date <= from_date:
            if tr.state == 'settle':
                cleared += tr.amount
        balance = used - cleared
        return {
                'company_name': user_obj.company_id.name or '',
                'current_date_time': date_start,
                'tr' : "(TR #: %s)"%(data['form']['tr_model_id'][1]),
                'tr_limit': tr_obj.limit - balance,
                'tr_full_limit': tr_obj.limit
                }
    
    def get_opening_balance(self, cr, uid, ids, from_date, tr_model_id, context=None):
        tr_pool = self.pool.get('tr.details')
        
        
        domain = ['|', ('start_date', '<', from_date),
#                   ('settle_date', '<', from_date),
                  ('tr_model_id.id', '=', tr_model_id),
                  ('state', 'not in', ['draft', 'cancel'])]
        tr_ids = tr_pool.search(cr, uid, domain, context=context)
        used = 0.00
        cleared = 0.00
        for tr in tr_pool.browse(cr, uid, tr_ids, context=context):
            if tr.start_date < from_date:
                used += tr.amount
#             if tr.state == 'settle' and tr.settle_date < from_date:
            if tr.state == 'settle':
                cleared += tr.amount
        if used > 0.00 or cleared > 0.00:
            return {
                    'tt_date': datetime.strptime(from_date, '%Y-%m-%d'),
                    'amount_cleared': cleared or 0.00,
                    'amount_used': used or 0.00,
                    'cr_days': 0.00,
                    'note': "OPENING BALANCE",
                    'disb_id': ''
                    }
        else:
            return {}
        
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        tr_pool = self.pool.get('tr.details')
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        tr_no = data['form']['tr_model_id'][1]
        domain = ['|', '&', ('start_date', '>=', from_date), ('start_date', '<=', to_date),
#                   '&', ('settle_date', '>=', from_date), ('settle_date', '<=', to_date),
                  ('tr_model_id.id', '=', data['form']['tr_model_id'][0]),
                  ('state', 'not in', ['draft', 'cancel'])]
        opening_data = self.get_opening_balance(cr, uid, ids, from_date,
                                                data['form']['tr_model_id'][0], context=context)
        if opening_data:
            result.append(opening_data)
        tr_ids = tr_pool.search(cr, uid, domain, context=context)
        for tr_obj in tr_pool.browse(cr, uid, tr_ids, context=context):
            if tr_obj.start_date >= from_date and \
                                tr_obj.start_date <= to_date:
                data = {
                        'tr' : "(TR #: %s)"%(tr_no),
                        'tt_date': datetime.strptime(tr_obj.start_date, '%Y-%m-%d'),
                        'amount_cleared': 0.00,
                        'amount_used': tr_obj.amount or "0.00",
                        'cr_days': tr_obj.duration or "0.00",
                        'due_date': datetime.strptime(tr_obj.closing_date, '%Y-%m-%d'),
                        'note': tr_obj.note or '',
                        'disb_id': tr_obj.voucher_id and tr_obj.voucher_id.name or ''
                        }
                result.append(data)
            if tr_obj.state == 'settle':
                for settle_obj in tr_obj.settle_ids:
                    if settle_obj.settle_date >= from_date and settle_obj.settle_date <= to_date:
                        settle_data = {
                                       'tr' : "(TR #: %s)"%(tr_no),
                                       'tt_date': datetime.strptime(settle_obj.settle_date, '%Y-%m-%d'),
                                       'amount_cleared': settle_obj.amt_cleared or "0.00",
                                       'amount_used': 0.00,
                                       'cr_days': 0.00,
                                       'note': settle_obj.settle_note or '',
                                       'disb_id': settle_obj.settle_voucher_id and settle_obj.settle_voucher_id.name or ''
                                       }
                        result.append(settle_data)
        result = sorted(result, key=itemgetter('tt_date'))
        return result
    
jasper_report.report_jasper('report.tr.status.report.jasper', 'tr.status.report.wizard', parser=tr_status_report)
jasper_report.report_jasper('report.tr.status.report.xls.jasper', 'tr.status.report.wizard', parser=tr_status_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

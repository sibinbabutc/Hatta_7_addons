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
from tools.translate import _


class tr_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(tr_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true',
            'net.sf.jasperreports.export.xls.detect.cell.type': 'true',
            'net.sf.jasperreports.export.xls.white.page.background': 'true',
            'net.sf.jasperreports.export.xls.show.gridlines': 'true',
            }
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        tr_pool = self.pool.get('tr.details')
        user_pool = self.pool.get('res.users')
        tr_num = False
        if data['form']['tr_model_id']:
            tr_num = data['form']['tr_model_id'][0]
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        total_tr = tr_pool.get_tr_amount(cr, uid, ['open', 'settle'], tr_num)
        open_tr = tr_pool.get_tr_amount(cr, uid, ['open'], tr_num)
        closed_tr = tr_pool.get_tr_amount_settle(cr, uid, ['settle'], tr_num)
        company_tr_limit = 0.00
        for tr_limit in user_obj.company_id.tr_limit:
            if tr_num:
                if tr_num == tr_limit.id:
                    company_tr_limit += tr_limit.limit or 0.00
            else:
                company_tr_limit += tr_limit.limit or 0.00
        balance_tr = company_tr_limit - open_tr
        vals = {
                'company_name': user_obj.company_id.name or '',
                'current_date_time': date_start,
                'total_tr': total_tr or 0.00,
                'open_tr': open_tr or 0.00,
                'closed_tr': closed_tr or 0.00,
                'company_tr_limit': company_tr_limit or 0.00,
                'balance_tr': balance_tr or 0.00
                }
        if data['report_type']=='xls':
            vals.update({'IS_IGNORE_PAGINATION':True})
        return vals
    
    def _get_closing_interest(self, tr, amount):
        start_date = datetime.strptime(tr.start_date, "%Y-%m-%d")
        today = datetime.today()
        end_date = datetime.strptime(tr.closing_date, "%Y-%m-%d")
        final_days = (end_date - start_date).days
        int_rate = tr.interest_rate/ 100.00
        priciple = amount or 0.00
        final_interest = (priciple * (1.00 + (int_rate * (final_days / 365.00)))) - priciple
        return final_interest
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        tr_num = ''
        tr_pool = self.pool.get('tr.details')
        domain = []
        if data['form']['from_date']:
            domain.append(('closing_date', '>=', data['form']['from_date']))
        if data['form']['to_date']:
            domain.append(('closing_date', '<=', data['form']['to_date']))
        if data['form']['tr_model_id']:
            tr_num = data['form']['tr_model_id'][1]
            domain.append(('tr_model_id.id', '=', data['form']['tr_model_id'][0]))
        state = []
        wiz_type = data['form']['type']
        if wiz_type == 'open_settle':
            state = ['open', 'settle']
        else:
            state = [wiz_type]
        if state:
            domain.append(('state', 'in', state))
        tr_ids = tr_pool.search(cr, uid, domain, context=context)
        if tr_ids:
            for tr in tr_pool.browse(cr, uid, tr_ids, context=context):
                amount = 0.0
                if tr.state == 'open' and tr.started_settlement:
                    amount = tr.amount - tr.amount_total
                    intrest_clsoing = self._get_closing_interest(tr, amount)
#                     if intrest:
#                         intrest_clsoing = intrest and intrest[0] or 0.0
                else:
                    amount = tr.amount
                    intrest_clsoing = tr.final_interest
                vals = {
                        'tr' : "(TR #: %s)"%(tr_num),
                        'tr_no': tr.name,
                        'tr_start_date': datetime.strptime(tr.start_date, '%Y-%m-%d'),
                        'tr_closing_date': datetime.strptime(tr.closing_date, '%Y-%m-%d'),
                        'amount': amount or "0.00",
                        'interest_rate': tr.interest_rate / 100.00 or "0.00",
                        'duration': tr.duration,
                        'int_clsoing':intrest_clsoing or "0.00",
                        'int_today': tr.interest_today or "0.00",
                        'purpose': tr.note
                        }
                result.append(vals)
        else:
            vals = {
                    'tr' : "(TR #: %s)"%(tr_num),
                    }
            result.append(vals)
        return result
    
jasper_report.report_jasper('report.tr.report.jasper', 'tr.report.wizard', parser=tr_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
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

from osv import osv, fields

import time
from dateutil.relativedelta import relativedelta
from datetime import datetime

class ageing_report(osv.osv_memory):
    _name = 'partner.ageing.report.wizard'
    
    def _get_chart_account(self, cr, uid, context=None):
        account_pool = self.pool.get('account.account')
        account_ids = account_pool.search(cr, uid, [('parent_id', '=', False)], context=context)
        return account_ids and account_ids[0] or False
    
    _columns = {
                'chart_account_id': fields.many2one('account.account', 'Chart of Account',
                                                    domain="[('parent_id', '=', False)]"),
                'report_date': fields.date('Report As On'),
                'account_analytic_id': fields.many2one('account.analytic.account',
                                                       'Cost Center'),
                'partner_id': fields.many2one('res.partner', 'Partner'),
                'print_type': fields.selection([('customer', 'Receivable'),
                                                ('supplier', 'Payable'),
                                                ('customer_supplier', 'Receivable and Payable')],
                                               'Type'),
                'mode': fields.selection([('detail', 'Detail'),
                                          ('summary', 'Summary')],
                                         'Report Type'),
                'report_type': fields.selection([('pdf', 'PDF'),
                                                 ('xls', 'Excel')],
                                                'Report Type')
                }
    _defaults = {
                 'chart_account_id': _get_chart_account,
                 'print_type': 'customer',
                 'report_date': lambda self, cr, uid, context={}: context.get('date', time.strftime("%Y-%m-%d")),
                 'mode': 'detail',
                 'report_type': 'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        res = {}
        data = self.read(cr, uid, ids, context={})[0]
        start = datetime.strptime(data['report_date'], "%Y-%m-%d")
        period_length = 29
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data.update(res)
        datas = {'form': data}
        mode = data.get('mode', 'detail')
        if mode == 'detail':
            report_name = 'partner.ageing.jasper'
        else:
            report_name = 'partner.ageing.summary.jasper'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
                'nodestroy': True,
                }
    
ageing_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

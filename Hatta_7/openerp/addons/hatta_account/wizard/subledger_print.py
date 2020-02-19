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
from datetime import datetime
from dateutil.relativedelta import relativedelta

class subledger_print(osv.osv_memory):
    _name = 'subledger.print'
    _description = 'Subledger Printing'
    
    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = [('company_id', '=', company_id), ('date_start', '<=', now), ('date_stop', '>=', now)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False
    
    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False),
                                                                     ('company_id', '=', user.company_id.id)],
                                                           limit=1)
        return accounts and accounts[0] or False
    
    _columns ={
               'chart_account_id': fields.many2one('account.account', 'Chart of Account',
                                                   help='Select Charts of Accounts', required=True,
                                                   domain = [('parent_id','=',False)]),
               'start_date': fields.date('Start Date'),
               'end_date': fields.date('End Date'),
               'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
               'account_id': fields.many2one('account.account', domain="[('type', '!=', 'view')]",
                                             string='Control A/C'),
               'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
               'partner_id': fields.many2one('res.partner', 'Sub Ledger Code From',
                                             domain="[('parent_id','=',False)]"),
               'partner_id_to': fields.many2one('res.partner', 'Sub Ledger Code To',
                                             domain="[('parent_id','=',False)]"),
               'include_matching_tran': fields.boolean('Include Matching Transaction'),
               'job_subledger': fields.boolean('Job Sub ledger'),
               'job_id': fields.many2one('job.account', 'Job Account'),
               'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'Excel')],
                                               'Report Type', required=True)
               }
    _defaults = {
                 'fiscalyear_id': _get_fiscalyear,
                 'chart_account_id': _get_account,
                 'start_date': '2003-01-01',
                 'end_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'report_type': 'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        res = {}
        data = self.read(cr, uid, ids, context={})[0]
        start = datetime.strptime(data['end_date'], "%Y-%m-%d")
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
        if data.get('job_subledger', False):
            report_name = 'job.subledger.jasper'
        else:
            report_name = 'subledger.jasper'
            if data['report_type'] == 'xls':
                report_name = 'subledger.jasper.xls'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
                'nodestroy': True,
                'report_type': data['report_type']
                }
    
subledger_print()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

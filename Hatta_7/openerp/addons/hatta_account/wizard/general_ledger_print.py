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

class general_ledger_print(osv.osv_memory):
    _name = 'general.ledger.print'
    _description = 'General Ledger Wizard'
    
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
    
    def _get_from_date(self, cr, uid, context=None):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        now = time.strftime('%Y-%m-%d')
        fiscalyears = fiscalyear_obj.search(cr, uid, [('date_start', '<=', now), ('date_stop', '>=', now)], limit=1 )
        fiscal_year_id = fiscalyears and fiscalyears[0] or False
        start_date = fiscalyear_obj.browse(cr, uid, fiscal_year_id, context=context).date_start
        return start_date
    
    def onchange_account_from(self, cr, uid, ids, start_account_id, end_account_id, context=None):
        res = {'value': {}}
        if start_account_id:
            if not end_account_id:
                res['value']['end_account_id'] = start_account_id
        return res
    
    def onchange_account_to(self, cr, uid, ids, end_account_id, start_account_id, context=None):
        res = {'value': {}}
        if end_account_id:
            if not start_account_id:
                res['value']['start_account_id'] = end_account_id
        return res
    
    _columns = {
                'chart_account_id': fields.many2one('account.account', 'Chart of Account',
                                                   help='Select Charts of Accounts', required=True,
                                                   domain = [('parent_id','=',False)]),
                'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'start_account_id': fields.many2one('account.account', 'Account Code From',
                                                    domain="[('type', '!=', 'view')]"),
                'end_account_id': fields.many2one('account.account', 'Account Code To',
                                                  domain="[('type', '!=', 'view')]"),
                'date_from': fields.date('From Date'),
                'date_to': fields.date('To Date'),
                'print_forign_curr': fields.boolean('Print Foreign Currency'),
                'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'EXCEL')], 'Format', required=True),
                }
    _defaults = {
                 'fiscalyear_id': _get_fiscalyear,
                 'chart_account_id': _get_account,
                 'date_from': _get_from_date,
                 'date_to': lambda *a: time.strftime('%Y-%m-%d'),
                 'report_type': 'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        account_pool = self.pool.get('account.account')
        user_pool = self.pool.get('res.users')
        data = self.read(cr, uid, ids, context={})[0]
        start_account_data = data.get('start_account_id', False)
        end_account_data = data.get('end_account_id', False)
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_id= user_obj.company_id and user_obj.company_id.id or False
        start_account_code = ''
        end_account_code = ''
        if start_account_data:
            start_account_obj = account_pool.browse(cr, uid, start_account_data[0], context=context)
            start_account_code = start_account_obj.code or ''
        if end_account_data:
            end_account_obj = account_pool.browse(cr, uid, end_account_data[0], context=context)
            end_account_code = end_account_obj.code or ''
        account_ids = account_pool.search(cr, uid, [('type', '!=', 'view'),
                                                    ('company_id', '=', company_id)], context=context)
        real_account_ids = []
        for account in account_pool.browse(cr, uid, account_ids, context=context):
            cons = True
            account_code = account.code
            if start_account_code and account_code < start_account_code:
                cons = False
            if end_account_code and account_code > end_account_code:
                cons = False
            if cons:
                real_account_ids.append(account.id)
        data['account_ids'] = real_account_ids
        datas = {'form': data}
        report_name = 'general_ledger.jasper'
        if data['print_forign_curr']:
            report_name = 'general_ledger_fc.jasper'
        if data['report_type'] == 'xls':
            report_type = 'xls'
        else:
            report_type = 'pdf'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'report_type': report_type,
                'datas': datas,
                'nodestroy': True,
                }
    
general_ledger_print()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

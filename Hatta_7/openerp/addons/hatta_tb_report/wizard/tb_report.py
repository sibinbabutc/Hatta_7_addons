# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2012 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
#    conatct@zbeanztech.com
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

class trial_balance_report(osv.osv_memory):
    _name = 'trial.balance.webkit'
    
    
    
    def _get_company(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid).company_id.id
        return company_id
    
#     def _get_fiscalyear(self, cr, uid, context=None):
#         now = time.strftime('%Y-%m-%d')
#         fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
#         return fiscalyears and fiscalyears[0] or False
    
    def _get_from_date(self, cr, uid, context=None):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        now = time.strftime('%Y-%m-%d')
        fiscalyears = fiscalyear_obj.search(cr, uid, [('date_start', '<=', now), ('date_stop', '>=', now)], limit=1 )
        fiscal_year_id = fiscalyears and fiscalyears[0] or False
        start_date = fiscalyear_obj.browse(cr, uid, fiscal_year_id, context=context).date_start
        return start_date
    
    def onchange_start_account_id(self, cr, uid, ids, start_account_id):
        v = {}
        if start_account_id:
            v['end_account_id'] = start_account_id
        return {'value': v}
    
    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id):
        v = {}
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        if fiscalyear_id:
            start_date = fiscalyear_obj.browse(cr, uid, fiscalyear_id).date_start
            stop_date = fiscalyear_obj.browse(cr, uid, fiscalyear_id).date_stop
            today = time.strftime('%Y-%m-%d')
            fiscalyear = fiscalyear_obj.browse(cr, uid, fiscalyear_id).name
            year = str(today).split('-')
            if year[0] == fiscalyear:
                v['to_date'] = today
            else:
                v['to_date'] = stop_date
            v['from_date'] = start_date
        return {'value': v}
    
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
        
    
    _columns = {
        'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'XLS')], 'Format', required=True),
        'language': fields.selection([('en_US', 'English'), ('ar_AR', 'Arabic'), ('en_ar', 'English and Arabic')], 'Language', required=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
        'type': fields.selection([('summary', 'Summary'), ('detail', 'Detailed')], 'Type', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'start_account_id': fields.many2one('account.account', 'Starting'),
        'end_account_id': fields.many2one('account.account', 'Ending'),
        'from_date': fields.date('From Date'),
        'to_date': fields.date('To Date'),
        'display_zero': fields.boolean('Display Zero Balance'),
        'display_view': fields.boolean('Display View Account')
        }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids)[0]
        account_ids = []
        account_codes = ''
        if context is None:
            context = {}
        domain = []
        account_pool = self.pool.get('account.account')
        if data.type == 'summary':
            domain = [('type', '=', 'view')]
        if data.start_account_id and data.end_account_id:
            start_code = account_pool.browse(cr, uid, data.start_account_id.id, context=context).code
            end_code = account_pool.browse(cr, uid, data.end_account_id.id, context=context).code
            account_codes += '[' + start_code + '-' + end_code + ']'
            acc_ids = account_pool.search(cr, uid, [('type', '!=', 'view'), ('company_id', '=', data.company_id.id)], context=context)
            acc_code = []
            for account_obj in account_pool.browse(cr, uid, acc_ids, context=context):
                code = account_obj.code
                acc_code.append(code)
            acc_code.sort()
            for code in acc_code:
                if start_code <= code <= end_code:
                    code = str(code)
                    acc_ids = account_pool.search(cr, uid, [('code', '=', code), ('company_id', '=', data.company_id.id)], context=context)
                    account_ids.append(acc_ids[0])
        else:
            domain.append(('company_id', '=', data.company_id.id))
            account_ids = account_pool.search(cr, uid, domain)
        type_dict = {'summary': 'Summary', 'detail': 'Detailed'}
        type = type_dict[data.type]
        if data.language == 'ar_AR':
            if type == 'Summary':
                type = 'خلاصة'
            elif type == 'Detailed':
                type = 'مفصل'
        elif data.language == 'en_ar':
            if type == 'Summary':
                type = 'Summary خلاصة '
            elif type == 'Detailed':
                type = 'Detailed مفصل'
#        else:
#            type = type_dict[data.type]
        datas = {
        'ids': account_ids,
        'model': 'sale.order',
        'report_type': data.report_type,
        'fiscalyear': data.fiscalyear_id.id,
        'company_id': data.company_id.id,
        'start_account_id': data.start_account_id.id,
        'end_account_id': data.end_account_id.id,
        'from_date': data.from_date,
        'to_date': data.to_date,
        'account_codes': account_codes,
        'type': type,
        'language': data.language,
        'display_zero': data.display_zero,
        'display_view': data.display_view
        }
        if data.type == 'summary':
            if data.report_type == 'xls':
                report_name = 'jasper_trial_balance_xls'
            else:
                report_name = 'jasper_trial_balance'
        else:
            if data.report_type == 'xls':
                report_name = 'jasper_trial_balance_detail_xls'
            else:
                report_name = 'jasper_trial_balance_detail'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
            'nodestroy': True,
            }
    
    _defaults = {
        'company_id': _get_company,
        'fiscalyear_id': _get_fiscalyear,
        'from_date': _get_from_date,
        'to_date': lambda *a: time.strftime('%Y-%m-%d'),
        'report_type': 'pdf',
        'type': 'detail',
        'language': 'en_US'
        }
trial_balance_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

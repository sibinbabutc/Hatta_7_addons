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
from tools.translate import _

class profit_and_loss_wizard(osv.osv_memory):
    _name = 'profit.loss.wizard'
    _description = 'Profit and Loss'
    
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
        report_type = context.get('print_report_type', 'pl')
        if report_type == 'bl':
            start_date = "2014-01-01"
        return start_date
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        fin_report_pool = self.pool.get('account.financial.report')
        res = super(profit_and_loss_wizard, self).default_get(cr, uid, fields, context=context)
        report_type = context.get('print_report_type', 'pl')
        fin_report_ids = fin_report_pool.search(cr, uid, [('parent_id', '=', False),
                                                          ('report_type', '=', report_type)])
        if not fin_report_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("Please Configure Financial Report!!!"))
        res['account_report_id'] = fin_report_ids[0]
        fin_report_obj = fin_report_pool.browse(cr, uid, fin_report_ids[0], context=context)
        res['fin_report_type'] = fin_report_obj.report_type
        return res
    
    _columns = {
                'chart_account_id': fields.many2one('account.account', 'Chart of Account',
                                                    help='Select Charts of Accounts', required=True,
                                                    domain = [('parent_id','=',False)]),
                'date_from': fields.date('From Date'),
                'date_to': fields.date('To Date'),
                'cost_center_ids': fields.many2many('account.analytic.account', 'cost_center_ana_rel1',
                                                    'wizard_id1', 'cc_id1', 'Cost Center'),
                'account_report_id': fields.many2one('account.financial.report', 'Account Reports',
                                                     required=True),
                'view_all': fields.boolean('View All Account ?'),
                'fin_report_type': fields.selection([('bl', 'Balance Sheet'), ('pl', 'Profit & Loss')],
                                                    'Report Type'),
                'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'Excel')],
                                                'Report Type'),
                }
    _defaults = {
                 'chart_account_id': _get_account,
                 'date_from': _get_from_date,
                 'date_to': lambda *a: time.strftime('%Y-%m-%d'),
                 'report_type': 'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        data['chart_account_id'] = data['chart_account_id'][0]
        data['filter_cmp'] = 'filter_no'
        data['filter'] = 'filter_date'
        data['debit_credit'] = False
        data['enable_filter'] = False
        report_name = 'balance_sheet_jasper'
        if data['report_type'] == 'xls':
            report_name = 'balance_sheet_jasper_xls'
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
                'nodestroy': True,
                }
    
profit_and_loss_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class cost_sheet_analysis(osv.osv_memory):
    _name = 'cost.sheet.analysis'
    _description = 'Cost Sheet Analysis'
    _columns = {
                'from_date': fields.date('Date From'),
                'to_date': fields.date('Date To'),
                'job_id': fields.many2one('job.account', 'A/C #'),
                'partner_id': fields.many2one('res.partner', 'Customer',
                                              domain="[('customer', '=', True), ('is_company','=', True)]"),
                'supplier_id': fields.many2one('res.partner', 'Supplier',
                                               domain="[('supplier', '=', True), ('is_company','=', True)]"),
                'transaction_type_id': fields.many2one('account.analytic.account',
                                                       'Transaction Type'),
                'duty_account_id': fields.many2one('account.account', 'Duty Account',
                                                   domain="[('type', '!=', 'view')]"),
                'bank_int_account_id': fields.many2one('account.account', 'Bank Interest Account',
                                                       domain="[('type', '!=', 'view')]"),
                'insu_account_id': fields.many2one('account.account', 'Insurance Account',
                                                   domain="[('type', '!=', 'view')]"),
                'tel_account_id': fields.many2one('account.account', 'Telephone Account',
                                                   domain="[('type', '!=', 'view')]"),
                'freight_account_id': fields.many2one('account.account', 'Freight Account',
                                                      domain="[('type', '!=', 'view')]")
                }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'cost.sheet.analysis.jasper',
                'datas': datas,
                'nodestroy' : True,
                'report_type': 'xls'
                }
    
cost_sheet_analysis()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

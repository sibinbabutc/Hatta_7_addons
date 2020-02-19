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

class rec_report_wizard(osv.osv_memory):
    _name = 'rec.report.wizard'
    _description = 'Reconcililation Report'
    _columns = {
                'from_date': fields.date('Date From'),
                'to_date': fields.date('Date To'),
                'bank_account_id': fields.many2one('account.account', 'Bank Account',
                                                   domain="[('user_type.code', '=', 'bank')]"),
                'type': fields.selection([('reconciled', 'Reconciled'),
                                          ('un_recon', 'To Reconcile'),
                                          ('all', 'All')], 'Show Only')
                }
    _defaults = {
                 'type': 'all'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'bank.rec.jasper',
                'datas': datas,
                'nodestroy': True,
                }
    
rec_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

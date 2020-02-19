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

class daily_bank_reconciliation_wizard(osv.osv_memory):
    _name = 'daily.bank.reconciliation.wizard'
    _description = 'Daily Bank Reconciliation Report Wizard'
    _columns = {
        'bank_id': fields.many2one('res.partner.bank', 'Bank'),
#         'account_id' : fields.many2one('account.account', string="Account", required=True),
        'date' : fields.date('As On', required=True)
                }
    
    _defaults = {
        'date' :fields.datetime.now
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = {}
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        datas = {
            'title': 'Daily Bank Reconciliation Report',
            'bank_id':data.bank_id.id,
            'date':data.date,
                }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'daily_bank_reconciliation_jasper',
            'datas': datas,
            'nodestroy' : True,
            'report_type': 'xls'
            }

daily_bank_reconciliation_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
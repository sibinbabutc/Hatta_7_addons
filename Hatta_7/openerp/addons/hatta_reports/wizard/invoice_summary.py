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

class invoice_summary(osv.osv_memory):
    _name = 'invoice.summary'
    _description = 'Invoice Summary Report'
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'inv_id': fields.many2one('account.invoice', 'Invoice'),
                'partner_id': fields.many2one('res.partner', 'Customer'),
                'date_from': fields.date('Date From'),
                'date_to': fields.date('Date To'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'inv.summary.jasper',
                'datas': datas,
                'nodestroy': True,
                }
    
invoice_summary()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

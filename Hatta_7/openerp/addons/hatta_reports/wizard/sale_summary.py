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

class sale_summary(osv.osv_memory):
    _name = 'sale.summary'
    _description = 'Sale Summary Report'
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'sale_id': fields.many2one('sale.order', 'Sale Order'),
                'partner_id': fields.many2one('res.partner', 'Customer'),
                'date_from': fields.date('Date From'),
                'date_to': fields.date('Date To'),
                'user_id': fields.many2one('res.users', 'Sale Person'),
                'product_id': fields.many2one('product.product', 'Product'),
                'filter_on': fields.selection([('posted', 'Posted'), ('unposted', 'Un-Posted'),
                                               ('all', 'All')], 'Filter On', required=True),
                'shop_id': fields.many2one('sale.shop', 'Location'),
                'del_but_not_inv': fields.boolean('Print Delivered But Not Invoiced'),
                'sale_cancelled': fields.boolean('Print Sale Order Cancelled'),
                'sort_based_on': fields.selection([('date', 'Order Date'),
                                                   ('seq', 'Order #'),
                                                   ('cust', 'Customer')],
                                                  'Sort Based On'),
                'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'EXCEL')], 'Format'),
                }
    _defaults = {
                 'filter_on': 'all',
                 'sort_based_on': 'date',
                 'date_to': lambda *a: time.strftime('%Y-%m-%d'),
                 'report_type':'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        if data['report_type'] == 'xls':
            report_type = 'xls'
        else:
            report_type = 'pdf'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'sale.summary.jasper',
                'datas': datas,
                'report_type': report_type,
                'nodestroy': True,
                }
    
sale_summary()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class delivery_order_summary(osv.osv_memory):
    _name = 'delivery.order.summary'
    _description = 'Delivery Order Summary'
    _columns = {
                'from_date': fields.date('From'),
                'to_date': fields.date('To'),
                'partner_id': fields.many2one('res.partner', 'Customer',
                                              domain="[('customer', '=', True), ('is_company', '=', True)]"),
                'report_type': fields.selection([('pdf', 'PDF'),
                                                 ('xls', 'Excel')],
                                                'Report Type'),
                'sort_based_on': fields.selection([('seq', 'DN Number'),
                                                   ('date', 'Date'), ('cust', 'Customer'),
                                                   ('job', 'Job No')],
                                                  'Sort Based On')
                }
    _defaults = {
                 'report_type': 'pdf',
                 'sort_based_on': 'seq'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'delivery_order_summary_jasper',
                'datas': data,
                'nodestroy': True,
                }
    
delivery_order_summary()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

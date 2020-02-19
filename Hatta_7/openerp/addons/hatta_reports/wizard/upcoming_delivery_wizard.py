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

class upcoming_delivery_wizard(osv.osv_memory):
    _name = 'upcoming.delivery.wizard'
    _description = 'Upcoming Delivery Wizard'
    _columns = {
                'from_date': fields.date('From Date'),
                'to_date': fields.date('To Date'),
                'type': fields.selection([('upcoming', 'Upcoming Deliveries'),
                                          ('del_done', 'Delivery Done')],
                                         'Report Type', required=True),
                'cust_id': fields.many2one('res.partner', 'Customer',
                                           domain="[('customer', '=', True)]"),
                'supp_id': fields.many2one('res.partner', 'Supplier',
                                           domain="[('supplier', '=', True)]"),
                'sort_based_on': fields.selection([('date', 'Date'), ('cust', 'Customer'),
                                                   ('job', 'Job No')],
                                                  'Sort Based On')
                }
    _defaults = {
                 'sort_based_on': 'date'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        if data['type'] == 'upcoming':
            report_name = 'upcoming.delivery.jasper'
        else:
            report_name = 'delivery.done.jasper'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
                'nodestroy': True,
                }
    
upcoming_delivery_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

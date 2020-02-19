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

class rejection_report(osv.osv_memory):
    _name = 'rejection.report'
    _description = 'Rejection Report'
    _columns = {
                'rejection_id': fields.many2one('rejection.model', 'Rejection'),
                'from_date': fields.date('From Date'),
                'to_date': fields.date('To Date'),
                'type': fields.selection([('reject', 'Rejection Report'),
                                          ('resupply', 'Rejection Re-delivered Report')],
                                         'Report Type')
                }
    _defaults = {
                 'type': 'reject'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        if data['type'] == 'reject':
            report_name = 'rejection.report.jasper'
        else:
            report_name = 'rejection.redel.report.jasper'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
                'nodestroy': True,
                }
    
rejection_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

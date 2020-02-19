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

class tr_status_report_wizard(osv.osv_memory):
    _name = 'tr.status.report.wizard'
    _description = 'TR Status Report'
    _columns = {
                'from_date': fields.date('Date From', required=True),
                'to_date': fields.date('Date To', required=True),
                'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'Excel')],
                                                "Report Type"),
                'tr_model_id' : fields.many2one('tr.model', 'TR', required=True)
                }
    _defaults = {
                 'from_date': lambda*a:time.strftime("%Y-01-01"),
                 'to_date': lambda*a:time.strftime("%Y-%m-%d"),
                 'report_type': 'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        if data['report_type'] == 'pdf':
            report_name = 'tr.status.report.jasper'
        else:
            report_name = 'tr.status.report.xls.jasper'
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': datas,
                'nodestroy': True,
                'report_type': data['report_type']
                }


tr_status_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

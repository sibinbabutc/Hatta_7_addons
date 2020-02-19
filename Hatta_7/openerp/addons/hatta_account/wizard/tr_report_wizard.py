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

class tr_report_wizard(osv.osv_memory):
    _name = 'tr.report.wizard'
    _description = 'TR Report'
    _columns = {
                'from_date': fields.date('Closing Date From'),
                'to_date': fields.date('Closing Date To'),
                'type': fields.selection([('open', 'Open'), ('settle', 'Settle'),
                                          ('open_settle', 'Open and Settled'),
                                          ('cancel', 'Cancelled')], 'State'),
                'tr_model_id' : fields.many2one('tr.model', 'TR'),
                'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'EXCEL')], 'Format'),
                }
    _defaults = {
                 'type': 'open',
                 'report_type': 'pdf'
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
                'report_name': 'tr.report.jasper',
                'datas': datas,
                'nodestroy': True,
                'report_type': report_type,
                }
    
tr_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

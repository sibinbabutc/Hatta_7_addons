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

class wizard_upcoming_receivable(osv.osv_memory):
    _name = 'wizard.upcoming.receivable'
    _description = 'Wizard for Upcoming Receivable Report'
    
    _columns ={
        'from_date' : fields.date('Date From'),
        'to_date' : fields.date('Date To'),
        'party_id' : fields.many2one('res.partner', 'Party'),
        'due_date_from' : fields.date('Due Date From'),
        'due_date_to' : fields.date('Due Date To'),
        'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'Excel')],
                                                "Report Type"),
               }
    
    _defaults = {
                 'report_type': 'pdf'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'upcoming_receivable_report.jasper',
                'datas': datas,
                'report_type': data['report_type'],
                'nodestroy': True,
                }

wizard_upcoming_receivable()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
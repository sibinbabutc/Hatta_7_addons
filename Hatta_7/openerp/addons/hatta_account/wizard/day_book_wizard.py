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

class day_book_wizard(osv.osv_memory):
    _name = 'day.book.wizard'
    _description = 'Day Book Printing Wizard'
    
    def _get_from_date(self, cr, uid, context=None):
        date_year = time.strftime('%Y')
        return date_year + '-01-01'
    
    _columns = {
                'journal_id': fields.many2one('account.journal', 'Voucher'),
                'from_date': fields.date('Date From'),
                'to_date': fields.date('Date To'),
                'sort_based_on': fields.selection([('date', 'Date'), ('seq', 'Sequence')], 'Sort Based On'),
                'print_opt': fields.selection([('all', 'All'), ('posted', 'Posted'), ('cancel', 'Unposted')],
                                              "Print Only"),
                'report_type': fields.selection([('pdf', 'PDF'), ('xls', 'EXCEL')], 'Format'),
                }
    
    _defaults = {
                 'from_date': _get_from_date,
                 'to_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'print_opt': 'all',
                 'sort_based_on': 'date',
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
                'report_name': 'day.book.jasper',
                'datas': datas,
                'nodestroy': True,
                'report_type': report_type,
                }
    
day_book_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

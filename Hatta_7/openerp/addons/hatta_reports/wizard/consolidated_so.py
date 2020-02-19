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

class wizard_consolidated_so(osv.osv_memory):
    _name = 'wizard.consolidated.so'
    _description = 'Consolidated Sale Order Report Wizard'

    _columns = {
        'from_date' : fields.date('Date From', required=True),
        'to_date' : fields.date('Date To', required=True),
        'customer_id' : fields.many2one('res.partner', string="Customer")
                }
    
    def print_report(self, cr, uid, ids, context=None):
        data = {}
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        datas = {
            'title': 'Consolidated Sale Order Report',
            'from_date':data.from_date,
            'to_date':data.to_date,
            'customer_id' : data.customer_id.name
                }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consolidated_sale_order_jasper',
            'datas': datas,
            'nodestroy' : True,
            'report_type': 'pdf'
            }

wizard_consolidated_so()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
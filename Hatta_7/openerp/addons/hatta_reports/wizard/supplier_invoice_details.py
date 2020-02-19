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
from datetime import date
from calendar import monthrange

class wizard_supplier_invoice(osv.osv_memory):
    _name = 'wizard.supplier.invoice'
    _description = 'Shipping Insurance Report Wizard'
    
    def _get_from_date(self, cr, uid, context=None):
        from_date = date(date.today().year, date.today().month, 1).strftime('%Y-%m-%d')
        return from_date
        
    def _get_to_date(self, cr, uid, context=None):
        to_day = monthrange(date.today().year,date.today().month)[1]
        to_date = date(date.today().year, date.today().month, to_day).strftime('%Y-%m-%d')
        return to_date
    
    _columns = {
        'from_date' : fields.date('Date From', required=True),
        'to_date' : fields.date('Date To', required=True),
        'cargo_company_id' : fields.many2one('cargo.company', string="Cargo Company", required=True)
                }
    
    _defaults = {
        'from_date' : _get_from_date,
        'to_date' : _get_to_date
                 }

    def print_report(self, cr, uid, ids, context=None):
        data = {}
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        datas = {
            'title': 'Shipping Insurance Report',
            'from_date':data.from_date,
            'to_date':data.to_date,
            'cargo_company_id' : data.cargo_company_id.id or False
                }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'supplier_invoice_details_jasper',
            'datas': datas,
            'nodestroy' : True,
            'report_type': 'xls'
            }

wizard_supplier_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
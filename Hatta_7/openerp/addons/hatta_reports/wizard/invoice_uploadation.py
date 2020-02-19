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

class invoice_uploadation_wizard(osv.osv_memory):
    _name = 'invoice.uploadation.wizard'
    _description = 'Invoice Online Upload Status Report Wizard'

    _columns = {
        'from_date' : fields.date('Invoice Date From', required=True),
        'to_date' : fields.date('Invoice Date To', required=True),
        'customer_id' : fields.many2one('res.partner', 'Customer'),
        'report_type' : fields.selection([('uploaded', 'Uploaded'), ('to_upload', 'To Upload')], required=True, string="Report Type")
                }
    _defaults = {
                 'report_type': 'to_upload'
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = {}
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'invoice_uploadation_report_jasper',
            'datas': datas,
            'nodestroy' : True,
            'report_type': 'pdf'
            }





invoice_uploadation_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
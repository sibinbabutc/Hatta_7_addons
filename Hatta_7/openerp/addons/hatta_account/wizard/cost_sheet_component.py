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

class cost_sheet_component(osv.osv_memory):
    _name = 'cost.sheet.component'
    _description = 'Cost Sheet Component Wizard'
    
    _columns = {
        'from_date': fields.date('Date From'),
        'to_date' : fields.date('Date To'),
        'component': fields.selection([('communication', 'Communication Charges'),
                        ('bank', 'Bank Charges'),
                        ('freight', 'Freight Charge'),
                        ('fob', 'FOB Charge'),
                        ('other', 'Other Charges'),
                        ('bank_int', 'Bank Interest'),
                        ('insu', 'Insurance Charges'),
                        ('custom_duty', 'Custom Duty'),
                        ('clearing', 'Clearing Agent Charges'),
                        ('port_clearance', 'Clearance Charge At Port'),
                        ('trans_del', 'Transportation and Clearance Charge'),
                        ('misc', 'Misc Expenses')], "Component", required=True),
        'exclude_zero': fields.boolean('Exclude Zero ?'),
        'tran_type_id': fields.many2one('transaction.type', 'Transaction Type',
                                        domain="[('model_id.model', '=', 'purchase.order')]")
                }
    
    def print_report(self, cr, uid, ids, context=None):
        data = {}
        result =[]
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, [], context=context)[0]
        datas = {'form': data}
#         datas = {
#             'title': 'Cost Sheet Component',
#             'from_date':data.from_date,
#             'to_date':data.to_date,
#             'component':data.component,
#                 }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'cost_sheet_component_jasper',
            'datas': datas,
            'nodestroy' : True,
            'report_type': 'pdf'
            }
    
    _defaults = {
        'component': 'communication',
    }
    
cost_sheet_component()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
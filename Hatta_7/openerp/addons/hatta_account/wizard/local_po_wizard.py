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

class local_po_report(osv.osv_memory):
    _name = 'local.po.report'
    _description = 'LPO Report'
    
    _columns ={
        'from_date' : fields.date('Date From'),
        'to_date' : fields.date('Date To'),
        'lpo_id' : fields.many2one('purchase.order', string="LPO")    
               }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'local_po_report.jasper',
                'datas': datas,
                'nodestroy': True,
                }

local_po_report()

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
     
    def name_get(self, cr, uid, ids, context = None):
        res = []
        if not ids:
            return []
        if context is None:
            context = {}
        if context.get('lpo'):
            reads = self.read(cr, uid, ids, ['name', 'lpo_no'], context=context)
            for record in reads:
                name = record['name']
                if record['lpo_no']:
                    name = name + ' [' + record['lpo_no'] + ']'
                res.append((record['id'], name))
        else:
            res = super(purchase_order, self).name_get(cr, uid, ids, context=context)
        return res

        
purchase_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

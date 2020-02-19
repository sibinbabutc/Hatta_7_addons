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

from tools.translate import _

class purchase_type_selection(osv.osv_memory):
    _name = 'purchase.type.selection'
    _description = 'Purchase type selection'
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type')
                }
    
    def open_record(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_model = self.pool.get('ir.model.data')
        transaction_type_pool = self.pool.get('transaction.type')
        data = self.read(cr, uid, ids, context=context)[0]
        transaction_type_id = data['transaction_type_id'][0]
        transaction_type_obj = transaction_type_pool.browse(cr, uid, transaction_type_id, context=context)
        dummy, view_id = obj_model.get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
        
#         model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),
#                                                   ('name','=','purchase.purchase_order_form')])
# #         print model_data_ids,"------------->>>>>>>>>>>>"
#         resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        ctx = context.copy()
        ctx.update({
                    'default_direct_purchase': True,
                    'default_display_del_address': False,
                    'default_transaction_type_id': transaction_type_id,
                    'default_analytic_account_id': transaction_type_obj and \
                                                        transaction_type_obj.cost_center_id and \
                                                        transaction_type_obj.cost_center_id.id or False,
                    'default_po_notes': ''
                    })
        result = {
                  'name': _('Purchase Order'),
                  'view_type': 'form',
                  'view_mode': 'form',
                  'view_id': view_id,
                  'res_model': 'purchase.order',
                  'type': 'ir.actions.act_window',
                  'nodestroy': True,
                  'target': 'current',
                  'context': ctx
                  }
        return result
    
purchase_type_selection()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class find_supplier(osv.osv_memory):
    _name = 'find.supplier'
    _description = 'Find Supplier'
    _columns = {
                'man_ids': fields.many2many('res.partner', 'manufacturer_wizard_rel', 'wizard_id',
                                            'man_id', 'Manufacturer(s)')
                }
    
    def display_supplier(self, cr, uid, ids, context=None):
        partner_pool = self.pool.get('res.partner')
        purchase_pool = self.pool.get('purchase.order')
        purchase_line_pool = self.pool.get('purchase.order.line')
        data = self.read(cr, uid, ids, context={})[0]
        man_ids = data['man_ids']
        partner_ids = partner_pool.search(cr, uid, [('manufacturer_ids', 'in', man_ids)], context=context)
        purchase_line_ids = purchase_line_pool.search(cr, uid, [('manufacturer_id', 'in', man_ids)],
                                                      context=context)
        for purchase_line_obj in purchase_line_pool.browse(cr, uid, purchase_line_ids, context=context):
            if purchase_line_obj.order_id:
                partner_ids.append(purchase_line_obj.order_id.partner_id.id)
        purchase_ids = purchase_pool.search(cr, uid, [('manufacturer', 'in', man_ids)],
                                            context=context)
        for pur_obj in purchase_pool.browse(cr, uid, purchase_ids, context=context):
            partner_ids.append(pur_obj.partner_id.id)
        partner_ids = list(set(partner_ids))
        return {
                'name': _('Supplying Supplier(s)'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'res.partner',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', partner_ids)],
                'context': {'default_supplier': True, 'default_customer': False}
                }
    
find_supplier()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

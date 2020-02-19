# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 ZestyBeanz Technologies Pvt. Ltd.
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

class option_create(osv.osv_memory):
    _name = 'option.create'
    _description = 'Option Creation'
    
    def default_get(self, cr, uid, field_names, context=None):
        if context is None:
            context = {}
        purchase_pool = self.pool.get('purchase.order')
        res = super(option_create, self).default_get(cr, uid, field_names, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            po_obj = purchase_pool.browse(cr, uid, active_id, context=context)
            vals = {
                    'po_id': active_id,
                    'partner_id': po_obj.partner_id and po_obj.partner_id.id or False
                    }
            lines = []
            for line in po_obj.order_line:
                line_vals = {
                             'si_no': line.sequence_no or '',
                             'product_id': line.product_id and line.product_id.id or False,
                             'option_count': 1,
                             'pol_id': line.id
                             }
                lines.append((0, 0, line_vals))
            vals['line_ids'] = lines
            res.update(vals)
        return res
    
    _columns = {
                'po_id': fields.many2one('purchase.order', 'Purchase Order'),
                'partner_id': fields.many2one('res.partner', 'Supplier'),
                'line_ids': fields.one2many('option.create.line', 'wizard_id', 'Lines')
                }
    
    def create_option(self, cr, uid, ids, context=None):
        purchase_pool = self.pool.get('purchase.order')
        purchase_line_pool = self.pool.get('purchase.order.line')
        line_pool = self.pool.get('option.create.line')
        data = self.read(cr, uid, ids, context={})[0]
        purchase_id_data = data.get('po_id', False)
        purchase_id = purchase_id_data and purchase_id_data[0] or False
        purchase_obj = purchase_pool.browse(cr, uid, purchase_id, context=context)
        line_ids = data.get('line_ids', [])
        pol_line_data = {}
        for line_obj in line_pool.browse(cr, uid, line_ids, context=context):
            pol_obj = line_obj.pol_id or False
            if pol_obj and line_obj.option_count > 0:
                pol_line_data[pol_obj] = line_obj.option_count
        if pol_line_data:
            purchase_pool.write(cr, uid, purchase_id, {'has_options': True}, context=context)
        while pol_line_data:
            new_pol_line_data = {}
            new_po_id = purchase_pool.copy(cr, uid, purchase_id, {'order_line': [],
                                                                  'parent_po_id': purchase_id,
                                                                  'cost_distributed': False,
                                                                  'sale_calculated': False,
                                                                  'has_options': False,
                                                                  },
                                            context=context)
            purchase_pool.write(cr, uid, new_po_id, {'partner_ref': purchase_obj.partner_ref},
                                context=context)
            for line in pol_line_data:
                count = pol_line_data[line]
                if count > 0:
                    new_pol_id = purchase_line_pool.copy(cr, uid, line.id, {'order_id': new_po_id,
                                                                            'parent_pol_id': line.id},
                                                         context=context)
                    count -= 1
                    if count > 0:
                        new_pol_line_data[line] = count
            pol_line_data = new_pol_line_data
        return True
    
option_create()

class option_create_line(osv.osv_memory):
    _name = 'option.create.line'
    _description = 'Option Lines'
    _columns = {
                'si_no': fields.char('SI No.', size=64),
                'product_id': fields.many2one('product.product', 'Product'),
                'option_count': fields.integer('Option Count'),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Line'),
                'wizard_id': fields.many2one('option.create', 'Wizard Ref.')
                }
    _defaults = {
                 'option_count': 1
                 }
option_create_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

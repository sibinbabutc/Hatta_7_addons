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

import openerp.addons.decimal_precision as dp
from tools.translate import _

class create_re_delivery(osv.osv_memory):
    _name = 'create.re.delivery'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        rej_pool = self.pool.get('rejection.model')
        res = super(create_re_delivery, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            rej_obj = rej_pool.browse(cr, uid, active_id, context=context)
            res['picking_id'] = rej_obj.picking_id and rej_obj.picking_id.id or False
            res['reject_id'] = active_id
            lines = []
            for line in rej_obj.line_ids:
                if line.rem_qty_resupply > 0.00:
                    vals = {
                            'product_id': line.product_id and line.product_id.id or False,
                            'lot_id': line.lot_id and line.lot_id.id or False,
                            'qty': line.rem_qty_resupply or 0.00,
                            'uom_id': line.uom_id and line.uom_id.id or False,
                            'move_id': line.move_id and line.move_id.id or False,
                            'rej_line_id': line.id or False
                            }
                    lines.append((0, 0, vals))
            res['line_ids'] = lines
            if not lines:
                raise osv.except_osv(_("Error!!!"),
                                     _("New Picking for all lines are already created !!!!"))
        return res
    
    _columns = {
                'picking_id': fields.many2one('stock.picking', 'Related Picking'),
                'reject_id': fields.many2one('rejection.model', 'Related Rejections'),
                'line_ids': fields.one2many('re.delivery.line', 'wizard_id',
                                            'Line(s)')
                }
    
    def create_picking(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context=context)[0]
        parent_picking_id = data['picking_id'][0]
        line_ids = data['line_ids']
        reject_id = data['reject_id'][0]
        picking_pool = self.pool.get('stock.picking')
        line_pool = self.pool.get('re.delivery.line')
        move_pool = self.pool.get('stock.move')
        reject_pool = self.pool.get('rejection.model')
        reject_line_pool = self.pool.get('rejection.line')
        if not line_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("No Lines selected to create new picking !!!!"))
        if reject_id and line_ids:
            picking_obj = picking_pool.browse(cr, uid, parent_picking_id,
                                              context=context)
            rej_parent_picking_id = picking_obj.rej_parent_picking_id and \
                                        picking_obj.rej_parent_picking_id.id or \
                                        picking_obj.id
            new_picking_id = picking_pool.copy(cr, uid, parent_picking_id,
                                               {'state': 'draft', 'move_lines': [],
                                                'reject_ids': [],
                                                'rej_parent_picking_id': rej_parent_picking_id})
            if picking_obj.sale_id:
                picking_pool.write(cr, uid, new_picking_id,
                                   {'origin': picking_obj.sale_id.name or ''})
            for line in line_pool.browse(cr, uid, line_ids, context=context):
                if line.qty <= 0.00:
                    raise osv.except_osv(_("Error !!!"),
                                         _("Line with Qty as 0.00 not allowed !!!"))
                def_vals = {
                            'state': 'draft',
                            'prodlot_id': line.lot_id and line.lot_id.id or False,
                            'product_qty': line.qty or 1.00,
                            'product_uom': line.uom_id and line.uom_id.id or False,
                            'picking_id': new_picking_id
                            }
                new_move_id = move_pool.copy(cr, uid, line.move_id.id, def_vals,
                                             context=context)
                line.rej_line_id.write({'return_move_ids': [(4, new_move_id)]})
            picking_pool.draft_force_assign(cr, uid, [new_picking_id])
            picking_pool.force_assign(cr, uid, [new_picking_id])
            reject_pool.write(cr, uid, reject_id, {'repicking_ids': [(4, new_picking_id)]},
                              context=context)
            reject_pool.check_rejection(cr, uid, [reject_id], context=context)
        return True
    
create_re_delivery()

class re_delivery_line(osv.osv_memory):
    _name = 're.delivery.line'
    _columns = {
                'product_id': fields.many2one('product.product', 'Product'),
                'lot_id': fields.many2one('stock.production.lot', 'Product Lot'),
                'qty': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure')),
                'uom_id': fields.many2one('product.uom', 'UOM'),
                'move_id': fields.many2one('stock.move', 'Related Move'),
                'wizard_id': fields.many2one('create.re.delivery', 'Wizard Ref.'),
                'rej_line_id': fields.many2one('rejection.line', 'Rejection Line Ref #')
                }
re_delivery_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

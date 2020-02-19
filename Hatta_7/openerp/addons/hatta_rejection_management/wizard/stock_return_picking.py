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
from openerp import netsvc
import time

class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'
    
    def view_init(self, cr, uid, fields_list, context=None):
        """
         Creates view dynamically and adding fields at runtime.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view with new columns.
        """
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        if record_id:
            pick_obj = self.pool.get('stock.picking')
            pick = pick_obj.browse(cr, uid, record_id, context=context)
            if pick.state not in ['done','confirmed','assigned']:
                raise osv.except_osv(_('Warning!'), _("You may only return pickings that are Confirmed, Available or Done!"))
            valid_lines = 0
            return_history = self.get_return_history(cr, uid, record_id, context)
            for m  in pick.move_lines:
                if m.state == 'done' and m.product_qty * m.product_uom.factor > return_history.get(m.id, 0):
                    valid_lines += 1
            if not valid_lines:
                raise osv.except_osv(_('Warning!'), _("Products already Rejected !!!"))
        res = super(stock_return_picking, self).view_init(cr, uid, fields_list, context=context)
        return res
    
    _columns = {
                'note': fields.text('Notes'),
                'date': fields.date('Return Date')
                }
    _defaults = {
                 'date': lambda *a: time.strftime('%Y-%m-%d')
                 }
    
    def default_get(self, cr, uid, fields, context=None):
        rejection_line_pool = self.pool.get('rejection.line')
        move_pool = self.pool.get('stock.move')
        uom_pool = self.pool.get('product.uom')
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        print res
        product_returm_moves = res.get('product_return_moves', [])
        new_line = []
        for line in product_returm_moves:
            move_id = line.get('move_id', False)
            if move_id:
                move_obj = move_pool.browse(cr, uid, move_id, context=context)
                move_uom_id = move_obj.product_uom.id or False
                move_qty = move_obj.product_qty or 0.00
                rejection_line_ids = rejection_line_pool.search(cr, uid, [('move_id', '=', move_id),
                                                                          ('rej_id.state', '!=', 'cancel')])
                done_qty = 0.00
                for rejection_line_obj in rejection_line_pool.browse(cr, uid, rejection_line_ids,
                                                                     context=context):
                    line_uom_id = rejection_line_obj.uom_id and rejection_line_obj.uom_id.id or False
                    qty = rejection_line_obj.qty or 0.00
                    if move_uom_id != line_uom_id:
                        qty = uom_pool._compute_qty(cr, uid, line_uom_id, qty, move_uom_id)
                    done_qty += qty
                net_qty = move_qty - done_qty
                if net_qty > 0.00:
                    line.update({'quantity': net_qty})
                    new_line.append(line)
            if not new_line:
                raise osv.except_osv(_("Error!!!"),
                                     _("All lines are already returned !!!"))
        res['product_return_moves'] = new_line
        return res
    
    def create_rejection(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        active_model = context.get('active_model', '')
        picking_id = False
        if active_model in ['stock.picking.out', 'stock.picking.in']:
            picking_id = context.get('active_id', False)
        line_pool = self.pool.get('stock.return.picking.memory')
        rejection_line_pool = self.pool.get('rejection.line')
        rejection_pool = self.pool.get('rejection.model')
        uom_pool = self.pool.get('product.uom')
        picking_pool = self.pool.get('stock.picking')
        purchase_pool = self.pool.get('purchase.order')
        purchase_line_pool = self.pool.get('purchase.order.line')
        partial_picking_pool = self.pool.get('stock.partial.picking')
        data = self.read(cr, uid, ids, context=context)[0]
        line_ids = data.get('product_return_moves', [])
        lines = []
        purchase_line_ids = []
        ret_product_ids = []
        new_picking_datas = self.create_returns(cr, uid, ids, context=context)
        domain = eval(new_picking_datas.get('domain', []))
        new_ret_pick_ids = domain[0][2]
        picking_pool.write(cr, uid, new_ret_pick_ids, {'date': data['date'], 'min_date': data['date'],
                                                       'date_done': data['date'],
                                                       'rej_parent_picking_id': False}, context=context)
        wf_service = netsvc.LocalService('workflow')
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            if not line.move_id:
                raise osv.except_osv(_("Error!!!"),
                                     _("Invalid product in selection !!!"))
            move_qty = line.move_id.product_qty or 0.00
            move_uom_id = line.move_id and line.move_id.product_uom.id or False
            exist_qty = 0.00
            rej_line_ids = rejection_line_pool.search(cr, uid, [('move_id', '=', line.move_id.id),
                                                                ('rej_id.state', '!=', 'cancel')],
                                                      context=context)
            for rej_line_obj in rejection_line_pool.browse(cr, uid, rej_line_ids, context=context):
                qty = rej_line_obj.qty
                rej_line_uom_id = rej_line_obj.uom_id and rej_line_obj.uom_id.id or False
                if rej_line_uom_id != move_uom_id:
                    qty = uom_pool._compute_qty(cr, uid, rej_line_uom_id, qty, move_uom_id)
                exist_qty += qty
            if exist_qty + line.quantity > move_qty:
                raise osv.except_osv(_("Error!!!"),
                                     _("Invalid Quantity !!!"))
            if line.move_id and line.move_id.purchase_line_id:
                purchase_line_ids.append(line.move_id.purchase_line_id.id)
            vals = {
                    'product_id': line.product_id.id,
                    'lot_id': line.prodlot_id and line.prodlot_id.id or False,
                    'qty': line.quantity or 0.00,
                    'uom_id': move_uom_id,
                    'move_id': line.move_id and line.move_id.id or False
                    
                    }
            lines.append((0, 0, vals))
            ret_product_ids.append(line.product_id.id)
        if picking_id:
            picking_obj = picking_pool.browse(cr, uid, picking_id, context=context)
            partner_obj = picking_obj.partner_id
            invoice_ids = []
            if picking_obj.sale_id:
                invoice_ids = [x.id for x in picking_obj.sale_id.invoice_ids]
                sale_obj = picking_obj.sale_id
                domain = [('state', 'not in', ['draft', 'bid', 'sent', 'cancel'])]
                if sale_obj.lead_id:
                    domain.append(('lead_id', '=', sale_obj.lead_id.id))
                else:
                    domain.append(('direct_sale_id', '=', sale_obj.id))
                purchase_ids = purchase_pool.search(cr, uid, domain, context=context)
                if purchase_ids and ret_product_ids:
                    all_pur_line_ids = purchase_line_pool.search(cr, uid, [('order_id', 'in', purchase_ids),
                                                                           ('product_id', 'in', ret_product_ids)],
                                                                 context=context)
                    purchase_line_ids.extend(all_pur_line_ids)
            purchase_line_ids = list(set(purchase_line_ids))
            rejection_vals = {
                              'picking_id': picking_id,
                              'partner_id': partner_obj.id,
                              'parent_partner_id': partner_obj.parent_id and partner_obj.parent_id.id or \
                                                        partner_obj.id,
                              'line_ids': lines,
                              'sale_id': picking_obj.sale_id and picking_obj.sale_id.id or False,
                              'job_id': picking_obj.job_id and \
                                            picking_obj.job_id.id or False,
                              'invoice_ids': [(6, 0, invoice_ids)],
                              'picking_type': picking_obj.type == 'out' and 'out' or 'in',
                              'purchase_line_ids': [(6, 0, purchase_line_ids)],
                              'delivery_return_id': new_ret_pick_ids[0],
                              'note': data.get('note', ''),
                              'date': data['date']
                              }
            rejection_id = rejection_pool.create(cr, uid, rejection_vals, context=context)
            wf_service.trg_validate(uid, 'rejection.model', \
                                    rejection_id, 'confirm', cr)
            if new_ret_pick_ids:
                ctx = context.copy()
                ctx['active_model'] = picking_obj.type == 'out' and 'stock.picking.in' or \
                                            'stock.picking.out'
                ctx['active_ids'] = new_ret_pick_ids
                partial_picking_def = partial_picking_pool.default_get(cr, uid, ['picking_id',
                                                                                 'move_ids',
                                                                                 'date'],
                                                                       context=ctx)
                move_line_data = []
                for line_data in partial_picking_def.get('move_ids', []):
                    move_line_data.append((0, 0, line_data))
                partial_picking_def['move_ids'] = move_line_data
                partial_picking_id = partial_picking_pool.create(cr, uid, partial_picking_def,
                                                                 context=ctx)
                partial_picking_pool.do_partial(cr, uid, [partial_picking_id], context=context)
            return {
                    'name': _('Related Rejection'),
                    'view_mode':'form',
                    'res_model': 'rejection.model',
                    'res_id': rejection_id,
                    'type':'ir.actions.act_window',
                    'context':context,
                    }
        return True

stock_return_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

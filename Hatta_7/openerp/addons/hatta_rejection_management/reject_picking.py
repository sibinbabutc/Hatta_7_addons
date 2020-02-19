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
from openerp import netsvc
from tools.translate import _

class rejection_model(osv.osv):
    _name = 'rejection.model'
    _description = 'Rejection Model'
    
    _columns = {
                'picking_id': fields.many2one('stock.picking', 'Picking'),
                'date': fields.date('Date'),
                'partner_id': fields.many2one('res.partner', 'Delivery Address'),
                'parent_partner_id': fields.many2one('res.partner', 'Partner'),
                'picking_type': fields.selection([('out', 'Delivery Order'), ('in', 'Incoming Shipment')],
                                                 'Picking Type'),
                'line_ids': fields.one2many('rejection.line', 'rej_id', 'Rejection Line(s)'),
                'invoice_ids': fields.many2many('account.invoice', 'invoice_rej_rel',
                                                'rej_id', 'invoice_id', 'Related Invoice(s)'),
                'state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Cancelled')],
                                          'State'),
                'purchase_line_ids': fields.many2many('purchase.order.line', 'pol_rej_rel',
                                                     'rej_id', 'pol_id', 'Related Purchase(s)'),
                'delivery_return_id': fields.many2one('stock.picking', 'Related Delivery Return'),
#                 'related_cust_return_picking': fields.many2many('stock.picking', 'ret_picking_rej_rel',
#                                                                 'rej_id', 'picking_id',
#                                                                 'Related Customer Return Picking'),
                'sale_id': fields.many2one('sale.order', 'Related Sale Order'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'note': fields.text('Note'),
                'repicking_ids': fields.many2many('stock.picking', 'picking_ret_rel',
                                                         'ret_id', 'picking_id',
                                                         'Related Re-Picking')
                }
    _rec_name = "delivery_return_id"
    _defaults = {
                 'state': 'draft'
                 }
    
    def unlink(self, cr, uid, ids, context=None):
        for rej in self.browse(cr, uid, ids, context=context):
            if rej.state not in ['draft', 'cancel']:
                raise osv.except_osv(_("Error!!!"),
                                     _("Rejection not in state New/Cancel cannot be deleted !!!"))
        return super(rejection_model, self).unlink(cr, uid, ids, context=context)
    
    def check_rejection(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for rej in self.browse(cr, uid, ids, context=context):
            proceed = True
            for line in rej.line_ids:
                if line.rem_qty_resupply > 0.00:
                    proceed = False
            if proceed:
                wf_service.trg_validate(uid, 'rejection.model', \
                                    rej.id, 'done', cr)
        return True
    
    def view_re_delivery(self, cr, uid, ids, context=None):
        model_list = {
                      'out': 'stock.picking.out',
                      'in': 'stock.picking.in',
                      'internal': 'stock.picking'
                      }
        picking_ids = []
        for ret in self.browse(cr, uid, ids, context=context):
            picking_ids.extend([x.id for x in ret.repicking_ids])
            new_type = ret.picking_id.type
        return {
                'domain': "[('id', 'in', "+str(picking_ids)+")]",
                'name': _('Returned Picking'),
                'view_type':'form',
                'view_mode':'tree,form',
                'res_model': model_list.get(new_type, 'stock.picking'),
                'type':'ir.actions.act_window',
                'context':context,
                }
    
    def action_cancel(self, cr, uid, ids, context=None):
        for rej in self.browse(cr, uid, ids, context=context):
            if rej.delivery_return_id.state != 'cancel':
                raise osv.except_osv(_("Error!!!"),
                                     _("Please Cancel all related delivery returns !!!"))
            for re_del in rej.repicking_ids:
                if re_del.state != 'cancel':
                    raise osv.except_osv(_("Error!!!"),
                                         _("Please Cancel all related re-deliveries !!!"))
        return self.write(cr, uid, ids, {'state':'cancel'}, context=context)
    
rejection_model()

class rejection_line(osv.osv):
    _name = 'rejection.line'
    _description = 'Rejection Line'
    
    def _get_rem_resupply(self, cr, uid, ids, fields, args, context=None):
        res = {}
        uom_pool = self.pool.get('product.uom')
        for line in self.browse(cr, uid, ids, context=context):
            line_qty = line.qty or 0.00
            for return_move_id in line.return_move_ids:
                ret_uom_id = return_move_id.product_uom.id
                line_uom_id = line.uom_id.id
                ret_qty = return_move_id.product_qty
                if ret_uom_id != line_uom_id:
                    ret_qty = uom_pool._compute_qty(cr, uid, ret_uom_id, ret_qty,
                                                    line_uom_id)
                line_qty -= ret_qty
            res[line.id] = line_qty
        return res
    
    _columns = {
                'product_id': fields.many2one('product.product', 'Product'),
                'lot_id': fields.many2one('stock.production.lot', 'Product Lot'),
                'qty': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure')),
                'uom_id': fields.many2one('product.uom', 'UOM'),
                'move_id': fields.many2one('stock.move', 'Related Move'),
                'rej_id': fields.many2one('rejection.model', 'Rejection Ref.'),
                'return_move_ids': fields.many2many('stock.move', 'rej_line_move_rel',
                                                    'line_id', 'move_id', 'Return Moves'),
                'rem_qty_resupply': fields.function(_get_rem_resupply, type="float",
                                                    digits_compute= dp.get_precision('Product Unit of Measure'),
                                                    string="Remaining Qty")
                }
rejection_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

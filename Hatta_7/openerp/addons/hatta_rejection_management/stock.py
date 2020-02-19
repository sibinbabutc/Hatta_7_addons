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

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
                'rej_parent_picking_id': fields.many2one('stock.picking',
                                                         'Rejection Parent Picking'),
                'reject_ids': fields.one2many('rejection.model', 'picking_id',
                                              'Related Rejections')
                }
    _defaults = {
                 'rej_parent_picking_id': False
                 }
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
                'rej_parent_picking_id': fields.many2one('stock.picking',
                                                         'Rejection Parent Picking'),
                'reject_ids': fields.one2many('rejection.model', 'picking_id',
                                              'Related Rejections')
                }
    _defaults = {
                 'rej_parent_picking_id': False
                 }
    
    def view_rejects(self, cr, uid, ids, context=None):
        rej_ids = []
        for picking in self.browse(cr, uid, ids, context=context):
            rej_ids.extend([x.id for x in picking.reject_ids])
        if not rej_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("No Rejections Found !!!!"))
        return {
                'domain': "[('id', 'in', "+str(rej_ids)+")]",
                'name': _('Rejection Management'),
                'view_type':'form',
                'view_mode':'tree,form',
                'res_model': 'rejection.model',
                'type':'ir.actions.act_window',
                'context':context,
                }
        
    def view_re_delivery(self, cr, uid, ids, context=None):
        model_list = {
                      'out': 'stock.picking.out',
                      'in': 'stock.picking.in',
                      'internal': 'stock.picking'
                      }
        picking_ids = []
        for picking in self.browse(cr, uid, ids, context=context):
            new_type = picking.type
            for ret in picking.reject_ids:
                picking_ids.extend([x.id for x in ret.repicking_ids])
        if not picking_ids:
            raise osv.except_osv(_("Error!!!"),
                                 _("No Related re-delivery found!!!"))
        return {
                'domain': "[('id', 'in', "+str(picking_ids)+")]",
                'name': _('Returned Picking'),
                'view_type':'form',
                'view_mode':'tree,form',
                'res_model': model_list.get(new_type, 'stock.picking'),
                'type':'ir.actions.act_window',
                'context':context,
                }
    
stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

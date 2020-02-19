# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

class exchange_rate_change(osv.osv_memory):
    _inherit = 'exchange.rate.change'
    
    def change_cost(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_pool = self.pool.get('purchase.order.line')
        purchase_pool = self.pool.get('purchase.order')
        res = super(exchange_rate_change, self).change_cost(cr, uid, ids, context=context)
        active_ids = context.get('active_ids', [])
        if context.get('active_model', '') == 'purchase.order':
            temp_active_id = []
            for purchase_obj in purchase_pool.browse(cr, uid, active_ids, context=context):
                exchange_rate = purchase_obj.exchange_rate or 1.0000
                for cost_line in purchase_obj.charge_ids:
                    amount_fc = cost_line.amount_fc or 0.00
                    amount_lc = amount_fc * exchange_rate
                    cost_line.write({'amount_lc': amount_lc})
                for line in purchase_obj.order_line:
                    temp_active_id.append(line.id)
                    for cost_line in line.charge_ids:
                        amount_fc = cost_line.amount_fc or 0.00
                        amount_lc = amount_fc * exchange_rate
                        cost_line.write({'amount_lc': amount_lc})
            for po_obj in purchase_pool.browse(cr, uid, active_ids, context=context):
                if po_obj.cost_distributed:
                    line_pool.distribute_cost(cr, uid, temp_active_id, context=context)
        return res
    
exchange_rate_change()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

import openerp.addons.decimal_precision as dp

class exchange_rate_change(osv.osv_memory):
    _name = 'exchange.rate.change'
    _description = 'Exchange Rate Change'
    
    def default_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(exchange_rate_change, self).default_get(cr, uid, ids, context=context)
        if context.get('active_id', False) and \
                    context.get('active_model', '') in ['purchase.order', 'purchase.order.line']:
            model_pool = self.pool.get(context['active_model'])
            order_id = context.get('active_id', False)
            order_obj = model_pool.browse(cr, uid, order_id, context=context)
            res['exchange_rate'] = order_obj.exchange_rate or 0.00
        return res
    
    _columns = {
                'exchange_rate': fields.float('Exchange Rate',
                                              digits=(16, 5))
                }
    
    def change_cost(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context={})[0]
        if context.get('active_ids', False) and \
                    context.get('active_model', '') in ['purchase.order', 'purchase.order.line']:
            order_pool = self.pool.get(context['active_model'])
            order_ids = context['active_ids']
            order_pool.exchange_rate_change(cr, uid, order_ids, data.get('exchange_rate', 1.00),
                                            context=context)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
exchange_rate_change()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class create_direct_purchase(osv.osv_memory):
    _name = 'create.direct.purhase'
    _description = 'Create Direct Purchase'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(create_direct_purchase, self).default_get(cr, uid, fields, context=context)
        res['sale_id'] = context.get('active_id', False)
        return res
    
    _columns = {
                'sale_id': fields.many2one('sale.order', 'Sale Order'),
                'partner_ids': fields.many2many('res.partner', 'partner_wizard_rel_hatta', 'wizard_id',
                                                'partner_id', 'Supplier(s)')
                }
    
    def create_po(self, cr, uid, ids, context=None):
        sale_pool = self.pool.get('sale.order')
        data = self.read(cr, uid, ids, context=context)[0]
        sale_id = data.get('sale_id', False)
        partner_ids = data.get('partner_ids', [])
        if sale_id and partner_ids:
            res = sale_pool.create_po(cr, uid, [sale_id[0]], partner_ids, context=context)
            return res
        return True
    
create_direct_purchase()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class sale_confirm_wizard(osv.osv):
    _name = 'sale.confirm.wizard'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        sale_pool = self.pool.get('sale.order')
        res = super(sale_confirm_wizard, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            sale_obj = sale_pool.browse(cr, uid, active_id, context=context)
            res['sale_id'] = active_id
            enq_name = sale_obj.lead_id and sale_obj.lead_id.reference or ''
            res['name'] = "<b>All the items and their quantities from the customer enquiry %s is not found in this sale quotation. Do you want to continue with this sale quotation?</b>"%(enq_name)
        return res
    
    _description = 'Sale Confirmation Wizard'
    _columns = {
                'name': fields.text('Warning'),
                'sale_id': fields.many2one('sale.order', 'Sale Order')
                }
    
    def confirm_sale(self, cr, uid, ids, context=None):
        sale_pool = self.pool.get('sale.order')
        data = self.read(cr, uid, ids, context=context)[0]
        sale_id = data.get('sale_id', (False))[0]
        if sale_id:
            sale_pool.action_button_confirm(cr, uid, [sale_id], context=context)
        return True
    
sale_confirm_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

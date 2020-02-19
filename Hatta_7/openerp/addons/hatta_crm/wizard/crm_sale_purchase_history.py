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

class crm_sale_purchase_history(osv.osv_memory):
    _name = 'crm.sale.purchase.history'
    _description = 'CRM Sale Purchase History'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        line_pool = self.pool.get('crm.product.lines')
        res = super(crm_sale_purchase_history, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            line_obj = line_pool.browse(cr, uid, active_id, context=context)
            lead_obj = line_obj.lead_id
            res['product_id'] = line_obj.product_id and line_obj.product_id.id or False
            res['partner_id'] = lead_obj.partner_id and lead_obj.partner_id.id or False
            product_ids = [x.product_id.id for x in lead_obj.product_lines if x.product_id]
            res['product_ids'] = product_ids
        return res
    
    def onchange_product(self, cr, uid, ids, product_id=False, partner_id=False, context=None):
        sale_domain = [('state', 'not in', ['draft', 'cancel'])]
        purchase_domain = [('state', 'not in', ['cancel'])]
        res = {'value': {}}
        sale_line_pool = self.pool.get('sale.order.line')
        purchase_line_pool = self.pool.get('purchase.order.line')
        if product_id:
            sale_domain.append(('product_id', '=', product_id))
            purchase_domain.append(('product_id', '=', product_id))
        if partner_id:
            sale_domain.append(('order_id.partner_id', '=', partner_id))
        sale_line_ids = sale_line_pool.search(cr, uid, sale_domain, context=context)
        purchase_line_ids = purchase_line_pool.search(cr, uid, purchase_domain, context=context)
        res['value']['sale_line_ids'] = [(6, 0, sale_line_ids)]
        res['value']['purchase_line_ids'] = [(6, 0, purchase_line_ids)]
        return res
    
    _columns = {
                'product_id': fields.many2one('product.product', 'Product'),
                'product_ids': fields.many2many('product.product', 'crm_product_wiz_rel',
                                                'wizard_id', 'product_id', 'Product'),
                'partner_id': fields.many2one('res.partner', 'Customer'),
                'sale_line_ids': fields.many2many('sale.order.line', 'crm_sale_line_wizard_rel',
                                                  'wizard_id', 'sale_line_id', 'Sale Order Lines'),
                'purchase_line_ids': fields.many2many('purchase.order.line', 'crm_purchase_line_wizard_rel',
                                                      'wizard_id', 'purchase_line_id',
                                                      'Purchase Lines')
                }
    
crm_sale_purchase_history()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

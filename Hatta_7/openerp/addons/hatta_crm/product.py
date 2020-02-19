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

import re
import openerp.addons.decimal_precision as dp

class product_product(osv.osv):
    _inherit = 'product.product'
    
    def onchange_categ_id(self, cr, uid, ids, categ_id, context=None):
        res = {'value': {}}
        categ_pool = self.pool.get('product.category')
        if categ_id:
            categ_obj = categ_pool.browse(cr, uid, categ_id, context=context)
            res['value']['type'] = categ_obj.product_type
            res['value']['valuation'] = categ_obj.valuation
            res['value']['cost_method'] = categ_obj.cost_method
        return res
    
    def _compute_inventory_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            inventory_value = 0.0
            res[product.id] = {
                'iventory_value': 0.0,
            }
            res[product.id]['iventory_value'] = product.standard_price * product.qty_available
        return res
    
    def _get_product(self, cr, uid, ids, context=None):
        result = {}
        for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if move.state=='done':
                result[move.product_id.id] = True
        return result.keys()
    
    def _get_total_qty(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}
        move_pool = self.pool.get('stock.move')
        internal_locs = self.pool.get('stock.location').search(cr, uid, [('usage','=','internal')],context=context)
        for product in self.browse(cr, uid, ids, context=None):
            res[product.id] = 0.0
            outgoing_move_ids = move_pool.search(cr, uid,[('location_id','in',internal_locs),('product_id','=',product.id),('state','=','done')],context=context)
            outgoing_sum = 0.0
            incoming_sum = 0.0
            if outgoing_move_ids:
                for outgoing_move in move_pool.browse(cr, uid, outgoing_move_ids, context=context):
                    outgoing_sum += outgoing_move.product_qty
            incoming_move_ids = move_pool.search(cr, uid,[('location_dest_id','in',internal_locs),('product_id','=',product.id),('state','=','done')],context=context)
            if incoming_move_ids:
                for incoming_move in move_pool.browse(cr, uid, incoming_move_ids, context=context):
                    incoming_sum += incoming_move.product_qty
            res[product.id] = incoming_sum - outgoing_sum
        return res
    
    _columns = {
                'certificate_ids': fields.many2many('product.certificate', 'product_cert_rel',
                                                    'product_id', 'certificate_id', 'Certificate(s)'),
                'manufacturer_id': fields.many2one('res.partner', 'Manufacturer'),
                'part_no': fields.char('Part Number', size=128),
                'type': fields.selection([('product','Stock Item'),('consu', 'Non Stock Item'),
                                          ('service','Service Charges')], 'Product Type', required=True,
                                         help="Consumable: Will not imply stock management for this product. \nStockable product: Will imply stock management for this product."),
                'multi_price_ids': fields.one2many('product.multiple.prices', 'product_id', 'Multiple Prices'),
                'iventory_value': fields.function(_compute_inventory_value, digits_compute=dp.get_precision('Account'), string='Inventory Value',
                                                multi='value'),
                'qty_on_hand_store': fields.function(_get_total_qty,type='float', string='Quantity On Hand',
                                                       digits_compute=dp.get_precision('Product Unit of Measure'),
                                                       store = {
                        'stock.move': (_get_product, [], 10),
                    })
                }
    _defaults = {
                 'type': 'consu'
                 }
    
    def _check_internal_number(self, cr, uid, ids, context=None):
        for product_obj in self.browse(cr, uid, ids, context=context):
            if product_obj.default_code and product_obj.type != 'product':
                product_ids = self.search(cr, uid, [('default_code', '=', product_obj.default_code),
                                                    ('id', '!=', product_obj.id)],
                                          context=context)
                if product_ids:
                    return False
        return True
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('part_no','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('default_code',operator,name)], limit=limit, context=context))
                ids.update(self.search(cr, user, args + [('part_no',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    _constraints = [
                    (_check_internal_number, 'Product with same internal number already exists', ['default_code']),
                    ]
    
product_product()

class product_uom(osv.osv):
    _inherit = 'product.uom'
    
    def _get_categ(self, cr, uid, *args):
        cr.execute('select id from product_category order by id limit 1')
        res = cr.fetchone()
        return res and res[0] or False
    
    def name_create(self, cr, uid, name, context=None):
        """ The UoM category and factor are required, so we'll have to add temporary values
            for imported UoMs """
        cr.execute('select id from product_category order by id limit 1')
        categ_id = cr.fetchone()
        if categ_id:
            categ_id = categ_id[0]
        else:
            categ_id, _ = uom_categ.name_create(cr, uid, categ_misc)
        uom_id = self.create(cr, uid, {self._rec_name: name,
                                       'category_id': categ_id,
                                       'factor': 1})
        return self.name_get(cr, uid, [uom_id], context=context)[0]
    
    _defaults = {
                 'category_id': _get_categ
                 }
product_uom()

class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
                'product_type': fields.selection([('product','Stock Item'),('consu', 'Non Stock Item'),
                                          ('service','Service Charges')], 'Product Type', required=True,
                                         help="Consumable: Will not imply stock management for this product. \nStockable product: Will imply stock management for this product."),
                'valuation': fields.selection([('manual_periodic', 'Periodical (manual)'),
                                        ('real_time','Real Time (automated)'),], 'Inventory Valuation',
                                        help="If real-time valuation is enabled for a product, the system will automatically write journal entries corresponding to stock moves." \
                                             "The inventory variation account set on the product category will represent the current inventory value, and the stock input and stock output account will hold the counterpart moves for incoming and outgoing products."
                                        , required=True),
                'cost_method': fields.selection([('standard','Standard Price'), ('average','Average Price')], 'Costing Method', required=True,
                                                help="Standard Price: The cost price is manually updated at the end of a specific period (usually every year). \nAverage Price: The cost price is recomputed at each incoming shipment."),
                }
    _defaults = {
                 'type': 'consu',
                 'valuation': 'manual_periodic',
                 'cost_method': 'standard'
                 }
product_category()


class product_multiple_prices(osv.osv):
    _name = 'product.multiple.prices'
    _columns = {
                'product_id': fields.many2one('product.product','Product'),
                'currency_id': fields.many2one('res.currency','Currency'),
                'list_price': fields.float('Price', digits_compute=dp.get_precision('Product Price')),
        }
                
product_multiple_prices()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

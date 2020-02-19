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

from openerp.osv import fields, osv

from openerp import SUPERUSER_ID

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def _has_approve_access(self, cr, uid, ids, name, args, context=None):
        res =  {}
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.amount_untaxed <= user_obj.sale_approve_limit and sale_obj.state == 'wait_for_approval':
                res[sale_obj.id] = True
            else:
                res[sale_obj.id] = False
        return res
    
    _columns = {
                'state': fields.selection([
                                           ('draft', 'Draft Quotation'),
                                           ('sent', 'Quotation Sent'),
                                           ('cancel', 'Cancelled'),
                                           ('wait_for_approval','Waiting For Approval'),
                                           ('waiting_date', 'Waiting Schedule'),
                                           ('progress', 'Sales Order'),
                                           ('manual', 'Sale to Invoice'),
                                           ('shipping_except', 'Shipping Exception'),
                                           ('invoice_except', 'Invoice Exception'),
                                           ('done', 'Done'),
                                           ], 'Status', readonly=True,help="Gives the status of the quotation or sales order.\
                                            \nThe exception status is automatically set when a cancel operation occurs \
                                            in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
                                            but waiting for the scheduler to run on the order date.",
                                            select=True, copy=False),
                'can_approve': fields.function(_has_approve_access, type='boolean', string='Can Approve ?'),
                'name': fields.char('Order Reference', size=64,  copy=False, required=True,
                                    readonly=True, states={'draft': [('readonly', False)],
                                                           'sent': [('readonly', False)],
                                                           'wait_for_approval': [('readonly', False)]}, select=True),
                
                'date_order': fields.datetime('Date', required=True, readonly=True, select=True,
                                          states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)],
                                                  'wait_for_approval': [('readonly', False)]
                                                  }),
                'user_id': fields.many2one('res.users', 'Salesperson', states={'draft': [('readonly', False)],
                                                                               'sent': [('readonly', False)],
                                                                               'wait_for_approval': [('readonly', False)]}, select=True, track_visibility='onchange'),
                'partner_id': fields.many2one('res.partner', 'Customer', readonly=True,
                                              states={'draft': [('readonly', False)],
                                                      'sent': [('readonly', False)],
                                                      'wait_for_approval': [('readonly', False)]}, required=True, change_default=True, select=True, track_visibility='always'),
                'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, required=True,
                                                      states={'draft': [('readonly', False)],
                                                              'sent': [('readonly', False)],
                                                              'wait_for_approval': [('readonly', False)]}, help="Invoice address for current sales order."),
                'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=True, required=True,
                                                       states={'draft': [('readonly', False)],
                                                               'sent': [('readonly', False)],
                                                               'wait_for_approval': [('readonly', False)]}, help="Delivery address for current sales order."),
                'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=True, readonly=True,
                                                states={'draft': [('readonly', False)],
                                                        'sent': [('readonly', False)],
                                                        'wait_for_approval': [('readonly', False)]}, help="Pricelist for current sales order."),
                'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency", readonly=True, required=True),
                'project_id': fields.many2one('account.analytic.account', 'Contract / Analytic', readonly=True,
                                              states={'draft': [('readonly', False)],
                                                      'sent': [('readonly', False)],
                                                      'wait_for_approval': [('readonly', False)]}, help="The analytic account related to a sales order."),
                'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True,
                                              states={'draft': [('readonly', False)],
                                                      'sent': [('readonly', False)],
                                                      'wait_for_approval': [('readonly', False)]}, copy=True),
                'picking_policy': fields.selection([('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
                                                   'Shipping Policy', required=True, readonly=True, states={'draft': [('readonly', False)],
                                                                                                            'sent': [('readonly', False)],
                                                                                                            'wait_for_approval': [('readonly', False)]},
                                                   help="""Pick 'Deliver each product when available' if you allow partial delivery."""),
                'order_policy': fields.selection([
                                                  ('manual', 'On Demand'),
                                                  ('picking', 'On Delivery Order'),
                                                  ('prepaid', 'Before Delivery'),
                                                  ], 'Create Invoice', required=True, readonly=True, states={'draft': [('readonly', False)],
                                                                                                             'sent': [('readonly', False)],
                                                                                                             'wait_for_approval': [('readonly', False)]},
                                                 help="""On demand: A draft invoice can be created from the sales order when needed. \nOn delivery order: A draft invoice can be created from the delivery order when the products have been delivered. \nBefore delivery: A draft invoice is created from the sales order and must be paid before the products can be delivered."""),
                }
    
    def action_portal_confirm(self, cr, uid, ids, context=None):
        return self.action_button_confirm(cr, SUPERUSER_ID, ids, context={})
    
    def check_approval_limit(self, cr, uid, ids, context=None):
        ok = True
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if sale_obj.amount_untaxed > user_obj.sale_approve_limit:
                ok = False
        return ok
    
    def sale_send_for_approval(self, cr, uid, ids, context=None):
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        self.write(cr, uid, ids, {'state': 'wait_for_approval'}, context=context)
        return True
    
    def sale_approved(self, cr, uid, ids, context=None):
        return True
    
sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

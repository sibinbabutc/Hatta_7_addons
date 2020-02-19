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

from tools.translate import _
from openerp import netsvc
import time

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _order = 'min_date'
    
    def _get_real_partner(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            partner_obj = picking.manual_partner_id or picking.partner_id or False
            if partner_obj and partner_obj.parent_id:
                partner_obj = partner_obj.parent_id
            if picking.sale_id:
                partner_obj = picking.sale_id.partner_id
            partner_id = partner_obj and partner_obj.id or False
            res[picking.id] = partner_id
        return res
    
    _columns = {
                'return_par_pick_id': fields.many2one('stock.picking', 'Parent Picking Id'),
                'package': fields.char('Package', size=128),
                'shop_id': fields.many2one('sale.shop', 'Location'),
                'client_order_ref': fields.char('Customer PO Number', size=128),
                'unposted': fields.boolean('Unposted ?'),
                'real_customer_id': fields.function(_get_real_partner, type="many2one",
                                                    relation="res.partner",
                                                    string="Customer", store=True),
                'manual_partner_id': fields.many2one('res.partner', 'Manual Partner',
                                                     domain="[('customer', '=', True)]"),
                'manual_name': fields.char('Manual DN #', size=128),
                'perm_cancel': fields.boolean('Perm Cancel')
                }
    _defaults = {
                 'return_par_pick_id': False
                 }
    
    def set_to_draft(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        move_obj = self.pool.get('stock.move')
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            moves = move_obj.search(cr, uid, [('picking_id', '=', p_id)])
            move_obj.write(cr, uid, moves, {'state': 'draft'})
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'stock.picking', p_id, cr)
            wf_service.trg_create(uid, 'stock.picking', p_id, cr)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _("Picking '%s' has been set in draft state.") % name
            self.log(cr, uid, id, message)
        return True
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        transaction_type_pool = self.pool.get('transaction.type')
        invoice_pool = self.pool.get('account.invoice')
        invoice_line_pool = self.pool.get('account.invoice.line')
        obj_sequence = self.pool.get('ir.sequence')
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id,
                                                               group, type, context=context)
        for picking_obj in self.browse(cr, uid, ids, context=context):
            inv_id = res.get(picking_obj.id, False)
            inv_number = ''
            if picking_obj.sale_id and picking_obj.sale_id.unposted:
                for invoice in picking_obj.sale_id.invoice_ids:
                    if invoice.unposted and invoice.state == 'cancel':
                        inv_number = invoice.internal_number
                        invoice.write({'internal_number': inv_number + " Cancelled - " + str(time.strftime("%d-%m-%Y %H:%M:%S")),
                                       'unposted': False})
                        break;
            if inv_id and picking_obj.type == 'out':
                cost_center_id = picking_obj.cost_center_id and \
                                    picking_obj.cost_center_id.id or False
                if cost_center_id:
                    tran_type_domain = [('model_id.model', '=', 'account.invoice'),
                                        ('cost_center_id', '=', cost_center_id)]
                    if picking_obj.return_par_pick_id:
                        tran_type_domain.append(('refund', '=', True))
                    transaction_type_ids = transaction_type_pool.search(cr, uid, tran_type_domain,
                                                                        context=context)
                    if transaction_type_ids:
                        tran_obj = transaction_type_pool.browse(cr, uid, transaction_type_ids[0], context=context)
                    if tran_obj.sequence_id:
                        if not inv_number:
                            inv_number = obj_sequence.next_by_id(cr, uid,
                                                                 tran_obj.sequence_id.id,
                                                                 context=context)
                        invoice_pool.write(cr, uid, inv_id, {'transaction_type_id': transaction_type_ids[0],
                                                             'cost_center_id': cost_center_id,
                                                             'internal_number': inv_number})
                    else:
                        raise osv.except_osv(_("Error !!!"),
                                             _("Please configure transaction type"))
            if picking_obj.type == 'in' and picking_obj.purchase_id:
                invoice_id = res.get(picking_obj.id, False)
                if invoice_id:
                    for line in picking_obj.purchase_id.order_line:
                        for charge in line.charge_ids:
                            if charge.pay_to_cust:
                                invoice_line_vals = {
                                                     'name': charge.charge_id.name or '',
                                                     'origin': picking_obj.name,
                                                     'invoice_id': invoice_id,
                                                     'account_id': charge.account_id and charge.account_id.id or \
                                                                        False,
                                                     'price_unit': charge.amount_fc or 0.00,
                                                     'quantity': 1.00,
                                                     }
                                invoice_line_pool.create(cr, uid, invoice_line_vals, context=context)
                    for charge in picking_obj.purchase_id.charge_ids:
                        if charge.pay_to_cust:
                            invoice_line_vals = {
                                                 'name': charge.charge_id.name or '',
                                                 'origin': picking_obj.name,
                                                 'invoice_id': invoice_id,
                                                 'account_id': charge.account_id and charge.account_id.id or \
                                                                    False,
                                                 'price_unit': charge.amount_fc or 0.00,
                                                 'quantity': 1.00,
                                                 }
                            invoice_line_pool.create(cr, uid, invoice_line_vals, context=context)
        return res
    
    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
                              invoice_vals, context=None):
        res = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line,
                                                               invoice_id, invoice_vals, context=context)
        res['sequence_no'] = move_line.sequence_no
        return res
    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type,
                                                          journal_id, context=context)
        res['parent_partner_id'] = partner.parent_id and partner.parent_id.id or partner.id
        return res
    
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _order = 'min_date'
    
    def _get_real_partner(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            partner_obj = picking.manual_partner_id or picking.partner_id or False
            if partner_obj and partner_obj.parent_id:
                partner_obj = partner_obj.parent_id
            if picking.sale_id:
                partner_obj = picking.sale_id.partner_id
            partner_id = partner_obj and partner_obj.id or False
            res[picking.id] = partner_id
        return res
    
    def onchange_manual_partner(self, cr, uid, ids, manual_partner_id, context=None):
        res = {'value': {'real_customer_id': manual_partner_id}}
        return res
    
    _columns = {
                'package': fields.char('Package', size=128),
                'shop_id': fields.many2one('sale.shop', 'Location'),
                'client_order_ref': fields.char('Customer PO Number', size=128),
                'unposted': fields.boolean('Unposted ?'),
                'real_customer_id': fields.function(_get_real_partner, type="many2one",
                                                    relation="res.partner",
                                                    string="Customer", store=True),
                'manual_partner_id': fields.many2one('res.partner', 'Manual Partner',
                                                     domain="[('customer', '=', True)]"),
                'manual_name': fields.char('Manual DN #', size=128),
                'perm_cancel': fields.boolean('Perm Cancel')
                }
    
    def set_to_draft(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        move_obj = self.pool.get('stock.move')
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            moves = move_obj.search(cr, uid, [('picking_id', '=', p_id)])
            move_obj.write(cr, uid, moves, {'state': 'draft'})
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'stock.picking', p_id, cr)
            wf_service.trg_create(uid, 'stock.picking', p_id, cr)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _("Picking '%s' has been set in draft state.") % name
            self.log(cr, uid, id, message)
        return True
    
    def button_perm_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'perm_cancel': True}, context=context)
        return self.button_cancel(cr, uid, ids, context=context)
    
    def button_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_id and picking.invoice_id.state != 'cancel':
                raise osv.except_osv(_("Error !!!"),
                                     _("Please unpost related invoice before unposting picking"))
            set_draft = False
            if picking.state == 'done':
                set_draft = True
            if picking.seq_created:
                picking.write({'unposted': True})
            wf_service.trg_validate(uid, 'stock.picking', \
                                    picking.id, 'button_cancel', cr)
        return True
    
    def create_invoice_refund(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoiceing_pool = self.pool.get('stock.invoice.onshipping')
        ctx = context.copy()
        ctx.update({
                    'active_model': 'stock.picking.out',
                    'active_ids': ids,
                    'active_id': ids[0]
                    })
        default_vals = invoiceing_pool.default_get(cr, uid, ['invoice_date', 'group', 'journal_id'],
                                                   context=ctx)
        invoiceing_id = invoiceing_pool.create(cr, uid, default_vals, context=ctx)
        res = invoiceing_pool.open_invoice(cr, uid, [invoiceing_id], context=ctx)
        return res
    
    
stock_picking_out()

class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
                'sequence_no': fields.char('SI. No', size=64),
                'name': fields.text('Description')
                }
    
    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
        if move.product_id.valuation == 'real_time': # FIXME: product valuation should perhaps be a property?
            if context is None:
                context = {}
            src_company_ctx = dict(context,force_company=move.location_id.company_id.id)
            dest_company_ctx = dict(context,force_company=move.location_dest_id.company_id.id)
            account_moves = []
            # Outgoing moves (or cross-company output part)
            if move.location_id.company_id \
                and (move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, src_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                #returning goods to supplier
                if move.location_dest_id.usage == 'supplier':
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_src, reference_amount, reference_currency_id, context))]
                else:
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_dest, reference_amount, reference_currency_id, context))]

            # Incoming moves (or cross-company input part)
            if move.location_dest_id.company_id \
                and (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                #goods return from customer
                if move.location_id.usage == 'customer':
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_dest, acc_valuation, reference_amount, reference_currency_id, context))]
                else:
                    print "Removed To match Hatta Process"
#                     account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_src, acc_valuation, reference_amount, reference_currency_id, context))]

            move_obj = self.pool.get('account.move')
            for j_id, move_lines in account_moves:
                move_obj.create(cr, uid,
                        {
                         'journal_id': j_id,
                         'line_id': move_lines,
                         'ref': move.picking_id and move.picking_id.name}, context=context)
    
stock_move()


class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    
    def set_to_draft(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        move_obj = self.pool.get('stock.move')
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            moves = move_obj.search(cr, uid, [('picking_id', '=', p_id)])
            move_obj.write(cr, uid, moves, {'state': 'draft'})
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'stock.picking', p_id, cr)
            wf_service.trg_create(uid, 'stock.picking', p_id, cr)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _("Picking '%s' has been set in draft state.") % name
            self.log(cr, uid, id, message)
        return True
stock_picking_in()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

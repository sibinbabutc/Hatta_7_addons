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

import time

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'seq_created': fields.boolean('Seq Created ?'),
                'invoice_num' : fields.related('invoice_id', 'number', type='char', string='Invoice Number'),
                'cancel_note': fields.text(string="Cancellation Note"),
                'invoice_status': fields.related('invoice_id', 'state', type="selection",
                                                 selection=[("draft","Draft"), ("proforma","Pro-forma"),
                                                            ("proforma2","Unposted"), ("open","Posted"),
                                                            ("paid","Paid"), ("cancel","Cancelled")],
                                                 string="Invoice State"),
#                 'invoice_date': fields.date('Invoice Date')
                'invoice_date': fields.related('invoice_id', 'date_invoice', type="date",
                                               string='Invoice Date', store=True)
                }
    
    def action_done(self, cr, uid, ids, context=None):
        obj_sequence = self.pool.get('ir.sequence')
        res = super(stock_picking, self).action_done(cr, uid, ids, context=context)
        for picking_obj in self.browse(cr, uid, ids, context=context):
            picking_name = ''
            if picking_obj.sale_id and picking_obj.sale_id.unposted:
                for picking in picking_obj.sale_id.picking_ids:
                    if picking.state == 'cancel' and picking.unposted:
                        picking_name = picking.name or ''
                        picking.write({'name': picking_name + "Cancelled"+str(time.strftime('%d/%m/%Y %H:%M:%S')), 'unposted': False})
            if picking_obj.state != 'cancel' and picking_obj.unposted and picking_obj.seq_created:
                picking_name = picking_obj.name or ''
                picking_obj.write({'unposted': False})
            if picking_obj.manual_name:
                picking_name = picking_obj.manual_name
                picking_obj.write({'manual_name': ''})
            if picking_obj.rej_parent_picking_id:
                all_rej_picking_ids = self.search(cr, uid, [('rej_parent_picking_id', '=', picking_obj.rej_parent_picking_id.id),
                                                            ('state', '=', 'done'),
                                                            ('id', '!=', picking_obj.id)],
                                                  context=context)
                count = len(all_rej_picking_ids)
                count += 1
                picking_name = picking_obj.rej_parent_picking_id.name + ".%s"%(str(count))
            if not picking_name and picking_obj.transaction_type_id and picking_obj.transaction_type_id.sequence_id:
                picking_name = obj_sequence.next_by_id(cr, uid,
                                               picking_obj.transaction_type_id and \
                                                        picking_obj.transaction_type_id.sequence_id.id,
                                               context=context)
            if picking_name:
                picking_obj.write({'name': picking_name, 'seq_created': True})
        return res
    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        if context is None:
            context = {}
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type,
                                                          journal_id, context=context)
        res['sale_id'] = picking.sale_id and picking.sale_id.id or False
        res['purchase_id'] = picking.purchase_id and picking.purchase_id.id or False
        res['job_id'] = picking.job_id and picking.job_id.id or False
        if inv_type in ['out_invoice', 'in_refund']:
            res['date_invoice'] = time.strftime('%Y-%m-%d')
        return res
    
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'seq_created': fields.boolean('Seq Created ?'),
                'cancel_note': fields.text(string="Cancellation Note"),
                'invoice_num' : fields.related('invoice_id', 'number', type='char', string='Invoice Number'),
#                 'invoice_date': fields.date('Invoice Date')
                'invoice_date': fields.related('invoice_id', 'date_invoice', 'Invoice Date', store=True,
                                               type="date")
                }
stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _columns = {
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'seq_created': fields.boolean('Seq Created ?'),
                'invoice_num' : fields.related('invoice_id', 'number', type='char', string='Invoice Number'),
                'cancel_note': fields.text(string="Cancellation Note"),
                'invoice_status': fields.related('invoice_id', 'state', type="selection",
                                                 selection=[("draft","Draft"), ("proforma","Pro-forma"),
                                                            ("proforma2","Unposted"), ("open","Posted"),
                                                            ("paid","Paid"), ("cancel","Cancelled")],
                                                 string="Invoice State"),
#                 'invoice_date': fields.date('Invoice Date')
                'invoice_date': fields.related('invoice_id', 'date_invoice', 'Invoice Date',
                                               type="date", store=True)
                }
    
    def make_payment(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
#         ctx = context.copy()
#         ctx.update({
# #                     'default_number': parent.name,
#                     'active_move_line': ids[0],
# #                     'line_type': line_type,
#                     'default_type': 'payment',
#                     'type': 'payment',
# #                     'default_partner_id': partner_id,
# #                     'default_journal_id': parent.journal_id,
# #                     'default_reference': name,
# #                     'default_date': parent.date,
# #                     'default_name': name,
# #                     'default_active': False,
# #                     'account_id': account_id
#                     })
        context['active_ids'] = ids
        context['active_id'] = ids[0]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.matching',
#             'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    
stock_picking_in()

class stock_move(osv.osv):
    _inherit = 'stock.move'
    
#     def _get_reference_accounting_values_for_valuation(self, cr, uid, move, context=None):
#         reference_amount, reference_currency_id = super(stock_move, self)._get_reference_accounting_values_for_valuation(cr, uid,
#                                                                                                        move,
#                                                                                                        context=context)
#         if move.picking_id.type in ['in', 'out']:
#             reference_amount = move.price_unit or 0.00
#             if move.sale_line_id:
#                 reference_currency_id = move.sale_line_id.order_id.currency_id.id
#             if move.purchase_line_id:
#                 reference_currency_id = move.purchase_line_id.order_id.currency_id.id
# #             reference_currency_id = move.company_id.currency_id.id
# #             reference_currency_id = move.price_currency_id.id or reference_currency_id
#         return reference_amount, reference_currency_id
    
    def _create_account_move_line(self, cr, uid, move, src_account_id, dest_account_id,
                                  reference_amount, reference_currency_id, context=None):
        
        debit_credit_line = super(stock_move, self)._create_account_move_line(cr, uid, move,
                                                                                    src_account_id,
                                                                                    dest_account_id,
                                                                                    reference_amount,
                                                                                    reference_currency_id,
                                                                                    context=context)
        if move.picking_id and move.picking_id.invoice_date:
            debit = debit_credit_line[0][2]
            debit['man_date'] = move.picking_id.invoice_date
            debit['date'] = move.picking_id.invoice_date
            debit['amount_fc_temp'] = abs(debit['amount_currency'])
            credit = debit_credit_line[1][2]
            credit['man_date'] = move.picking_id.invoice_date
            credit['date'] = move.picking_id.invoice_date
            credit['amount_fc_temp'] = abs(credit['amount_currency'])
            debit_credit_line = [(0, 0, debit), (0, 0, credit)]
        return debit_credit_line
    
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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
from openerp.tools.translate import _

from openerp.tools.safe_eval import safe_eval
from datetime import datetime

class shipping_carrier(osv.osv):
    _name = 'shipping.carrier'
    _description = 'Shipping Carrier Model'
    
    _columns = {
        'name' : fields.char(string="Name", size=128),
        'note' : fields.text(string="Note"),
        'account_number': fields.char('Account Number', size=128),
        'partner_id': fields.many2one('res.partner', 'Partner', domain="[('supplier', '=', True)]",
                                      required=True)
                }

shipping_carrier()


class shipping_quotation(osv.osv):
    _name = 'shipping.quotation'
    _description = 'Shipping Quotation Model'
    _rec_name = 'awb'
    
    def _calc_total(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for quotation in self.browse(cr, uid, ids, context=context):
            res[quotation.id] = quotation.invoice_freight + quotation.invoice_duty
        return res
    
    def action_select(self, cr, uid, ids, context=None):
        if ids:
            for quotation in self.browse(cr, uid, ids, context=context):
                self.write(cr, uid, quotation.id, {'state' : 'selected'})
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        if ids:
            for quotation in self.browse(cr, uid, ids, context=context):
                self.write(cr, uid, quotation.id, {'state' : 'cancel'})
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        invoices = self.read(cr, uid, ids, ['state'], context=context)
        for inv in invoices:
            if inv['state'] in ['new', 'cancel']:
                unlink_ids.append(inv['id'])
            else:
                inv_obj = self.browse(cr, uid, [inv['id']], context=context)
                for invoice in inv_obj:
                    if invoice.invoice_id.quotation_ids:
                        for quotation in invoice.invoice_id.quotation_ids:
                            if inv['id'] == quotation.id:
                                raise osv.except_osv(_('Invalid Action!'), _('This Shipping Quotation is selected in a Shipping Invoice, so it cannot be deleted.'))
                    else:
                        unlink_ids.append(inv['id'])  
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def onchange_purchase_id(self, cr, uid, ids, purchase_id, context=None):
        res = {'value': {}}
        purchase_pool = self.pool.get('purchase.order')
        if purchase_id:
            purchase_obj = purchase_pool.browse(cr, uid, purchase_id, context=context)
            account_analytic_id = purchase_obj.analytic_account_id and \
                                        purchase_obj.analytic_account_id.id or False
            res['value']['account_analytic_id'] = account_analytic_id
        return res
    
    _columns = {
        'carrier_id' : fields.many2one('shipping.carrier', string='Carrier'),
        'carrier_freight' : fields.float(string='Carrier Freight Quote', digits=(2,2)),
        'carrier_duty' : fields.float(string='Carrier Duty Quote', digits=(2,2)),
        'invoice_freight' : fields.float(string='Carrier Invoice Freight', digits=(2,2)),
        'invoice_duty' : fields.float(string='Carrier Invoice Duty', digits=(2,2)),
        'purchase_id' : fields.many2one('purchase.order', string='Purchase Order'),
        'costsheet_freight_charge' : fields.related('purchase_id', 'freight_charges_lc',
                                        relation="purchase.order", readonly="1", string='CostSheet Freight Charge'),
        'costsheet_duty' : fields.related('purchase_id', 'customs_duty', relation="purchase.order",
                                    readonly="1", string='CostSheet Duty'),
        'awb_date' : fields.date(string='AWB Date'),
        'awb' : fields.char(string='AWB #', size=128),
        'remarks' : fields.text(string="Remarks"),
        'invoice_number' : fields.char(string='Invoice Number', size=128),
        'duty_invoice_number': fields.char('Duty Invoice Number', size=128),
        'state' : fields.selection([('new', 'New'), ('selected', 'Selected'), ('cancel', 'Cancel')],
                                   string='State'),
        'total' : fields.function(_calc_total, type='float', readonly="1", string='Total'),
        'invoice_id' : fields.many2one('shipping.invoice', string='Shipping Invoice'),
        'job_id': fields.related('purchase_id', 'job_id', type="many2one", relation='job.account',
                                 string="Job No.", store=True),
        'vessel_name' : fields.char('Vessel Name'),
        'move_id': fields.many2one('account.move', 'Related Voucher'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Cost Center'),
        'movement_state': fields.selection([('with_supp', 'With Supplier'),
                                           ('in_transit', 'In Transit'),
                                           ('received', 'Received')],'Movement Status'),
                }

    _defaults = {
        'state' : 'new'
                 }
    
    def _check_awb_no(self, cr, uid, ids, context=None):
        for ship_quote in self.browse(cr, uid, ids, context=context):
	        if ship_quote.awb:
                 ship_quotes = self.search(cr, uid, [('awb','=',ship_quote.awb),
                                       ('carrier_id','=',ship_quote.carrier_id.id),
                                       ('invoice_number','=',ship_quote.invoice_number),
                                       ('awb_date','=',ship_quote.awb_date)], context=context)
                 if len(ship_quotes) > 1:
                     return False
        return True
    
    _constraints = [
        (_check_awb_no, 'AWB # must be unique!', ['awb','carrier_id','invoice_number','awb_date']),
    ]
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'awb':False,
            'carrier_id':False,
            'invoice_number':False,
            'awb_date': False,
        })
        return super(shipping_quotation, self).copy(cr, uid, id, default, context)
    
#     def _check_carrier_awb(self, cr, uid, ids, context=None):
#         for quotation in self.browse(cr, uid, ids, context=context):
#             record = self.search(cr, uid, [('carrier_id', '=', quotation.carrier_id.id),
#                                            ('awb', '=', quotation.awb)])
#             if len(record) >= 2:
#                 return False
#             else:
#                 return True
#         return True    

shipping_quotation()


class shipping_invoice(osv.osv):
    _name = 'shipping.invoice'
    _description = 'Shipping Invoice Model'
    _rec_name = 'acc_no'
    
    def _calc_total(self, cr, uid, ids, field, arg, context=None):
        res, total = {}, 0.0
        inv_obj = self.browse(cr, uid, ids, context=context)
        for inv in inv_obj:
            total = 0.00
            for quotation in inv.quotation_ids:
                total+=quotation.total
            res[inv.id] = total
        return res
    
    def _calc_net_total(self, cr, uid, ids, field, arg, context=None):
        res = {}
        inv_obj = self.browse(cr, uid, ids, context=context)
        for inv in inv_obj:
            res[inv.id] = inv.total - inv.rounding_off
        return res
    
    def action_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        icp = self.pool.get('ir.config_parameter')
        period_pool = self.pool.get('account.period')
        account_move_line = self.pool.get('account.move.line')
        account_move_pool = self.pool.get('account.move')
        shipping_quot_pool = self.pool.get('shipping.quotation')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        duty_account_id = safe_eval(icp.get_param(cr, uid,
                                                  'hatta_account.duty_account_id', 'False'))
        courier_account_id = safe_eval(icp.get_param(cr, uid,
                                                     'hatta_account.courier_account_id', 'False'))
        if not duty_account_id or not courier_account_id:
            raise osv.except_osv(_("Error!!!"),
                                 _("Please configure Duty and Courier accounts in settings or contact Administartor"))
        move_ids = []
        for invoice in self.browse(cr, uid, ids, context=context):
            if not invoice.acc_date:
                raise osv.except_osv(_("Error!!!"),
                                     _("Please select a accounting date!!!"))
            if not invoice.journal_id:
                raise osv.except_osv(_("Error!!!"),
                                     _("Please select a journal!!!"))
            amount_total = 0.00
            lines = []
            carrier_name = invoice.carrier_id.name.upper()
            date_from_obj = datetime.strptime(invoice.acc_date, "%Y-%m-%d")
            month = date_from_obj.strftime("%B")
            year = str(date_from_obj.strftime("%Y"))
            ctx = dict(context or {}, account_period_prefer_normal=True)
            search_periods = period_pool.find(cr, uid, invoice.acc_date, context=ctx)
            period_id = search_periods[0]
            invoice_list = []
            has_cou = False
            has_duty = False
            quotation_ids = []
            for line in invoice.quotation_ids:
                quotation_ids.append(line.id)
                if line.invoice_freight != 0.00:
                    has_cou = True
                    invoice_number = line.invoice_number or ''
                    if invoice_number:
                        invoice_list.append(invoice_number)
                    name = "%s COURIER CHARGES FOR %s %s INV NO %s"%(carrier_name, month, year, invoice_number)
                    if line.remarks:
                        name = "%s\n%s"%(name, line.remarks)
                    vals = {
                            'name': name.upper(),
                            'date': invoice.acc_date,
                            'partner_id': False,
                            'account_id': courier_account_id,
                            'journal_id': invoice.journal_id.id,
                            'period_id': period_id,
                            'job_id': line.job_id and line.job_id.id or False,
                            'debit': line.invoice_freight or 0.00,
                            'credit': 0.00,
                            'analytic_account_id': line.account_analytic_id.id
                            }
#                     account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
#                                                                                          courier_account_id,
#                                                                                          context=context)
#                     vals.update(account_change_onchange_data.get('value', {}))
                    lines.append((0, 0, vals))
                    amount_total += line.invoice_freight
                if line.invoice_duty != 0.00:
                    has_duty = True
                    invoice_number = line.duty_invoice_number or ''
                    if invoice_number:
                        invoice_list.append(invoice_number)
                    name = "%s CUSTOMS DUTY FOR %s %s INV NO %s"%(carrier_name, month, year, invoice_number)
                    if line.remarks:
                        name = "%s\n%s"%(name, line.remarks)
                    vals = {
                            'name': name.upper(),
                            'date': invoice.acc_date,
                            'partner_id': False,
                            'account_id': duty_account_id,
                            'journal_id': invoice.journal_id.id,
                            'period_id': period_id,
                            'job_id': line.job_id and line.job_id.id or False,
                            'debit': line.invoice_duty or 0.00,
                            'credit': 0.00,
                            'analytic_account_id': line.account_analytic_id.id
                            }
#                     account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
#                                                                                          duty_account_id,
#                                                                                          context=context)
#                     vals.update(account_change_onchange_data.get('value', {}))
                    lines.append((0, 0, vals))
                    amount_total += line.invoice_duty
            if amount_total != 0.00:
                invoice_number = ''
                if invoice_list:
                    invoice_list = list(set(invoice_list))
                    invoice_number = ", ".join(invoice_list)
                name_list = []
                if has_duty:
                    name_list.append("CUSTOMS DUTY")
                if has_cou:
                    name_list.append("COURIER CHARGES")
                name = " & ".join(name_list)
                invoice_list = list(set(invoice_list))
                name = "%s %s AS PER %s FOR %s %s"%(carrier_name, name, str(', '.join(invoice_list)),
                                                    month, year)
                vals = {
                        'name': name.upper(),
                        'date': invoice.acc_date,
                        'partner_id': invoice.carrier_id.partner_id.id,
                        'account_id': invoice.carrier_id.partner_id.property_account_payable.id,
                        'journal_id': invoice.journal_id.id,
                        'period_id': period_id,
                        'debit': 0.00,
                        'credit': amount_total or 0.00,
                        }
                account_change_onchange_data = account_move_line.onchange_account_id(cr, uid, ids,
                                                                                     invoice.carrier_id.partner_id.property_account_payable.id,
                                                                                     context=context)
                vals.update(account_change_onchange_data.get('value', {}))
                lines.append((0, 0, vals))
                move_vals = {
                             'journal_id': invoice.journal_id.id,
                             'ref': name.upper(),
                             'date': invoice.acc_date,
                             'period_id': period_id,
                             'line_id': lines
                             }
                move_id = account_move_pool.create(cr, uid, move_vals, context=context)
                shipping_quot_pool.write(cr, uid, quotation_ids, {'move_id': move_id},
                                         context=context)
                invoice.write({'purchase_others': move_id})
                move_ids.append(move_id)
            self.write(cr, uid, invoice.id, {'state' : 'confirm'})
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_move_journal_line')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in',["+','.join(map(str, move_ids))+"])]"
        return result
    
    def action_cancel(self, cr, uid, ids, context=None):
        if ids:
            for invoice in self.browse(cr, uid, ids, context=context):
                self.write(cr, uid, invoice.id, {'state' : 'cancel'})
        return True
    
    def onchange_carrier(self, cr, uid, ids, carrier_id, context=None):
        carrier_pool = self.pool.get('shipping.carrier')
        res = {'value': {}}
        if carrier_id:
            carrier_obj = carrier_pool.browse(cr, uid, carrier_id, context=context)
            res['value']['acc_no'] = carrier_obj.account_number or ''
        return res
    
    _columns = {
        'carrier_id' : fields.many2one('shipping.carrier', required="1",
                            readonly=True, states={'draft': [('readonly', False)],
                                                   'cancel': [('readonly', False)]},
                            string="Carrier"),
                
        'date' : fields.date(required="1", readonly=True, states={'draft': [('readonly', False)],
                                                                  'cancel': [('readonly', False)]},
                            string="Date"),
        'acc_date': fields.date('Accounting Date'),
                
        'quotation_ids' : fields.one2many('shipping.quotation', 'invoice_id', 'Shipping Quotation',
                            readonly=True, states={'draft': [('readonly', False)],
                                                   'cancel': [('readonly', False)]}),
                
        'payments_ids' : fields.many2many('account.move', 'invoice_move_rel', 'invoice_id', 'move_id',
                            string="Payments"),
                
        'state' : fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')],
                            string='State'),
                
        'acc_no' : fields.char('A/C #', readonly=True, states={'draft': [('readonly', False)],
                                                               'cancel': [('readonly', False)]},),
        
        'notes' : fields.text('Notes', readonly=True, states={'draft': [('readonly', False)],
                                                                  'cancel': [('readonly', False)]},),
        
        'purchase_others' : fields.many2one('account.move', 'Purchase Others',
                            readonly=True, states={'draft': [('readonly', False)],
                                                   'cancel': [('readonly', False)]},),
        
        'total' : fields.function(_calc_total, type='float', readonly="1", string='Total'),
        
        'rounding_off' : fields.float(readonly=True, states={'draft': [('readonly', False)],
                                                             'cancel': [('readonly', False)]},
                            string="Rounding Off"),
                
        'net_total' : fields.function(_calc_net_total, type='float', readonly="1", string='Net Total'),
        'journal_id': fields.many2one('account.journal', 'Journal',
                                      domain="[('display_in_voucher', '=', True)]")
                }
    
    _defaults={
        'state' : 'draft'
               }

shipping_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

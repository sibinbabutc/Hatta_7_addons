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

import openerp.addons.decimal_precision as dp
from openerp import netsvc
import time

class pol_mass_select(osv.osv_memory):
    _name = 'pol.mass.select'
    _description = 'Purchase Line Mass Selection'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        purchase_pool = self.pool.get('purchase.order')
        res = super(pol_mass_select, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            po_obj = purchase_pool.browse(cr, uid, active_id, context=context)
            res['po_id'] = active_id
            res['partner_id'] = po_obj.partner_id and po_obj.partner_id.id or False
            res['partner_ref'] = po_obj.partner_ref or ''
            res['quote_send_by'] = po_obj.quote_send_by
            if po_obj.quote_date:
                res['quote_date'] = po_obj.quote_date
            lines = []
            for line in po_obj.order_line:
                vals = {
                        'select': line.select_line or False,
                        'sequence_no': line.sequence_no,
                        'product_id': line.product_id and line.product_id.id or False,
                        'price': line.price_unit or 0.00,
                        'pol_id': line.id
                        }
                lines.append((0, 0, vals))
            res['line_ids'] = lines
        return res
    
    _columns = {
                'po_id': fields.many2one('purchase.order', 'RFQ'),
                'partner_id': fields.many2one('res.partner', 'Supplier'),
                'line_ids': fields.one2many('pol.mass.select.line', 'wizard_id', 'Line(s)'),
                'partner_ref': fields.char('Supplier Quote No.', size=128),
                'quote_send_by': fields.char('Quote Send By', size=128),
                'quote_date': fields.date('Quote Date'),
                'pricelist_id': fields.many2one('product.pricelist', 'Pricelist',
                                                domain="[('type', '=', 'purchase')]")
                }
    
    _defaults = {
                 'quote_date': lambda *a: time.strftime('%Y-%m-%d')
                 }
    
    def confirm_select_line(self, cr, uid, ids, context=None):
        line_pool = self.pool.get('pol.mass.select.line')
        po_pool = self.pool.get('purchase.order')
        pol_pool = self.pool.get('purchase.order.line')
        wf_service = netsvc.LocalService('workflow')
        data = self.read(cr, uid, ids, context={})[0]
        lines = data.get('line_ids', [])
        po_id = data.get('po_id', False)[0]
        partner_ref = data.get('partner_ref', '')
        quote_send_by = data.get('quote_send_by', '')
        quote_date = data.get('quote_date', False)
        pricelist_id = data.get('pricelist_id', False)[0]
        po_obj = po_pool.browse(cr, uid, po_id, context=context)
        pricelist_change_data = po_pool.onchange_pricelist(cr, uid, ids, pricelist_id, context=context)
        pricelist_change_vals = pricelist_change_data.get('value', {})
        base_currency = po_obj.foreign_currency and po_obj.foreign_currency.id or False
        currency_id = pricelist_change_vals.get('currency_id', False)
        currency_onchange_data = po_pool.onchange_currency(cr, uid, ids, base_currency, currency_id)
        pricelist_change_vals.update(currency_onchange_data.get('value', {}))
        pricelist_change_vals.update({
                                      'partner_ref': partner_ref,
                                      'quote_send_by': quote_send_by,
                                      'quote_date': quote_date,
                                      'pricelist_id': pricelist_id
                                      })
        po_obj.write(pricelist_change_vals)
        exchange_rate = po_obj.exchange_rate or 1.0000
        for line_obj in line_pool.browse(cr, uid, lines, context=context):
            pol_line_obj = line_obj.pol_id or False
            if pol_line_obj:
                vals = {
                        'price_unit': line_obj.price or 0.00
                        }
                pol_line_obj.write(vals)
                if line_obj.select and not pol_line_obj.select_line:
                    ctx = context.copy()
                    ctx['overide'] =True
                    pol_pool.select_po_line(cr, uid, [pol_line_obj.id], context=ctx)
                else:
                    pol_line_obj.write({'select_line': line_obj.select})
        wf_service.trg_validate(uid, 'purchase.order', \
                                po_id, 'bid_received', cr)
        return True
    
pol_mass_select()

class pol_mass_select_line(osv.osv_memory):
    _name = 'pol.mass.select.line'
    _description = 'Mass selection line'
    _columns = {
                'sequence_no': fields.char('SI. No', size=128),
                'product_id': fields.many2one('product.product', 'Product'),
                'price': fields.float('Unit Price', digits_compute=dp.get_precision('Account')),
                'select': fields.boolean('Select ?'),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Line'),
                'wizard_id': fields.many2one('pol.mass.select', 'Wizard Ref.')
                }
pol_mass_select_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

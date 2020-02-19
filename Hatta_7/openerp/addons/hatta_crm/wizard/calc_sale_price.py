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
from tools.translate import _
import math

class calc_sale_price(osv.osv_memory):
    _name = 'calc.sale.price'
    _description = 'Sale Price Calculation Form RFQ'
    
    def default_get(self, cr, uid, fields, context=None):
        purchase_pool = self.pool.get('purchase.order')
        if context is None:
            context = {}
        res = super(calc_sale_price, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            warn = True
            purchase_obj = purchase_pool.browse(cr, uid, active_id, context=context)
            lines = []
            for line in purchase_obj.order_line:
                vals = {}
                if line.select_line:
                    warn = False
                    vals = {
                            'sequence_no': line.sequence_no,
                            'product_id': line.product_id and line.product_id.id or False,
                            'cost_price': line.unit_price_lc or 0.00,
                            'pol_id': line.id or False
                            }
                    lines.append((0, 0, vals))
            res['line_ids'] = lines
            if warn:
                raise osv.except_osv(_('Error !!!'),_('No Lines Selected !!'))
            cost_price = purchase_obj.total_products_cost or 0.00
            cost_price_lc = purchase_obj.total_products_cost_lc or 0.00
            freight_charges = purchase_obj.freight_charges or 0.00
            freight_charges_lc = purchase_obj.freight_charges_lc or 0.00
            fob_charges = purchase_obj.fob_charges or 0.00
            fob_charges_lc = purchase_obj.fob_charges_lc or 0.00
            other_charges = purchase_obj.other_charges or 0.00
            other_charges_lc = purchase_obj.other_charges_lc or 0.00
            total_cost = purchase_obj.total_amount_fc or 0.00
            total_cost_lc = purchase_obj.total_amount_lc or 0.00
            communication_charges = purchase_obj.communication_charges or 0.00
            bank_charges = purchase_obj.bank_charges or 0.00
            bank_interest = purchase_obj.bank_interest or 0.00
            insurance_charges = purchase_obj.insurance_charges or 0.00
            customs_duty = purchase_obj.customs_duty or 0.00
            clg_agent_charges = purchase_obj.clg_agent_charges or 0.00
            clearing_expenses = purchase_obj.clearing_expenses or 0.00
            transport_delivery_expenses = purchase_obj.transport_delivery_expenses or 0.00
            misc_expenses = purchase_obj.misc_expenses or 0.00
            total_amount_lc = purchase_obj.total_expenses or 0.00
            exchange_rate = purchase_obj.exchange_rate or 0.00
            total_amount = float(total_amount_lc) + float(total_cost_lc)
            if cost_price_lc != 0.00:
                factor = float(total_amount) / float(cost_price_lc)
            total_sell_price = 0.00
            for line in purchase_obj.order_line:
                if line.select_line:
                    total_sell_price += float(line.unit_price_lc) * float(factor) * float(line.product_qty)
            res.update({
                        'lead_id': purchase_obj.lead_id and purchase_obj.lead_id.id or False,
                        'po_id': active_id,
                        'partner_id': purchase_obj.partner_id and purchase_obj.partner_id.id or \
                                        False,
                        'exchange_rate': exchange_rate,
                        'currency_id': purchase_obj.currency_id and purchase_obj.currency_id.id or \
                                            False,
                        'local_currency_id': purchase_obj.company_id and \
                                                purchase_obj.company_id.currency_id and \
                                                purchase_obj.company_id.currency_id.id or
                                                False,
                        'cost_price_fc': cost_price,
                        'cost_price_lc': cost_price_lc,
                        'freight_charges_fc': freight_charges,
                        'freight_charges_lc': freight_charges_lc,
                        'fob_charges_fc': fob_charges,
                        'fob_charges_lc': fob_charges_lc,
                        'other_charges_fc': other_charges,
                        'other_charges_lc': other_charges_lc,
                        'total_cost_fc': total_cost,
                        'total_cost_lc': total_cost_lc,
                        'comm_charges': communication_charges,
                        'bank_charges': bank_charges,
                        'insu_charges': insurance_charges,
                        'bank_int': bank_interest,
                        'duty': customs_duty,
                        'agent_charge': clg_agent_charges,
                        'clearing_exp_port': clearing_expenses,
                        'trans_del_expense': transport_delivery_expenses,
                        'misc_exp': misc_expenses,
                        'total_exp': total_amount_lc,
                        'total_exp2': total_amount_lc,
                        'total_cost_lc2': total_cost_lc,
                        'total_sell_price': total_sell_price,
                        'factor': factor
                        })
        return res
    
    def onchange_margin(self, cr, uid, ids, margin, po_id=False, total_exp2=0.00, total_cost_lc2=0.00,
                        cost_price_lc=0.00, context=None):
        po_pool = self.pool.get('purchase.order')
        res = {'value': {}}
        if po_id:
            po_obj = po_pool.browse(cr, uid, po_id, context=context)
            total_amount = float(margin) + float(total_exp2) + float(total_cost_lc2)
            factor = 1.000
            if cost_price_lc != 0.00:
                factor = float(total_amount) / float(cost_price_lc)
            total_sell_price = 0.00
            for line in po_obj.order_line:
                if line.select_line:
                    unit_selling_price = float(line.unit_price_lc) * float(factor)
                    total_sell_price += round(unit_selling_price, 2) * float(line.product_qty)
            res['value']['total_sell_price'] = total_sell_price
            res['value']['factor'] = factor
        return res
    
    _columns = {
                'lead_id': fields.many2one('crm.lead', 'Enquiry No'),
                'po_id': fields.many2one('purchase.order', 'Purchase Order'),
                'partner_id': fields.many2one('res.partner', 'Supplier'),
                'exchange_rate': fields.float('Exchange Rate', digits=(16, 5)),
                'currency_id': fields.many2one('res.currency', 'Currency'),
                'local_currency_id': fields.many2one('res.currency', 'Local Currency'),
                'cost_price_lc': fields.float('Cost Price', digits_compute=dp.get_precision('Account')),
                'cost_price_fc': fields.float('Cost Price', digits_compute=dp.get_precision('Account')),
                'freight_charges_fc': fields.float('Freight Charges',
                                                   digits_compute=dp.get_precision('Account')),
                'freight_charges_lc': fields.float('Freight Charges',
                                                   digits_compute=dp.get_precision('Account')),
                'fob_charges_lc': fields.float('Fob Charges', digits_compute=dp.get_precision('Account')),
                'fob_charges_fc': fields.float('Fob Charges', digits_compute=dp.get_precision('Account')),
                'other_charges_lc': fields.float('Other Charges',
                                                 digits_compute=dp.get_precision('Account')),
                'other_charges_fc': fields.float('Other Charges',
                                                 digits_compute=dp.get_precision('Account')),
                'total_cost_fc': fields.float('Total Cost', digits_compute=dp.get_precision('Account')),
                'total_cost_lc': fields.float('Total Cost', digits_compute=dp.get_precision('Account')),
                'comm_charges': fields.float('Communication Charges',
                                             digits_compute=dp.get_precision('Account')),
                'bank_charges': fields.float('Bank Charges',
                                             digits_compute=dp.get_precision('Account')),
                'insu_charges': fields.float('Insurance Charges',
                                             digits_compute=dp.get_precision('Account')),
                'bank_int': fields.float('Bank Interest 8% Days',
                                         digits_compute=dp.get_precision('Account')),
                'duty': fields.float('Customs Duty 6%',
                                     digits_compute=dp.get_precision('Account')),
                'agent_charge': fields.float('Clg. Agent Charges',
                                             digits_compute=dp.get_precision('Account')),
                'clearing_exp_port': fields.float('Clearing Expense At Port',
                                                  digits_compute=dp.get_precision('Account')),
                'trans_del_expense': fields.float('Transport & Delivery Expense',
                                                  digits_compute=dp.get_precision('Account')),
                'misc_exp': fields.float('Misc. Expenses if Any',
                                         digits_compute=dp.get_precision('Account')),
                'total_exp': fields.float('Total Expenses',
                                          digits_compute=dp.get_precision('Account')),
                'total_exp2': fields.float('Total Expenses',
                                           digits_compute=dp.get_precision('Account')),
                'total_cost_lc2': fields.float('Total Cost',
                                               digits_compute=dp.get_precision('Account')),
                'margin': fields.float('Margin',
                                       digits_compute=dp.get_precision('Account')),
                'total_sell_price': fields.float('Total Selling Price',
                                                 digits_compute=dp.get_precision('Account')),
                'factor': fields.float('Ratio', digits=(16, 8)),
                'cost_sheet_required': fields.boolean('Cost Sheet Required ?'),
                'line_ids': fields.one2many('calc.sale.price.line', 'wizard_id',
                                            'Lines')
                }
    _defaults = {
                 'currency_id': 3,
                 'local_currency_id': 1,
                 'cost_sheet_required': True
                 }
    
    def cal_sale_price(self, cr, uid, ids, context=None):
        crm_product_line_pool = self.pool.get('crm.product.lines')
        po_pool = self.pool.get('purchase.order')
        line_pool = self.pool.get('calc.sale.price.line')
        data = self.read(cr, uid, ids, context=context)[0]
        factor = data.get('factor', 1.0000)
        lead_id = data.get('lead_id', (False)) and data.get('lead_id', False)[0]
        po_id = data.get('po_id', (False))[0]
        margin = data.get('margin', 0.00)
        factor = data.get('factor', 0.00)
        cost_sheet_required = data.get('cost_sheet_required', False)
        lines = data.get('line_ids', [])
        if po_id:
            po_obj = po_pool.browse(cr, uid, po_id, context=context)
            po_obj.write({'sale_calculated': True})
        if po_id and cost_sheet_required:
            total_sale = 0.00
            for line in po_obj.order_line:
                unit_price_lc = line.unit_price_lc or 0.00
                sale_price = float(line.unit_price_lc) * float(factor)
                total_sale += sale_price
                line.write({'sale_price': sale_price, 'sale_calculated': True})
            po_obj.write({'margin': margin, 'factor': factor})
        elif po_id and not cost_sheet_required:
            tot_margin = 0.00
            for line_obj in line_pool.browse(cr, uid, lines, context=context):
                margin = line_obj.margin or 0.00
                pol_obj = line_obj.pol_id or False
                if pol_obj:
                    tot_margin += margin * pol_obj.product_qty
                    pol_obj.write({'sale_price': line_obj.sale_price or 0.00, 'sale_calculated': True,
                                   'margin': margin})
            po_pool.write(cr, uid, po_id, {'sale_calculated': True, 'margin': tot_margin},
                          context=context)
        return True
    
calc_sale_price()

class calc_sale_price_line(osv.osv_memory):
    _name = 'calc.sale.price.line'
    _description = 'Calc Sale Price Line'
    
    def onchange_line_margin(self, cr, uid, ids, margin=0.00, cost_price=0.00, context=None):
        res = {
               'value': {
                         'sale_price': 0.00
                         }
               }
        if margin:
            res['value']['sale_price'] = cost_price + margin
        return res
    
    _columns = {
                'sequence_no': fields.char('SI.No', size=64),
                'product_id': fields.many2one('product.product', 'Product'),
                'cost_price': fields.float('Unit Cost Price'),
                'sale_price': fields.float('Unit Sale Price'),
                'margin': fields.float('Margin'),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Line Ref'),
                'wizard_id': fields.many2one('calc.sale.price', 'Wizard Ref')
                }
calc_sale_price_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

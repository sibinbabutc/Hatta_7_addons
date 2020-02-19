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

class pol_cost_price_update(osv.osv):
    _name = 'cost.price.update'
    _decription = 'Cost Price Update from purchase line'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        pol_pool = self.pool.get('purchase.order.line')
        res = super(pol_cost_price_update, self).default_get(cr, uid, fields, context=context)
        pol_id = context.get('active_id', False)
        if pol_id:
            pol_obj = pol_pool.browse(cr, uid, pol_id, context=context)
            res.update({
                        'freight_charges': pol_obj.freight_charges,
                        'fob_charges': pol_obj.fob_charges,
                        'other_charges': pol_obj.other_charges,
                        'communication_charges': pol_obj.communication_charges,
                        'bank_charges': pol_obj.bank_charges,
                        'bank_interest': pol_obj.bank_interest,
                        'insurance_charges': pol_obj.insurance_charges,
                        'customs_duty': pol_obj.customs_duty,
                        'clg_agent_charges': pol_obj.clg_agent_charges,
                        'clearing_expenses': pol_obj.clearing_expenses,
                        'transport_delivery_expenses': pol_obj.transport_delivery_expenses,
                        'misc_expenses': pol_obj.misc_expenses,
                        'pol_id': pol_obj.id,
                        'exchange_rate': pol_obj.exchange_rate or 1.0000
                        })
        return res
    
    def onchange_freight(self, cr, uid, ids, freight_charges, freight_charges_lc, exchange_rate,
                         context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if context.get('fc_change', False) and freight_charges and exchange_rate:
            new_freight_charges_lc = float(freight_charges) * float(exchange_rate)
            if round(new_freight_charges_lc, 2) != round(freight_charges_lc, 2):
                res['value']['freight_charges_lc'] = new_freight_charges_lc
        if context.get('lc_change', False) and freight_charges_lc and exchange_rate:
            new_freight_charges = float(freight_charges_lc) / float(exchange_rate)
            if round(new_freight_charges, 2) != round(freight_charges, 2):
                res['value']['freight_charges'] = new_freight_charges
        return res
    
    def onchange_fob(self, cr, uid, ids, fob_charges, fob_charges_lc, exchange_rate,
                     context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if context.get('fc_change', False) and fob_charges and exchange_rate:
            new_fob_charges_lc = float(fob_charges) * float(exchange_rate)
            if round(new_fob_charges_lc, 2) != round(fob_charges_lc, 2):
                res['value']['fob_charges_lc'] = new_fob_charges_lc
        if context.get('lc_change', False) and fob_charges_lc and exchange_rate:
            new_fob_charges = float(fob_charges_lc) / float(exchange_rate)
            if round(new_fob_charges, 2) != round(fob_charges, 2):
                res['value']['fob_charges'] = new_fob_charges
        return res
    
    def onchange_other_ch(self, cr, uid, ids, other_charges, other_charges_lc, exchange_rate,
                          context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if context.get('fc_change', False) and other_charges and exchange_rate:
            new_other_charges_lc = float(other_charges) * float(exchange_rate)
            if round(new_other_charges_lc, 2) != round(other_charges_lc, 2):
                res['value']['other_charges_lc'] = new_other_charges_lc
        if context.get('lc_change', False) and other_charges_lc and exchange_rate:
            new_other_charges = float(other_charges_lc) / float(exchange_rate)
            if round(new_other_charges, 2) != round(other_charges, 2):
                res['value']['other_charges'] = new_other_charges
        return res
    
    _columns = {
                'freight_charges': fields.float('Freight Charges FC'),
                'fob_charges': fields.float('Fob Charges FC'),
                'other_charges': fields.float('Other Charges(Cert of Compliance) FC'),
                'freight_charges_lc': fields.float('Freight Charges LC'),
                'fob_charges_lc': fields.float('Fob Charges LC'),
                'other_charges_lc': fields.float('Other Charges(Cert of Compliance) LC'),
                'communication_charges': fields.float('Communication Charges'),
                'bank_charges': fields.float('Bank Charges'),
                'bank_interest': fields.float('Bank Interest(9% days)'),
                'insurance_charges': fields.float('Insurance Charges'),
                'customs_duty': fields.float('Customs Duty(6%)'),
                'clg_agent_charges': fields.float('Cleaning Agent Charges'),
                'clearing_expenses': fields.float('Clearing Expenses at port'),
                'transport_delivery_expenses': fields.float('Transport and Delivery Expenses'),
                'misc_expenses': fields.float('Misc. Expenses if any'),
                'pol_id': fields.many2one('purchase.order.line', 'Purchase Line Reference'),
                'exchange_rate': fields.float('Exchange Rate', digits=(16, 5))
                }
    
    def change_cost(self, cr, uid, ids, context=None):
        pur_pool = self.pool.get('purchase.order')
        pur_line_pool = self.pool.get('purchase.order.line')
        data = self.read(cr, uid, ids, context={})[0]
        pur_line_id = data.get('pol_id', (False))[0]
        if pur_line_id:
            pur_line_obj = pur_line_pool.browse(cr, uid, pur_line_id, context=context)
            pur_id = pur_line_obj.order_id and pur_line_obj.order_id.id or False
            if pur_id:
                vals = {
                        'freight_charges': data.get('freight_charges', 0.00),
                        'fob_charges': data.get('fob_charges', 0.00),
                        'other_charges': data.get('other_charges', 0.00),
                        'freight_charges_lc': data.get('freight_charges_lc', 0.00),
                        'fob_charges_lc': data.get('fob_charges_lc', 0.00),
                        'other_charges_lc': data.get('other_charges_lc', 0.00),
                        'communication_charges': data.get('communication_charges', 0.00),
                        'bank_charges': data.get('bank_charges', 0.00),
                        'bank_interest': data.get('bank_interest', 0.00),
                        'insurance_charges': data.get('insurance_charges', 0.00),
                        'customs_duty': data.get('customs_duty', 0.00),
                        'clg_agent_charges': data.get('clg_agent_charges', 0.00),
                        'clearing_expenses': data.get('clearing_expenses', 0.00),
                        'transport_delivery_expenses': data.get('transport_delivery_expenses', 0.00),
                        'misc_expenses': data.get('misc_expenses', 0.00),
                        }
                pur_pool.write(cr, uid, pur_id, vals, context=context)
        return True
    
pol_cost_price_update()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

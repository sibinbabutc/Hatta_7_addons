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
from datetime import datetime
from operator import itemgetter

class bank_charge_calc(osv.osv_memory):
    _name = 'bank.charge.calc'
    _description = 'Bank Charge Calculation'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        purchase_pool = self.pool.get('purchase.order')
        payment_term_pool = self.pool.get('account.payment.term')
        line_pool = self.pool.get('bank.charge.line')
        res = super(bank_charge_calc, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            purchase_obj = purchase_pool.browse(cr, uid, active_id, context=context)
            res['amount_total'] = purchase_obj.total_amount_lc
            res['int_rate'] = purchase_obj.bank_int_rate or 0.00
            res['currency_id'] = purchase_obj.foreign_currency and \
                                        purchase_obj.foreign_currency.id or False
            res['purchase_id'] = purchase_obj.id or False
            lines = []
            if purchase_obj.payment_interest_ids:
                for line in purchase_obj.payment_interest_ids:
                    vals = {
                            'amount': line.amount,
                            'days': line.days,
                            'int_amount': line.int_amount
                            }
                    lines.append((0, 0, vals))
            else:
                weeks = purchase_obj.delivery_weeks or 0
                days = (weeks * 7) + 45
                vals = {
                        'amount': purchase_obj.total_amount_lc,
                        'days': days,
                        }
                onchange_data = line_pool.onchange_int(cr, uid, [], purchase_obj.total_amount_lc,
                                                       purchase_obj.bank_int_rate or 0.00,
                                                       purchase_obj.total_amount_lc,
                                                       days, context=context)
                vals.update(onchange_data.get('value', {}))
                lines.append((0, 0, vals))
            res['line_ids'] = lines
        return res
    
    def onchange_line(self, cr, uid, ids, line_ids, amount_total, context=None):
        res = {'value': {}}
        amount_alloted = 0.00
        for line in line_ids:
            if not line[1] and isinstance(line[2], dict):
                data = line[2]
                amount_alloted += data.get('int_amount', 0.00)
        res['value'] = {
                        'amount_total_int': amount_alloted
                        }
        return res
    
    _columns = {
                'amount_total': fields.float('Total Amount'),
                'int_rate': fields.float('Bank Interest Rate', digits_compute=dp.get_precision('Account')),
                'purchase_id': fields.many2one('purchase.order', 'Purchase Ref'),
                'currency_id': fields.many2one('res.currency', 'Currency'),
                'line_ids': fields.one2many('bank.charge.line', 'wizard_id',
                                            'Lines'),
                'amount_total_int': fields.float('Total Interest', digits_compute=dp.get_precision('Account')),
                }
    
    def apply_bank_charge(self, cr, uid, ids, context=None):
        line_pool = self.pool.get('bank.charge.line')
        purchase_pool = self.pool.get('purchase.order')
        purchase_int_pool = self.pool.get('purchase.bank.interest')
        data = self.read(cr, uid, ids, context={})[0]
        line_ids = data.get('line_ids', [])
        purchase_id = data.get('purchase_id', False)
        int_rate = data.get('int_rate', 0.00)
        interest_amount = 0.00
        line_vals = []
        for line_obj in line_pool.browse(cr, uid, line_ids, context=context):
            interest_amount += line_obj.int_amount or 0.00
            line_vals.append((0, 0, {
                                     'amount': line_obj.amount or 0.00,
                                     'days': line_obj.days or 0,
                                     'int_amount': line_obj.int_amount or 0.00
                                     }))
        if purchase_id:
            old_line_ids = purchase_int_pool.search(cr, uid, [('purchase_id', '=', purchase_id[0])],
                                                    context=context)
            purchase_int_pool.unlink(cr, uid, old_line_ids, context=context)
            round_bank_int = interest_amount
            if round_bank_int < 100.00:
                round_bank_int = 100.00
            purchase_pool.write(cr, uid, purchase_id[0], {'bank_interest': round_bank_int,
                                                          'real_bank_interest': interest_amount,
                                                          'payment_interest_ids': line_vals,
                                                          'bank_int_rate': int_rate},
                                context=context)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
bank_charge_calc()

class bank_charge_line(osv.osv_memory):
    _name = 'bank.charge.line'
    _description = 'Lines'
    
    def onchange_int(self, cr, uid, ids, amount_total=0.00, int_rate=0.00, amount=0.00, days=0, context=None):
        res = {}
        int = (float(amount)* (float(int_rate) / 100.00) * float(days)) / 360
        res['value'] = {'int_amount': int}
        return res
    
    _columns = {
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'days': fields.integer('Days'),
                'int_amount': fields.float('Interest Amount', digits_compute=dp.get_precision('Account')),
                'wizard_id': fields.many2one('bank.charge.calc', 'Wizard Ref')
                }
bank_charge_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

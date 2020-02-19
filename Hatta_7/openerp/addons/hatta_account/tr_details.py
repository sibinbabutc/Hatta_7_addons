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

import time
from datetime import date,datetime
from datetime import date, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil import parser
from dateutil.relativedelta import relativedelta


import openerp.addons.decimal_precision as dp


class tr_model(osv.osv):
    _name = 'tr.model'
    _description = 'TR Model'
    
    
    _columns = {
            'name' : fields.char(size=128, string="TR No.", required="1"),
            'limit' : fields.float('Limit', digits_compute=dp.get_precision('Account'), required="1"),
            'company_id' : fields.many2one('res.company', 'Company TR'),
            'account_id': fields.many2one('account.account', 'Related Account')
                }
tr_model()


class tr_details(osv.osv):
    _name = 'tr.details'
    _description = 'TR Details'
    
#     def function_add_tr_details(self, cr, uid, context=None):
#         cr.execute('SELECT id FROM tr_details')
#         res = cr.fetchall()
#         count = 1
#         settle_wizard_pool = self.pool.get('settle.tr.wizard')
#         for data in res:
#             id = data[0]
#             tr_obj = self.pool.get('tr.details').browse(cr, uid, id)
#             if tr_obj.settle_voucher_id and tr_obj.changed_settlement==False:
#                 settle_vals = {
#                            'date': tr_obj.settle_date,
#                            'amount': tr_obj.amt_cleared,
#                            'name': tr_obj.settle_note or '',
#                            'voucher_id': tr_obj.settle_voucher_id.id,
#                            'tr_id': id
#                            }
#                 wizard_id = settle_wizard_pool.create(cr, uid, settle_vals, context=context)
#                 settle_wizard_pool.settle_tr(cr, uid, [wizard_id], context=context)
#                 print "_____tr_obj.amt_cleared>>>", tr_obj.amt_cleared,"<<< --------tr_obj.amount ",tr_obj.amount, "_tr_obj.settle_voucher_id.id_",tr_obj.settle_voucher_id.id
#                 if tr_obj.amount_total < tr_obj.amount :
#                     print "________INNNNNN IFFFFFFFF"
#                     tr_obj.write({'state': 'open'})
#                 print '\n\n'
#             tr_obj.write({'changed_settlement':True})
#         return True

    
#     def _next_payment_date(self, cr, uid, ids, name, args, context=None):
#         res = {}
#         for tr in self.browse(cr, uid, ids, context=context):
#             next_payment_date = 0
#             start_date = datetime.strptime(tr.start_date, '%Y-%m-%d').date()
#             close_date = datetime.strptime(tr.closing_date, '%Y-%m-%d').date()
#             next_payment_date = start_date + relativedelta(months=+int(tr.repayment_interval))
#             if next_payment_date <= close_date:
#                 res[tr.id] = str(next_payment_date)
#             else:
#                 res[tr.id] = ""
#         return res
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        if context is None:
            context = {}
        default.update({'started_settlement': False, 'settle_ids': False})
        return super(tr_details, self).copy(cr, uid, id, default, context)
    
    def onchange_start_date(self, cr, uid, ids, start_date, duration, context=None):
        date = parser.parse(start_date)
        close_date = date + relativedelta(days=+duration)
        return {
                    'value':{'closing_date': str(close_date.date())}
                    }
    
    def action_confirm(self, cr, uid, ids, context=None):
        for tr in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, tr.id, {'state' : 'open'}, context=context)
        return True
    
    def action_settle(self, cr, uid, ids, context=None):
        tr_obj = self.browse(cr, uid, ids, context=context)
        for tr in tr_obj:
            self.write(cr, uid, tr.id, {'state' : 'settle'}, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        tr_obj = self.browse(cr, uid, ids, context=context)
        for tr in tr_obj:
            self.write(cr, uid, tr.id, {'state' : 'cancel'}, context=context)
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        tr_obj = self.browse(cr, uid, ids, context=context)
        for tr in tr_obj:
            self.write(cr, uid, tr.id, {'state' : 'draft'}, context=context)
        return True
    
    def action_notification_mail(self, cr, uid, context=None):
        context = context or {}
        current_date = datetime.today().date()
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hatta_account',
                            'tr_details_cron_email_template')[1]
        tr_ids = self.search(cr, uid, [('state', 'in', ['open'])], context=context)
        if tr_ids:
            for tr in self.browse(cr, uid, tr_ids, context=context):
                next_date = (datetime.strptime(tr.closing_date, '%Y-%m-%d')).date()
                notify_date = current_date + relativedelta(days=tr.notify_before)
                if notify_date == next_date:
                    self.pool.get('email.template').send_mail(cr, uid, template_id, tr.id,
                            force_send=True, context=context)
        return True
    
    def _get_final_interest(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for tr in self.browse(cr, uid, ids, context=context):
            if tr.state == 'settle':
                res[tr.id] = {
                          'final_interest': 0.0,
                          'interest_today': 0.0,
                          }
            else:
                start_date = datetime.strptime(tr.start_date, "%Y-%m-%d")
                today = datetime.today()
                end_date = datetime.strptime(tr.closing_date, "%Y-%m-%d")
                final_days = (end_date - start_date).days
                days_today = (today - start_date).days
                print final_days,"------------>Final"
                print days_today,"----------->Today"
                int_rate = tr.interest_rate/ 100.00
                priciple = tr.amount or 0.00
                res[tr.id] = {
                              'final_interest': (priciple * (1.00 + (int_rate * (final_days / 365.00)))) - priciple,
                              'interest_today': (priciple * (1.00 + (int_rate * (days_today / 365.00)))) - priciple,
                              }
        return res
    
    def get_tr_amount(self, cr, uid, state=[], tr_id = False, context=None):
        domain = [('state', 'in', state)]
        if tr_id:
            domain.append(('tr_model_id', '=', tr_id))
        tr_ids = self.search(cr, uid, domain, context=context)
        amount = 0.00
        for tr in self.browse(cr, uid, tr_ids, context=context):
            if tr.started_settlement and len(state) == 1:
                amount += tr.amount - tr.amount_total
            else:
                amount += tr.amount
        return amount
    
    def get_tr_amount_settle(self, cr, uid, state=[], tr_id = False, context=None):
        domain = ['|',('state', '=', 'settle'),('state', '=', 'open'),('started_settlement','=',True)]
        if tr_id:
            domain.append(('tr_model_id', '=', tr_id))
        tr_ids = self.search(cr, uid, domain, context=context)
        amount = 0.00
        for tr in self.browse(cr, uid, tr_ids, context=context):
            if tr.state == 'settle':
                amount += tr.amount
            else:
                amount += tr.amount_total
        return amount
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for tr in self.browse(cr, uid, ids, context=context):
            total = 0.0
            res[tr.id] = {
                'amount_total': 0.0,
                'due_amount': 0.0,
            }
            for settle_obj in tr.settle_ids:
                if settle_obj.state == 'posted':
                    total += settle_obj.amt_cleared
            res[tr.id]['amount_total'] = total
            if tr.amount - total >= 0:
                res[tr.id]['due_amount'] = tr.amount - total
            else:
                res[tr.id]['due_amount'] = 0.0
        return res
    
    def _get_settle_details(self, cr, uid, ids, context=None):
        result = {}
        for settle_obj in self.pool.get('tr.settle.details').browse(cr, uid, ids, context=context):
            result[settle_obj.tr_details_id.id] = True
        return result.keys()
    
    _columns = {
        'name' : fields.char('TR Number', required="1",
                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'amount' : fields.float('Amount', required="1", digits_compute=dp.get_precision('Account'),
                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'interest_rate' : fields.float('Interest Rate',required="1", digits=(3,2),
                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'duration' : fields.float('Duration (Days)',required="1", digits=(2,2),
                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'start_date' : fields.date('Start Date', required="1",
                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'closing_date' : fields.date('Closing Date', required="1",
                        readonly=True, states={'draft': [('readonly', False)]}),
                
#         'repayment_interval' : fields.float('Repayment Interval(months)',required="1", digits=(2,2),
#                         readonly=True, states={'draft': [('readonly', False)]}),
                
#         'next_payment_date' : fields.function(_next_payment_date, string='Next Payment Date', type="date",
#                         readonly=True),
                
        'notify_before' : fields.integer('Notify Before(days)', required="1",
                        readonly=True, states={'draft': [('readonly', False)]}),
                
        'state' : fields.selection([('draft', 'Draft'), ('open', 'Open'), ('settle', 'Settled'),
                                    ('cancel', 'Cancelled'), ('close', 'Closed')], 'State'),
        'note': fields.text('Purpose'),
        'final_interest': fields.function(_get_final_interest, type="float",
                                          string="Interest as on Closing Date", multi="interest"),
        'interest_today': fields.function(_get_final_interest, type="float",
                                          string="Interest as on Today", multi="interest"),
        'amt_cleared': fields.float('Amount Cleared', digits_compute=dp.get_precision('Account')),
        'voucher_id': fields.many2one('account.move', 'Related Voucher',
                                      readonly=True, states={'draft': [('readonly', False)]}),
        'settle_voucher_id': fields.many2one('account.move', 'Settlement Voucher'),
        'settle_date': fields.date('Settlement Date'),
        'settle_note': fields.text('Settlement Note'),
        'tr_model_id' : fields.many2one('tr.model', 'Related TR', readonly=True, states={'draft': [('readonly', False)]}),
        'settle_ids':  fields.one2many('tr.settle.details', 'tr_details_id', 'Settlement Lines'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            multi='sums', help="The total amount."),
        'due_amount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            multi='sums', help="The total amount."),
        'started_settlement': fields.boolean('Started Settlement'),
        'changed_settlement': fields.boolean('Changed Settlement Data?',)
        }
    
    _defaults = {
        'state': 'draft',
                }
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True

tr_details()

class tr_settle_details(osv.osv):
    _name = 'tr.settle.details'
    _description = 'Settlement Details'
    
    def _get_state(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for settle_obj in self.browse(cr, uid, ids, context):
            if settle_obj.settle_voucher_id:
                res[settle_obj.id] = settle_obj.settle_voucher_id.state
        return res
    
    def _get_move(self, cr, uid, ids, context=None):
        result = {}
        for settle_obj in self.pool.get('tr.settle.details').browse(cr, uid, ids, context=context):
            result[settle_obj.settle_voucher_id.id] = True
        return result.keys()
    
    _columns = {
        'tr_details_id': fields.many2one('tr.details', 'TR Details'),
        'amt_cleared': fields.float('Amount Cleared', digits_compute=dp.get_precision('Account')),
        'settle_date': fields.date('Settlement Date'),
        'settle_note': fields.text('Settlement Note'),
        'settle_voucher_id': fields.many2one('account.move', 'Settlement Voucher'),
        'state': fields.related('settle_voucher_id', 'state',  
                                string="Voucher Status", readonly=True, required=True, type='selection', 
                                selection=[('draft','Unposted'), ('posted','Posted')]),
    }
tr_settle_details()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

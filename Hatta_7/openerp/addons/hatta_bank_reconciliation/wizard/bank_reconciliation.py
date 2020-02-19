# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 ZestyBeanz Technologies Pvt. Ltd.
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

from datetime import datetime
import openerp.addons.decimal_precision as dp
from tools.translate import _

class bank_reconsiliation(osv.osv_memory):
    _name = 'bank.reconciliation'
    _description = 'Bank Reconciliation'
    _columns = {
                'from_date': fields.date('Date From'),
                'to_date': fields.date('Date To'),
                'bank_account_id': fields.many2one('account.account', 'Bank Account',
                                                   domain="[('user_type.code', '=', 'bank')]"),
                'line_ids': fields.one2many('bank.reconciliation.line', 'rec_id', 'Bank Reconciliation Line'),
                'type': fields.selection([('reconciled', 'Reconciled'),
                                          ('un_recon', 'To Reconcile'),
                                          ('all', 'All')], 'Show Only')
                }
    _defaults = {
                 'type': 'un_recon'
                 }
    
    def update_record(self, cr, uid, ids, context=None):
        move_line_pool = self.pool.get('account.move.line')
        line_pool = self.pool.get('bank.reconciliation.line')
        for record in self.browse(cr, uid, ids, context=context):
            from_date = record.from_date
            to_date = record.to_date
            type = record.type
            bank_account_id = record.bank_account_id.id
            ext_line_ids = [x.id for x in record.line_ids]
            line_pool.unlink(cr, uid, ext_line_ids, context=context)
            domain = [('move_id.state', '=', 'posted'),
                      ('account_id', '=', bank_account_id),
                      ('date', '>=', from_date),
                      ('date', '<=', to_date)]
            if type == 'reconciled':
                domain.append(('rec_date', '!=', False))
            elif type == 'un_recon':
                domain.append(('rec_date', '=', False))
            move_line_ids = move_line_pool.search(cr, uid, domain, context=context)
            lines = []
            for move_line_obj in move_line_pool.browse(cr, uid, move_line_ids, context=context):
                debit = 0.00
                credit = 0.00
                if move_line_obj.amount_currency:
                    if move_line_obj.amount_currency < 0.00:
                        credit = move_line_obj.amount_currency * -1
                    else:
                        debit = move_line_obj.amount_currency
                else:
                    debit = move_line_obj.debit or 0.00
                    credit = move_line_obj.credit or 0.00
                vals = {
                        'rec_id': record.id,
                        'date': move_line_obj.date,
                        'remark': move_line_obj.name,
                        'move_id': move_line_obj.move_id.id,
                        'move_line_id': move_line_obj.id,
                        'rec_date': move_line_obj.rec_date,
                        'rec': move_line_obj.rec_date and True or False,
                        'ref': move_line_obj.move_id.cheque_no or '',
                        'debit': debit,
                        'credit': credit,
                        'bank_debit': move_line_obj.bank_debit,
                        'bank_credit': move_line_obj.bank_credit
                        }
                lines.append((0, 0, vals))
            record.write({'line_ids': lines})
        return True
    
    def execute(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            for line in record.line_ids:
                move_line_obj = line.move_line_id
                if line.rec_date and line.date > line.rec_date:
                    raise osv.except_osv(_("Error!!!"),
                                         _("Please check reconciliation date !!!!"))
                move_line_obj.write(
                                    {
                                     'rec_date': line.rec_date,
                                     'bank_credit': line.bank_credit,
                                     'bank_debit': line.bank_debit
                                     })
        self.update_record(cr, uid, ids, context=context)
        return True
    
bank_reconsiliation()

class bank_reconsiliation_line(osv.osv_memory):
    _name = 'bank.reconciliation.line'
    _description = 'Reconciliation Line'
    _order = 'date'
    
    def onchange_rec(self, cr, uid, ids, rec, date, debit, credit, context=None):
        res = {'value': {}}
        if rec:
            res['value']['rec_date'] = date or fields.date.today()
            res['value']['bank_debit'] = debit
            res['value']['bank_credit'] = credit
        else:
            res['value']['rec_date'] = False
            res['value']['bank_debit'] = 0.00
            res['value']['bank_credit'] = 0.00
        return res
    
    _columns = {
                'date': fields.date('Date'),
                'remark': fields.text('Remark'),
                'move_id': fields.many2one('account.move', 'Voucher'),
                'ref': fields.char('Ref', size=128),
                'move_line_id': fields.many2one('account.move.line', 'Move Line Ref'),
                'rec_date': fields.date('Reconciliation Date'),
                'rec': fields.boolean('Reconcile?'),
                'rec_id': fields.many2one('bank.reconciliation', 'Wizard Ref'),
                'credit': fields.float('Credit', digits_compute=dp.get_precision('Account')),
                'debit': fields.float('Debit', digits_compute=dp.get_precision('Account')),
                'bank_credit': fields.float('Bank Credit', digits_compute=dp.get_precision('Account')),
                'bank_debit': fields.float('Bank Debit', digits_compute=dp.get_precision('Account'))
                }
bank_reconsiliation_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

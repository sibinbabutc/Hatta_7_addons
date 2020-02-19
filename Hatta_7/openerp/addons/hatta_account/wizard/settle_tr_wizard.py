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

import openerp.addons.decimal_precision as dp
import time

class settle_tr_wizard(osv.osv_memory):
    _name = 'settle.tr.wizard'
    _description = 'Settle TR Wizard'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        tr_pool = self.pool.get('tr.details')
        res = super(settle_tr_wizard, self).default_get(cr, uid, fields, context=context)
        tr_id = context.get('active_id', False)
        if tr_id:
            tr_obj = tr_pool.browse(cr, uid, tr_id, context=context)
            res['amount'] = tr_obj.amount - tr_obj.amount_total or 0.0
            res['tr_id'] = tr_id
        return res
    
    _columns = {
                'name': fields.text('Settlement Note'),
                'voucher_id': fields.many2one('account.move', 'Related Settlement Voucher'),
                'amount': fields.float('Settlement Amount', digits_compute=dp.get_precision('Account')),
                'date': fields.date('Settlement Date'),
                'tr_id': fields.many2one('tr.details', 'Related TR')
                }
    _defaults = {
                 'date': lambda*a:time.strftime("%Y-%m-%d")
                 }
    
    def settle_tr(self, cr, uid, ids, context=None):
        settle_details_pool = self.pool.get('tr.settle.details')
        for data in self.browse(cr, uid, ids, context=context):
            tr_obj = data.tr_id
            settle_ids = settle_details_pool.search(cr, uid, [('tr_details_id','=',tr_obj.id),('settle_voucher_id','=',data.voucher_id.id),
                                                 ('settle_date','=',data.date)])
            if settle_ids:
                settle_id = settle_ids and settle_ids[0]
                settle_obj = settle_details_pool.browse(cr, uid, settle_id, context=context)
                amt_cleared = settle_obj.amt_cleared + data.amount or 0.00
                settle_details_pool.write(cr, uid, settle_ids, {'amt_cleared': amt_cleared}, context=context)
            else:
                vals = {
                        'amt_cleared': data.amount or 0.00,
                        'settle_voucher_id': data.voucher_id and data.voucher_id.id or False,
                        'settle_date': data.date,
                        'settle_note': data.name or '',
                        'tr_details_id': tr_obj.id
                        }
                settle_id = settle_details_pool.create(cr, uid, vals, context=context)
            tr_obj.write({'started_settlement': True})
            if tr_obj.amount_total >= tr_obj.amount:
                tr_obj.action_settle()
        return True
    
settle_tr_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

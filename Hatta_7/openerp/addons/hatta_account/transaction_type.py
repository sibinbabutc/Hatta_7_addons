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

class transaction_type(osv.osv):
    _name = 'transaction.type'
    _description = 'Transaction Type'
    
    def _check_model(self, cr, uid, ids, name, args, context=None):
        res = {}
        trans_list = self.browse(cr, uid, ids, context=context)
        for trans in trans_list:
            if trans.model_id.model == "purchase.order":
                res[trans.id] = True
            else:
                res[trans.id] = False
        return res
    
    _columns = {
                'name': fields.char('Name', size=128),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'sequence_id': fields.many2one('ir.sequence', 'Sequence'),
                'user_ids': fields.many2many('res.users', 'user_tran_type_rel', 'tran_id', 'user_id',
                                             'User(s)'),
                'refund': fields.boolean('Return ?'),
                'model_id': fields.many2one('ir.model', 'Groups'),
                'partner_seq': fields.boolean('Partner Based Seq. Sufix'),
                'direct_purchase': fields.boolean('Direct Purchase ?'),
                'direct_invoice': fields.boolean('Direct Invoice ?'),
                'track_revision': fields.boolean('Track Revision ?'),
                'check_model' : fields.function(_check_model, string='Check Model', type='boolean'),
                'local_purchase' : fields.boolean('Local Purchase'),
                }
    
transaction_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

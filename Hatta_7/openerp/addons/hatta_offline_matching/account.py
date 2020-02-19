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

from osv import osv, fields, expression

from tools.translate import _
import re

class account_move(osv.osv):
    _inherit = 'account.move'
    
    def hatta_vou_button_cancel(self, cr, uid, ids, context=None):
        voucher_line_pool = self.pool.get('account.voucher.line')
        voucher_pool = self.pool.get('account.voucher')
        cancel_voucher = []
        for move in self.browse(cr, uid, ids, context=context):
            for line in move.line_id:
                voucher_line_ids = voucher_line_pool.search(cr, uid, [('voucher_id.state', '=', 'posted'),
                                                                      ('move_line_id', '=', line.id)],
                                                            context=context)
                voucher_line_objs = voucher_line_pool.browse(cr, uid, voucher_line_ids, context=context)
                voucher_ids = [x.voucher_id.id for x in voucher_line_objs]
                cancel_voucher.extend(voucher_ids)
        if cancel_voucher:
            cancel_voucher = list(set(cancel_voucher))
            voucher_pool.cancel_voucher(cr, uid, cancel_voucher, context=context)
            voucher_pool.unlink(cr, uid, cancel_voucher, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            for line in move.line_id:
                if line.reconcile_id or line.reconcile_partial_id and not line.voucher_id:
                    raise osv.except_osv(_("Error!!!"),
                                         _("Matching already done for this voucher. Please unmatch before proceeding !!!"))
        res = self.button_cancel(cr, uid, ids, context=context)
        return res
    
account_move()

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def name_get(self, cr, user, ids, context=None):
        result = []
        def _name_get(d):
            number = d.get('number','')
            ref = d.get('ref',False)
            if ref:
                name = '[%s] %s' % (number, ref)
            return (d['id'], name)
        for voucher in self.browse(cr, user, ids, context=context):
            mydict = {
                      'number': voucher.number,
                      'ref': voucher.reference,
                      'id': voucher.id
                      }
            result.append(_name_get(mydict))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            ids = []
            if operator in positive_operators:
                ids = self.search(cr, user, [('number','=',name)]+ args, limit=limit, context=context)
#                 if not ids:
#                     ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('number',operator,name)],
                                       limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('reference',operator,name), ('id', 'not in', list(ids))], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
            elif not ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                ids = self.search(cr, user, args + ['&', ('reference', operator, name),
                                                    ('number', operator, name)], limit=limit, context=context)
            if not ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('number','=', res.group(2))] + args,
                                      limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

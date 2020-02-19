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

import re
from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    def onchange_partner_name(self, cr, uid, ids, name, context=None):
        res = {'value': {}}
        partner_pool = self.pool.get('res.partner')
        if name:
            name1 = name.replace(".", " ")
            name2 = name.replace(" ", '.')
            name3 = name.replace(".", "")
            name4 = name.replace(",", "")
            name5 = name.replace(",", ".")
            name6 = name.replace(",", " ")
            partner_ids = partner_pool.search(cr, uid, ['|', '|', '|', '|', '|', ('name', 'ilike', name1),
                                                        ('name', 'ilike', name2), ('name', 'ilike', name3),
                                                        ('name', 'ilike', name4), ('name', 'ilike', name5),
                                                        ('name', 'ilike', name6)],
                                              context=context)
            if partner_ids:
                partner_name_list = []
                for partner_obj in partner_pool.browse(cr, uid, partner_ids, context=context):
                    partner_name_list.append(partner_obj.name)
                warning = {
                    'title': _('Warning!!!'),
                    'message': _('ACCOUNT HAVING SIMILAR NAME ALREADY EXIST. PLEASE CHECK BELOW:\n%s'%('\n'.join(partner_name_list)))
                }
                res['warning'] = warning
        return res
    
    def _check_ac_code(self, cr, uid, ids, context=None):
        for partner_obj in self.browse(cr, uid, ids, context=context):
            partner_ac_code = partner_obj.partner_ac_code
            if partner_ac_code:
                partner_ids = self.search(cr, uid, [('partner_ac_code', '=', partner_ac_code),
                                                    ('id', 'not in', ids)], context=context)
                if partner_ids:
                    return False
        return True
    
    _columns = {
                'partner_ac_code': fields.char('Subledger Code', size=128),
                'analytic_account_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'seq_id': fields.many2one('ir.sequence', 'Sequence'),
                'partner_nick_name': fields.char('Partner Abb.', size=32),
                'upload_invoice' : fields.boolean('Upload Invoice to Customer site?')
                }
    _defaults = {
                 'supplier': True,
                 'customer': False
                 }
#     _sql_constraints = [
#         ('partner_ac_code_uniq', 'unique(partner_ac_code)', 'Partner Account Code already exists!'),
#     ]
    _constraints = [
        (_check_ac_code, 'Partner subledger code already exists !!!', ['chart_account_id','fiscalyear_id','period_from','period_to']),
    ]
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            name1 = name.replace(".", " ")
            name2 = name.replace(" ", '.')
            name3 = name.replace(".", "")
            name4 = name.replace(",", "")
            name5 = name.replace(",", ".")
            name6 = name.replace(",", " ")
            ids = self.search(cr, user, [('partner_ac_code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('partner_ac_code',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('partner_ac_code','=', res.group(2))] + args, limit=limit, context=context)
            new_ids = self.search(cr, user, args + ['|', '|', '|', '|', '|', ('name', 'ilike', name1),
                                            ('name', 'ilike', name2), ('name', 'ilike', name3),
                                            ('name', 'ilike', name4), ('name', 'ilike', name5),
                                            ('name', 'ilike', name6), ('id', 'not in', ids)],
                                  context=context)
            ids.extend(new_ids)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

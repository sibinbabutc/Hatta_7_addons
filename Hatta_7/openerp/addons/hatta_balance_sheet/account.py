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

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def _query_get(self, cr, uid, obj='l', context=None):
        if context is None:
            context = {}
        
        res = super(account_move_line, self)._query_get(cr, uid, obj, context=context)
        if context.get('ann_account_ids', False):
            if len(context['ann_account_ids']) == 1:
                res += ' AND '+obj+'.analytic_account_id = %s' % context['ann_account_ids'][0]
            else:
                res += ' AND '+obj+'.analytic_account_id in %s' % str(tuple(context['ann_account_ids']))
        return res

account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

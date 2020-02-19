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

class exp_additional_exp(osv.osv_memory):
    _name = 'expense.additional.info'
    _description = 'Additional Info'
    
    def default_get(self, cr, uid, field_names, context=None):
        if context is None:
            context = {}
        exp_pool = self.pool.get('pol.landing.cost')
        res = super(exp_additional_exp, self).default_get(cr, uid, field_names, context=context)
        print context
        active_id = context.get('active_id', False)
        if active_id:
            exp_obj = exp_pool.browse(cr, uid, active_id, context=context)
            res['info'] = exp_obj.info or ''
            res['exp_id'] = exp_obj.id
        return res
    
    _columns = {
                'exp_id': fields.many2one('pol.landing.cost', 'Expense Ref#'),
                'info': fields.text('Additional Info')
                }
    
    def add_note(self, cr, uid, ids, context=None):
        exp_pool = self.pool.get('pol.landing.cost')
        data = self.read(cr, uid, ids, context={})[0]
        info = data.get('info', '')
        exp_id = data.get('exp_id', '')
        exp_pool.write(cr, uid, exp_id[0], {'info': info}, context=context)
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
    
exp_additional_exp()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

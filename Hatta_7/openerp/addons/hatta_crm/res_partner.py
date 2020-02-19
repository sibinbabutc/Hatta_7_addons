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

from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    _columns = {
        'trn_code': fields.char('TRN Code')
    }
    
    def create(self, cr, uid, vals, context=None):
        user_pool = self.pool.get('res.users')
        cust_group_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hatta_crm',
                                                                            'group_cust_cr')[1]
        if vals.get('customer', False):
            user_obj = user_pool.browse(cr, uid, uid, context=context)
            user_group_ids = [x.id for x in user_obj.groups_id]
            if not cust_group_id in user_group_ids:
                raise osv.except_osv(_("Error !!!"),
                                     _("You are not allowed to create customers.\nPlease contact administrator !!!"))
        res = super(res_partner, self).create(cr, uid, vals, context=context)
        return res
    
res_partner()

class res_company(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'trn_code': fields.char('TRN Code')
    }

res_company()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

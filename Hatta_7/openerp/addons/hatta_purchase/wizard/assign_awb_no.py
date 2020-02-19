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

class assign_awb_no(osv.osv_memory):
    _name = 'assign.awb.no'
    _description = 'Assign AWB No'
    
    _columns = {
                'awb' : fields.char(string='AWB #', size=128),
        }
    
    def assign_awb_no(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        shipping_pool = self.pool.get('shipping.quotation')
        active_id = context.get('active_id', False)
        shipping_obj = shipping_pool.browse(cr, uid, active_id, context=context)
        for wizard in self.browse(cr, uid, ids, context=context):
            shipping_obj.write({'awb': wizard.awb or False})
        return True
    
assign_awb_no()
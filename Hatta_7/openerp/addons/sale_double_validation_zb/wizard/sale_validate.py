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

from openerp.osv import fields, osv

from openerp import netsvc
from openerp.tools.translate import _

class sale_validate(osv.osv_memory):
    _name = 'sale.validate'
    
    def validate_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wf_service = netsvc.LocalService('workflow')
        sale_ids = context.get('active_ids', [])
        sale_pool = self.pool.get('sale.order')
        for sale_obj in sale_pool.browse(cr, uid, sale_ids, context=context):
            if not sale_obj.can_approve:
                raise osv.except_osv(_('Error !!'), \
                                     _('You Dont have permission to approve this sale order'))
            if sale_obj.state == 'wait_for_approval':
                wf_service.trg_validate(uid, 'sale.order', \
                                        sale_obj.id, 'validate_order', cr)
            else:
                raise osv.except_osv(_('Error !!'), \
                                     _('Sale should be in state Waiting For Approval'))
        return True
    
sale_validate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

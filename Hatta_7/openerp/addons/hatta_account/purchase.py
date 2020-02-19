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

from tools.translate import _

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
                'job_id': fields.many2one('job.account', 'Job No.'),
                'supplier_invoice_date': fields.date('Supplier Invoice Date'),
                }
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(purchase_order, self)._prepare_order_picking(cr, uid, order, context=context)
        if not order.job_id and (order.lead_id or order.direct_sale_id):
            raise osv.except_osv(_("Error!!!"),
                                 _("No Job number assigned!!!"))
        res['cost_center_id'] = order.analytic_account_id and order.analytic_account_id.id or False
        res['job_id'] = order.job_id and order.job_id.id or False
        return res
    
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

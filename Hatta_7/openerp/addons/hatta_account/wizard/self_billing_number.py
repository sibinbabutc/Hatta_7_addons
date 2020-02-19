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

class self_billing_number(osv.osv_memory):
    _name = 'self.billing.number'
    _description = 'Self Billing number Addition'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        invoice_pool = self.pool.get('account.invoice')
        res = super(self_billing_number, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            res['invoice_id'] = active_id
            inv_obj = invoice_pool.browse(cr, uid, active_id, context=context)
            res['billing_number'] = inv_obj.self_billing_num or ''
        return res
    
    _columns = {
                'invoice_id': fields.many2one('account.invoice', 'Invoice'),
                'billing_number': fields.char('Self Billing Number', size=128)
                }
    
    def assign_number(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        data = self.read(cr, uid, ids, context={})[0]
        invoice_data = data.get('invoice_id', False)
        if not invoice_data:
            raise osv.except_osv(_("Error!!!"),
                                 _("Unable to assign billing number.\nPlease Contact Administrator!!!"))
        invoice_id = invoice_data[0]
        number = data.get('billing_number', '')
        if not number:
            raise osv.except_osv(_("Error!!!"),
                                 _("Invalid Billing Number!!!"))
        invoice_pool.assign_billing_number(cr, uid, invoice_id, number, context=context)
        return True
    
self_billing_number()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from openerp import netsvc

class wizard_invoice_upload(osv.osv_memory):
    _name = 'wizard.invoice.upload'
    _description = 'Invoice Uploaded to Customer?'
    
    def uploaded_invoice(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        for invoice in invoice_pool.browse(cr, uid, [context['active_id']], context=context):
            if context.get('validate'):
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_proforma2', cr)
                invoice_pool.write(cr, uid, [context['active_id']], {'invoice_uploaded':True}, context=context)
            elif context.get('post'):
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
                invoice_pool.write(cr, uid, [context['active_id']], {'invoice_uploaded':True}, context=context)
        return True
    
    def not_uploaded(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        for invoice in invoice_pool.browse(cr, uid, [context['active_id']], context=context):
            if context.get('validate'):
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_proforma2', cr)
                invoice_pool.write(cr, uid, [context['active_id']], {'invoice_uploaded':False}, context=context)
            elif context.get('post'):
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
                invoice_pool.write(cr, uid, [context['active_id']], {'invoice_uploaded':False}, context=context)
        return True
   
    
wizard_invoice_upload()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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

class invoice_upload_wizard(osv.osv_memory):
    _name = 'invoice.upload.wizard'
    _description = 'Invoice Uploaded to Customer?'
    _columns = {
                'validate': fields.boolean('Validate'),
                'post': fields.boolean('Post'),
                'invoice_id': fields.many2one('account.invoice', 'Invoice')
                }
    
    def invoice_uploaded(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice_pool = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        active_id = context.get('active_id', False)
        if active_id:
            wiz = self.browse(cr, uid, ids[0], context=context)
            invoice = wiz.invoice_id or False
            if wiz.validate:
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_proforma2', cr)
                invoice.write({'invoice_uploaded': True})
            elif wiz.post:
                invoice.write({'invoice_uploaded': True})
                ctx = context.copy()
                ctx['from_wizard'] = True
                invoice_pool.invoice_open(cr, uid, [invoice.id], context=ctx)
        return True
    
    def invoice_not_uploaded(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice_pool = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        active_id = context.get('active_id', False)
        print context
        if active_id:
            wiz = self.browse(cr, uid, ids[0], context=context)
            invoice = wiz.invoice_id or False
            if wiz.validate:
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_proforma2', cr)
                invoice.write({'invoice_uploaded': False})
            elif wiz.post:
                invoice.write({'invoice_uploaded': False})
                ctx = context.copy()
                ctx['from_wizard'] = True
                invoice_pool.invoice_open(cr, uid, [invoice.id], context=ctx)
        return True
   
    
invoice_upload_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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

from openerp import netsvc

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def _get_invoice(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        invoice_ids = invoice_pool.search(cr, uid, [('move_id', 'in', ids)],
                                          context=context)
        return invoice_ids
    
    def _get_invoice_number(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice_obj in self.browse(cr, uid, ids, context=context):
            if invoice_obj.internal_number:
                res[invoice_obj.id] = invoice_obj.internal_number
            else:
                res[invoice_obj.id] = invoice_obj.move_id and invoice_obj.move_id.name or False
        return res
    
    def _get_validate_condtn(self, cr, uid, ids, fields, args, context=None):
        res = {}
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hatta_invoice_double_validation', 'group_direct_validate')
        if view_id:
            for invoice in self.browse(cr, uid, ids, context=context):
                user_ids = self.pool.get('res.users').search(cr, uid, [('id', '=', uid), ('groups_id', '=', view_id[1])], context = context)
                if not user_ids:
                    if invoice.state == 'draft':
                        if invoice.upload_inv == False:
                            res[invoice.id] = True
                        else:
                            res[invoice.id] = False
                    else:
                        res[invoice.id] = False
                else:
                    res[invoice.id] = False
        return res
    
    def _get_post_condtn(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state == 'proforma2':
                if invoice.upload_inv == False:
                    res[invoice.id] = True
                else:
                    res[invoice.id] = False
            else:
                res[invoice.id] = False
        return res
    
    def _get_valid_condtn(self, cr, uid, ids, fields, args, context=None):
        res = {}
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hatta_invoice_double_validation', 'group_direct_validate')
        if view_id:
            for invoice in self.browse(cr, uid, ids, context=context):
                user_ids = self.pool.get('res.users').search(cr, uid, [('id', '=', uid), ('groups_id', '=', view_id[1])], context = context)
                if not user_ids:
                    if invoice.state == 'draft':
                        if invoice.upload_inv == True:
                            res[invoice.id] = True
                        else:
                            res[invoice.id] = False
                    else:
                        res[invoice.id] = False
                else:
                    res[invoice.id] = False
        return res
    
    def _get_condtn_post(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state == 'proforma2':
                if invoice.upload_inv == True:
                    res[invoice.id] = True
                else:
                    res[invoice.id] = False
            else:
                res[invoice.id] = False
        return res
    
    _columns = {
                'number': fields.function(_get_invoice_number, type="char", size=64,
                                          string="Number",
                                          store={
                                                 'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['internal_number', 'move_id'], 20),
                                                 'account.move': (_get_invoice, ['name'], 20),
                                                }),
#                 'number': fields.related('move_id','name', type='char', readonly=True, size=64,
#                                          relation='account.move', store=True, string='Number'),
                'validate_condtn' : fields.function(_get_validate_condtn, type="boolean", string="Condition"),
                'post_condtn' : fields.function(_get_post_condtn, type="boolean", string="Condition"),
                'valid_condtn' : fields.function(_get_valid_condtn, type="boolean", string="Condition"),
                'condtn_post' : fields.function(_get_condtn_post, type="boolean", string="Condition"),

                'state': fields.selection([
                                           ('draft','Draft'),
                                           ('proforma','Pro-forma'),
                                           ('proforma2','Unposted'),
                                           ('open','Posted'),
                                           ('paid','Paid'),
                                           ('cancel','Cancelled'),
                                           ],'Status', select=True, readonly=True, track_visibility='onchange',
                                          help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
                                            \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
                                            \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
                                            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
                                            \n* The \'Cancelled\' status is used when user cancel invoice.'),
                }
    
    def invoice_open(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for invoice_id in ids:
            wf_service.trg_validate(uid, 'account.invoice', \
                                    invoice_id, 'invoice_open', cr)
        return True
    
#     def invoice_validate(self, cr, uid, ids, context=None):
#         for invoice in self.browse(cr, uid, ids, context=context):
#             self.write(cr, uid, ids, {'state':'proforma2'}, context=context)
#         return True
#     
#     def invoice_post(self, cr, uid, ids, context=None):
#         for invoice in self.browse(cr, uid, ids, context=context):
#             self.write(cr, uid, ids, {'state':'open'}, context=context)
#         return True
    
account_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

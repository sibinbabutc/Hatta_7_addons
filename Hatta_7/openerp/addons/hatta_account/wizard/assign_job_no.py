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
from openerp import netsvc, SUPERUSER_ID

class assign_job_no(osv.osv_memory):
    _name = 'assign.job.no'
    _description = 'Assign Job No'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        sale_pool = self.pool.get('sale.order')
        invoice_pool = self.pool.get('account.invoice')
        purchase_pool = self.pool.get('purchase.order')
        res = super(assign_job_no, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            if context.get('active_model', 'account.invoice') == 'sale.order':
                sale_obj = sale_pool.browse(cr, uid, active_id, context=context)
                res['sale_id'] = active_id
                res['job_id'] = sale_obj.job_id and sale_obj.job_id.id or False
                res['name'] = sale_obj.job_id and sale_obj.job_id.name or ''
            elif context.get('active_model', 'sale.order') == 'account.invoice':
                invoice_obj = invoice_pool.browse(cr, uid, active_id, context=context)
                res['invoice_id'] = active_id
                res['job_id'] = invoice_obj.job_id and invoice_obj.job_id.id or False
                res['name'] = invoice_obj.job_id and invoice_obj.job_id.name or ''
            elif context.get('active_model', '') == 'purchase.order':
                purchase_obj = purchase_pool.browse(cr, uid, active_id, context=context)
                res['purchase_id'] = active_id
                res['job_id'] = purchase_obj.manual_job_id and purchase_obj.manual_job_id.id or \
                                    purchase_obj.job_id and purchase_obj.job_id.id or False
                res['name'] = purchase_obj.manual_job_id and purchase_obj.manual_job_id.name or \
                                    purchase_obj.job_id and purchase_obj.job_id.name or ''
        return res
    
    _columns = {
                'name': fields.char('Job Number', size=128),
                'use_existing': fields.boolean('Use Existing ?'),
                'exist_job_id': fields.many2one('job.account', 'Job A/c'),
                'sale_id': fields.many2one('sale.order', 'Sale Order'),
                'job_id': fields.many2one('job.account', 'Job A/c'),
                'invoice_id': fields.many2one('account.invoice', 'Invoice'),
                'purchase_id': fields.many2one('purchase.order', 'Purchase Order')
                }
    
    def assign_job_no(self, cr, uid, ids, context=None):
        uid = SUPERUSER_ID
        job_pool = self.pool.get('job.account')
        sale_pool = self.pool.get('sale.order')
        invoice_pool = self.pool.get('account.invoice')
        purchase_pool = self.pool.get('purchase.order')
        data = self.read(cr, uid, ids, context={})[0]
        sale_data = data.get('sale_id', False)
        invoice_data = data.get('invoice_id', False)
        purchase_data = data.get('purchase_id', False)
        job_data = data.get('job_id', False)
        use_exist = data.get('use_existing', False)
        exist_job_id = data.get('exist_job_id', False)
        new_job_number = data.get('name', False)
        job_id = False
        if use_exist and exist_job_id:
            job_id = exist_job_id[0]
            job_name = exist_job_id[1]
            if job_name == '?':
                raise osv.except_osv(_("Error !!!"),
                                     _("Invalid Job Number !!!"))
        elif not use_exist and new_job_number and job_data:
            rewrite_job_name = job_data[1]
            if rewrite_job_name != new_job_number and rewrite_job_name != '?':
                raise osv.except_osv(_("Error !!!"),
                                     _("Cannot change account number. Please amend it from job master!!!"))
            job_pool.write(cr, uid, job_data[0], {'name': new_job_number}, context=context)
            job_id = job_data[0]
        elif not use_exist and new_job_number and not job_data:
            if new_job_number == '?':
                raise osv.except_osv(_("Error !!!"),
                                     _("Invalid Job Number !!!"))
            vals = {'name': new_job_number}
            job_id = job_pool.create(cr, uid, vals, context=context)
        if job_id:
            if sale_data:
                sale_id = sale_data[0]
                sale_pool.write(cr, uid, sale_id, {'job_id': job_id, 'job_assigned': True}, context=context)
            if invoice_data:
                invoice_id = invoice_data[0]
                invoice_pool.write(cr, uid, invoice_id, {'job_id': job_id}, context=context)
            if purchase_data:
                purchase_id = purchase_data[0]
                purchase_pool.write(cr, uid, purchase_id, {'manual_job_id': job_id}, context=context)
        else:
            raise osv.except_osv(_("Error !!!"),
                                 _("Unable to assign job number. Please contact administrator !!!"))
        
        
        
        
        
        
#         sale_vals = {}
#         job_id = False
#         if job_data and use_exist:
#             job_id = job_data[0]
#         if sale_data and job_data:
#             if use_exist and exist_job_id:
#                 sale_vals.update({'job_id': exist_job_id[0]})
#                 job_sale_ids = sale_pool.search(cr, uid, [('job_id', '=', job_id)])
#                 if not job_sale_ids:
#                     job_pool.unlink(cr, uid, job_id, context=context)
#             else:
#                 job_number = data.get('name', '?')
#                 if job_number == '?':
#                     raise osv.except_osv(_("Error !!!"),
#                                          _("Invalid Job Number !!!"))
#                 job_pool.write(cr, uid, job_id, {'name': job_number}, context=context)
#         if not job_data and not use_exist:
#             job_number = data.get('name', '?')
#             if job_number == '?':
#                 raise osv.except_osv(_("Error !!!"),
#                                      _("Invalid Job Number !!!"))
#             job_vals = {
#                         'name': job_number
#                         }
#             job_id = job_pool.create(cr, uid, job_vals, context=context)
#         if sale_data:
#             sale_id = sale_data[0]
#             sale_vals.update({'job_assigned': True})
#             sale_pool.write(cr, uid, sale_id, sale_vals, context=context)
#         if invoice_data and job_id:
#             invoice_id = invoice_data[0]
#             invoice_pool.write(cr, uid, invoice_id, {'job_id': job_id})
        return True
    
assign_job_no()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

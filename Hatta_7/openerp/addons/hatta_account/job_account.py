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

class job_account(osv.osv):
    _name = 'job.account'
    _description = 'Job Account'
    
    def _get_purchase_ids(self, cr, uid, ids, name, args, context):
        res = {}
        purchase_pool= self.pool.get('purchase.order')
        po_ids = purchase_pool.search(cr, uid, [('job_id', 'in', ids),
                                                ('state', 'not in', ['draft', 'bid', 'sent', 'cancel'])],
                                      context=context)
        for id in ids:
            po_ids = purchase_pool.search(cr, uid, [('job_id', '=', id),
                                                    ('state', 'not in', ['draft', 'bid', 'sent', 'cancel'])],
                                          context=context)
            res[id] = po_ids
        return res
    
    def _get_delivery_ids(self, cr, uid, ids, name, args, context=None):
        res = {}
        picking_pool = self.pool.get('stock.picking.out')
        for id in ids:
            picking_ids = picking_pool.search(cr, uid, [('job_id', '=', id),
                                                        ('state', '!=', 'cancel'),
                                                        ('type', '=', 'out')],
                                              context=context)
            res[id] = picking_ids
        return res
    
    def _check_name(self, cr, uid, ids, context=None):
        for job in self.browse(cr, uid, ids, context=context):
            if job.name and job.name != '?':
                job_name = job.name
                job_ids = self.search(cr, uid, [('name', '=', job_name),
                                                ('id', '!=', job.id)],
                                      context=context)
                if job_ids:
                    return False
        return True
    
    def _get_job_short(self, cr, uid, ids, name, args, context=None):
        res = {}
        for job in self.browse(cr, uid, ids, context=context):
            abb = ''
            if job.manual_job_description:
                res[job.id] = job.manual_job_description
                continue
            if job.partner_id:
                partner_name = job.partner_id.name.upper()
                if job.partner_id.partner_nick_name:
                    partner_name = job.partner_id.partner_nick_name
                abb += partner_name.upper()
            cu_po_list = []
            for sale in job.sale_ids:
                if sale.client_order_ref and sale.state != 'cancel':
                    cu_po_list.append(sale.client_order_ref)
            if cu_po_list:
                abb += "PO:"
                abb += ','.join(cu_po_list)
            res[job.id] = abb
        return res
    
    def _get_partner_name(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for job in self.browse(cr, uid, ids, context=context):
            customer_id = False
            for sale in job.sale_ids:
                customer_id = sale.partner_id.id
            res[job.id] = customer_id
        return res
    
    def _get_cust_po_num(self, cr, uid, ids, fields, args, context=None):
        res = {}
        po_list = []
        for job in self.browse(cr, uid, ids, context=context):
            po_list = [x.client_order_ref for x in job.sale_ids if x.state not in ['cancel'] and x.client_order_ref]
            res[job.id] = ','.join(po_list)
        return res
    
    _columns = {
                'name': fields.char('Name', size=128),
                'partner_id': fields.function(_get_partner_name, type="many2one",
                                              relation='res.partner',
                                              string="Customer"),
#                 'partner_id': fields.many2one('res.partner', 'Customer'),
                'supplier_ids': fields.many2many('res.partner', 'partner_job_rel', 'job_id', 'partner_id',
                                                 'Supplier(s)'),
                'sale_ids': fields.one2many('sale.order', 'job_id', 'Sale order(s)'),
                'purchase_ids': fields.function(_get_purchase_ids, type="many2many", relation="purchase.order",
                                                string="Purchase Order"),
                'picking_ids': fields.function(_get_delivery_ids, type="many2many", relation='stock.picking.out',
                                               string="Delivery Orders"),
                'invoice_ids': fields.one2many('account.invoice', 'job_id', 'Invoice(s)'),
                'move_line_ids': fields.one2many('account.move.line', 'job_id', 'Accounting Entries'),
                'lead_id': fields.many2one('crm.lead', 'Enquiry'),
                'job_short_desc': fields.function(_get_job_short, type="char", size=128,
                                                  string="Job Description"),
                'manual_job_description': fields.char('Manual Job Description', size=512),
                'cust_po_num': fields.function(_get_cust_po_num, type="char", size=128,
                                               string="Customer PO Number")
                }
    
    _constraints = [
        (_check_name, 'Job number already exist.', ['name']),
    ]
    
job_account()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

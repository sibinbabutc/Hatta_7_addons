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

class purchase_order_status(osv.osv_memory):
    _name = 'purchase.order.status'
    _description = 'Purchase Order Status Report'
    _columns = {
        'from_date' : fields.date('From Date', required=True),
        'to_date' : fields.date('To Date', required=True),
        'customer_id' : fields.many2one('res.partner', 'Customer'),       
        'job_id' : fields.many2one('job.account', "A/C #"),
        'rfq' : fields.char('RFQ #'),
        'closing_date_from' : fields.date('From Closing Date'),
        'closing_date_to' : fields.date('To Closing Date'),
        'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
        'supplier_id': fields.many2one('res.partner', 'Supplier')
                }
    
    def print_report(self, cr, uid, ids, context=None):
        data = {}
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        datas = {
            'title': 'Client Purchase Order Status Report',
            'from_date':data.from_date,
            'to_date':data.to_date,
            'customer_id':data.customer_id and data.customer_id.id or False,
            'job_id':data.job_id.name,
            'rfq':data.rfq,
            'closing_date_from':data.closing_date_from,
            'closing_date_to':data.closing_date_to,
            'transaction_type_id': data.transaction_type_id and data.transaction_type_id.id or False,
            'supplier_id': data.supplier_id and data.supplier_id.id or False
                }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'purchase_order_status_jasper',
            'datas': datas,
            'nodestroy' : True,
            'report_type': 'pdf'
            }
        return True
  
    
purchase_order_status()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

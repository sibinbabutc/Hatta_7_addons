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

class purchase_analysis_report(osv.osv_memory):
    _name = 'purchase.analysis.report'
    _description = 'Purchase Analysis Report'
    _columns = {
                'po_id': fields.many2one('purchase.order', 'Purchase Order'),
                'partner_id': fields.many2one('res.partner', 'Supplier'),
                'date_from': fields.date('Date From'),
                'date_to': fields.date('Date To'),
                'sort_supp': fields.boolean('Supplier Wise'),
                'pending_only': fields.boolean('Pending Only'),
                'sort_del_date': fields.boolean('Supplier Delivery Date'),
                'disp_cust_del_date': fields.boolean('Display Customer Delivery Date'),
                'cost_center_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'job_id': fields.many2one('job.account', 'A/C #'),
                }
    _defaults = {
                 'pending_only': True,
                 'sort_del_date': True
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context={})[0]
        datas = {'form': data}
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'po.status.jasper',
                'datas': datas,
                'nodestroy': True,
                }
    
purchase_analysis_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

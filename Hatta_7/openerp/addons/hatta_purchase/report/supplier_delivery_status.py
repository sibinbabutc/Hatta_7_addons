# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import pooler
from openerp import tools
from openerp.osv import fields,osv

def str_to_datetime(strdate):
    return datetime.strptime(strdate, tools.DEFAULT_SERVER_DATE_FORMAT)

class supplier_delivery_status(osv.osv):
    _name = "supplier.delivery.status"
    _description = "Supplier Delivery Status Report"
    _auto = False

    def delivery_status_check(self, cr, uid, ids, name, args, context=None):
        res={}
        current_date = datetime.today()
        for delivery in self.browse(cr, uid, ids, context=context):
            delivery_date = str_to_datetime(delivery.delivery_date)
            r = relativedelta(delivery_date, current_date)
            months = r.months
            if months <= 1 and months > 0:
                res[delivery.id] = 'one'
            elif months > 1:
                res[delivery.id] = 'two'
            else:
                res[delivery.id] = 'overdue'
        return res

    _columns = {
        'account_no' : fields.many2one('job.account', 'Account No.'),
        'delivery_date' : fields.date('Delivery Date'),
        'partner_id':fields.many2one('res.partner', 'Supplier', required=True),
        'name' : fields.char('PO Number', size=64, required=True),
        'po_remark': fields.text('PO Remark'),
        'delivery_status': fields.function(delivery_status_check, type='selection', string='Date Check',
                    selection= [('overdue','Overdue'),
                        ('one', 'One Month'),
                        ('two', 'Two Month')]),
        'purchase_id' : fields.many2one('purchase.order', 'Purchase')
                }
    _order = 'delivery_date'
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'supplier_delivery_status')
        cr.execute("""create or replace view supplier_delivery_status as (
            select
               po.id as id, po.job_id as account_no, po.minimum_planned_date as delivery_date,
               po.partner_id as partner_id, po.name as name,
               po.datasheet_remark as po_remark, 
               po.id as purchase_id
            from
                purchase_order po
            where po.state not in ('draft', 'cancel', 'bid', 'sent', 'done')
            order by po.minimum_planned_date
                
                )""")

supplier_delivery_status()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

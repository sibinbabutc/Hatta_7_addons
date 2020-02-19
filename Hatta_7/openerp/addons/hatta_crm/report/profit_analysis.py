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

from openerp import tools
from openerp.osv import fields, osv

class profit_analysis(osv.osv):
    _name = "profit.analysis"
    _description = "Sales Orders Profit Statistics"
    _auto = False
    _rec_name = 'date_order'
    _columns = {
                'default_code': fields.char('Product Code', size=64),
                'product_id': fields.many2one('product.product', 'Product'),
                'date_order': fields.date('Date Order'),
                'supplier_id': fields.many2one('res.partner', 'Supplier'),
                'customer_id': fields.many2one('res.partner', 'Customer'),
                'user_id': fields.many2one('res.users', 'Salesperson'),
                'job_id': fields.many2one('job.account', 'Job No.'),
                'our_ref': fields.many2one('purchase.order', 'Our Ref.'),
                'cust_ref': fields.char('Customer Ref.', size=128),
                'sale_price': fields.float('Sale Price'),
                'cost_price': fields.float('Cost Price'),
                'product_qty': fields.float('Quantity'),
                'year': fields.char('Year', size=4, readonly=True),
                'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                           ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                           ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
                'day': fields.char('Day', size=128, readonly=True),
                'margin': fields.float('Margin'),
                'profit': fields.char('Profit %', size=64)
                }
    _order = 'date_order desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'profit_analysis')
        cr.execute("""
            create or replace view profit_analysis as (select
    min(pol.id) as id,
    pp.default_code as default_code,
    pol.product_id as product_id,
    po.date_order as date_order,
    po.partner_id as supplier_id,
    so.partner_id as customer_id,
    po.job_id as job_id,
    po.name as our_ref,
    po.customer_rfq as cust_ref,
    po.validator as user_id,
    to_char(po.date_order, 'YYYY') as year,
        to_char(po.date_order, 'MM') as month,
        to_char(po.date_order, 'YYYY-MM-DD') as day,
    sum(COALESCE(pol.product_qty, 0.00) / u.factor * u2.factor) as product_qty,
    sum(COALESCE(sol.price_unit, 0.00) * COALESCE(sol.product_uom_qty, 0.00)) as sale_price,
    sum(COALESCE(pol.unit_price_lc, 0.00) * COALESCE(pol.product_qty, 0.00)) as cost_price,
    sum(COALESCE(sol.price_unit, 0.00) * COALESCE(sol.product_uom_qty, 0.00)) - sum(COALESCE(pol.unit_price_lc, 0.00) * COALESCE(pol.product_qty, 0.00)) as margin,
    round((case when sum(COALESCE(pol.unit_price_lc, 0.00) * COALESCE(pol.product_qty, 0.00)) > 0.00 then (sum(COALESCE(sol.price_unit, 0.00) * COALESCE(sol.product_uom_qty, 0.00)) - sum(COALESCE(pol.unit_price_lc, 0.00) * COALESCE(pol.product_qty, 0.00))) / sum(COALESCE(pol.unit_price_lc, 0.00) * COALESCE(pol.product_qty, 0.00)) else 0.00 end) * 100.00, 2) || '%' as profit
from purchase_order_line pol
left join purchase_order po on po.id = pol.order_id
join sale_order_line sol on sol.crm_line_id = pol.lead_product_id
left join sale_order so on so.id = sol.order_id
left join product_product pp on pp.id = pol.product_id
left join product_template pt on pt.id = pp.product_tmpl_id
left join product_uom u on (u.id=pol.product_uom)
left join product_uom u2 on (u2.id=pt.uom_id)
left join product_uom u3 on (u3.id=sol.product_uom)
where po.state not in ('draft', 'sent', 'confirmed', 'bid', 'cancel') and pol.cust_selected is true
group by pp.default_code,
    pol.product_id,
    po.date_order,
    po.partner_id,
    so.partner_id,
    po.job_id,
    po.name,
    po.customer_rfq,
    po.validator
            )
        """)
profit_analysis()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

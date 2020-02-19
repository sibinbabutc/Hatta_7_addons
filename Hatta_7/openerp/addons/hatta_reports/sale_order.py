# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
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

from osv import fields,osv
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _description = 'Inherited Sale Order'
    
    def _get_amount_dhs(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_pool = self.pool.get('res.currency')
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        sale_obj = self.browse(cr, uid, ids, context=context)
        
        for sale in sale_obj:
            if user_obj.company_id.currency_id.name == sale.pricelist_id.currency_id.name:
                res[sale.id] = sale.amount_total
            else:
                amount = cur_pool.compute(cr, uid, sale.pricelist_id.currency_id.id,
                                user_obj.company_id.currency_id.id, sale.amount_total or 0.00,
                                round=True, currency_rate_type_from=False,
                                currency_rate_type_to=False, context=context)
                res[sale.id] = amount
        return res
    
    _columns = {
        'status' : fields.text('Status'),
        'rfq' : fields.related('lead_id', 'customer_rfq', type='char', relation='crm.lead', string='RFQ #'),
        'closing_date' : fields.related('lead_id', 'date_deadline', type='date', relation='crm.lead', string='Closing Date'),
        'amt_dhs' : fields.function(_get_amount_dhs, digits_compute=dp.get_precision('Account'), type='float', string='Amount in DHS',)
                }
    
       
sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

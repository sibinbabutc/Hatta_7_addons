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

from osv import osv, fields
import time

from openerp.report import report_sxw
from tools.translate import _

class worksheet_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(worksheet_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_data': self._get_data,
            'get_sale_price': self._get_sale_price,
            'get_numbering': self._get_numbering,
            'get_cost_price_fc': self._get_cost_price_fc,
            'get_cost_price_lc': self._get_cost_price_lc
        })

    def _get_data(self, po_objs):
        result = []
        uom_pool = self.pool.get('product.uom')
        user_pool = self.pool.get('res.users')
        sale_line_pool = self.pool.get('sale.order.line')
        user_obj = user_pool.browse(self.cr, self.uid, self.uid, context={})
        data = {}
        for po_obj in po_objs:
            lines= []
            lead = po_obj.lead_id and po_obj.lead_id or False
            skip_fc = False
            if po_obj.currency_id == po_obj.foreign_currency:
                skip_fc = True
            for pol_line in po_obj.order_line:
                if pol_line.select_line:
                    real_product_name = ''
                    i = 0
                    product_name = pol_line.product_id and pol_line.product_id.name or ''
                    for a in product_name:
                        i+=1
                        if i == 20:
                            real_product_name += ' '
                            i = 0
                        real_product_name += a
                    qty = pol_line.product_qty or 1.00
                    lead_line = pol_line.lead_product_id and pol_line.lead_product_id or False
                    uom = pol_line.product_uom and pol_line.product_uom.id or \
                                            False
                    line_uom = lead_line and lead_line.uom_id and lead_line.uom_id.id or False
                    uom_name = lead_line and lead_line.uom_id and lead_line.uom_id.name or \
                                    pol_line.product_uom and pol_line.product_uom.name or False
                    if line_uom and uom != line_uom:
                        qty = uom_pool._compute_qty(self.cr, self.uid, uom, qty, line_uom)
                    coeff = 1.00
                    if line_uom and uom != line_uom:
                        coeff = uom_pool._compute_qty(self.cr, self.uid, uom, 1.00, line_uom)
                    factor = pol_line.order_id and pol_line.order_id.factor or \
                                pol_line.margin or 1.00
                    selling_price_lc = pol_line.sale_price or 0.00
                    if po_obj.direct_sale_id:
                        line_product_id = pol_line.product_id.id
                        sale_line_ids = sale_line_pool.search(self.cr, self.uid, [('order_id', '=', po_obj.direct_sale_id.id),
                                                                        ('product_id', '=', line_product_id)])
                        if sale_line_ids:
                            sale_line_obj = sale_line_pool.browse(self.cr, self.uid, sale_line_ids[0], context={})
                            selling_price_lc = sale_line_obj.price_unit
                    print uom_name, skip_fc
                    cost_price_fc = pol_line.price_unit * coeff
                    total_cost_fc = pol_line.price_unit * coeff * qty
                    if skip_fc:
                        cost_price_fc = 0.00
                        total_cost_fc = 0.00
                    sequence_no = pol_line.sequence_no
                    try:
                        sequence_no = eval(sequence_no)
                    except:
                        pass
                    vals = {
                            #'product_id': pol_line.product_id and pol_line.product_id.id or \
                             #                   False,
                            'fc_obj': po_obj.currency_id or \
                                            po_obj.company_id.currency_id or False,
                            'sequence_no': sequence_no,
                            'product_id': real_product_name,
                            'qty': qty,
                            'uom_id': uom_name,
                            'cost_price_fc': cost_price_fc,
                            'total_cost_fc': total_cost_fc,
                            'cost_price_lc': pol_line.unit_price_lc * coeff,
                            'total_cost_lc': pol_line.unit_price_lc * coeff * qty,
                            'factor': factor,
                            'selling_price_lc': selling_price_lc or 0.00,
                            'total_selling_price_lc': selling_price_lc * qty,
                            'base_cur_obj': po_obj.foreign_currency
                            }
                    print vals
                    lines.append(vals)
            data['lines'] = lines
            data['customer_rfq'] = lead and lead.customer_rfq or ''
            data['reference'] = lead and lead.reference or ''
            data['po_obj'] = po_obj
            data['exchange_rate'] = pol_line.exchange_rate or 1.0000
            data['currency'] = po_obj.pricelist_id.currency_id.name or ''
            result.append(data)
        return result

    def _get_numbering(self, po_obj):
        po_pool = self.pool.get('purchase.order')
        number = ''
        if po_obj:
            number = po_pool._get_sheet_name(self.cr, self.uid, po_obj, context={})
        return number
    
    def _get_cost_price_fc(self, data):
        lines = data.get('lines', [])
        cost_price = 0.00
        for line in lines:
            cost_price += line.get('total_cost_fc', 0.00)
        return cost_price
    
    def _get_cost_price_lc(self, data):
        lines = data.get('lines', [])
        cost_price = 0.00
        for line in lines:
            cost_price += line.get('total_cost_lc', 0.00)
        return cost_price
    
    def _get_sale_price(self, data):
        lines = data.get('lines', [])
        sale_price = 0.00
        for line in lines:
            sale_price += line.get('total_selling_price_lc', 0.00)
        return sale_price

report_sxw.report_sxw('report.worksheet.report', 'purchase.order', 'addons/hatta_reports/report/rfq_worksheet_report.rml', parser=worksheet_report, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


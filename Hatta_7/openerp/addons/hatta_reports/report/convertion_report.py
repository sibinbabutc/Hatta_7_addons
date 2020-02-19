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
import itertools
import datetime as datetime  

class convertion_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(convertion_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_data': self._get_data,
            'get_sale_price': self._get_sale_price,
            'get_cost_price_fc': self._get_cost_price_fc,
            'get_cost_price_lc': self._get_cost_price_lc
        })

    def _get_data(self, claim_objs):
        result = []
        uom_pool = self.pool.get('product.uom')
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(self.cr, self.uid, self.uid, context={})
        lines= []
        for lead in claim_objs:
            data = {}
            lines= []
            lead.write({'worksheet_date': datetime.datetime.now()})
            for lead_line in lead.product_lines:
                for pol_line in lead_line.pol_ids:
                    if pol_line.select_line:
                        po_obj = pol_line.order_id
                        skip_fc = False
                        if po_obj.currency_id == po_obj.foreign_currency:
                            skip_fc = True
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
                        uom = pol_line.product_uom and pol_line.product_uom.id or \
                                                False
                        line_uom = lead_line.uom_id and lead_line.uom_id.id or False
                        line_uom_name = lead_line.uom_id and lead_line.uom_id.name or False
                        if line_uom and uom != line_uom:
                            qty = uom_pool._compute_qty(self.cr, self.uid, uom, qty, line_uom)
                        coeff = 1.00
                        if uom != line_uom:
                            coeff = uom_pool._compute_qty(self.cr, self.uid, uom, 1.00, line_uom)
                        factor = pol_line.order_id and pol_line.order_id.factor or \
                                    pol_line.margin or 0.00
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
                                'product_id': pol_line.product_id and pol_line.product_id.id or \
                                                    False,
                                'fc_obj': po_obj.currency_id or \
                                                po_obj.company_id.currency_id or False,
                                'sequence_no': sequence_no,
                                'product_id': real_product_name,
                                'qty': qty,
                                'uom_id': line_uom_name,
                                'cost_price_fc': cost_price_fc,
                                'total_cost_fc': total_cost_fc,
                                'cost_price_lc': pol_line.unit_price_lc * coeff,
                                'total_cost_lc': pol_line.unit_price_lc * coeff * qty,
                                'factor': factor,
                                'selling_price_lc': pol_line.sale_price or 0.00,
                                'total_selling_price_lc': pol_line.sale_price * qty,
                                'line_id': lead_line.id or False,
                                'base_cur_obj': po_obj.foreign_currency
                                }
                        lines.append(vals)
            
            product_found = []
            seq_found = []
            repeat_line = []
            line_data = {}
            for line in lines:
                product_id = line.get('product_id', False)
                seq_no = line.get('sequence_no', False)
                key = str(product_id)+str(seq_no)
                if product_id in product_found and seq_no in seq_found:
                    repeat_line.append(line)
                    repeat_line.extend(line_data.get(key, []))
                    line_data[key] = []
                else:
                    product_found.append(product_id)
                    seq_found.append(seq_no)
                    if not line_data.get(key, False):
                        line_data[key] = []
                    line_data[key].append(line)
            if not repeat_line:
                lines = sorted(lines, key=lambda a: a['sequence_no'])
                data['lines'] = lines
                data['customer_rfq'] = lead.customer_rfq
                data['reference'] = lead.reference
                result.append(data)
            else:
                repeat_product_data = {}
                rem_lines = []
                for line in lines:
                    product_id = line.get('product_id', False)
                    seq_no = line.get('sequence_no', False)
                    key = str(product_id)+str(seq_no)
                    if line in repeat_line:
                        if not repeat_product_data.get(key, False):
                            repeat_product_data[key] = []
                        repeat_product_data[key].append(line)
                    else:
                        rem_lines.append(line)
                repeat_line_list = []
                for key in repeat_product_data:
                    repeat_line_list.append(repeat_product_data[key])
                combinations = list(itertools.product(*repeat_line_list))
#                 rem_lines = [x for x in lines if x not in repeat_line]
                for line in combinations:
                    line = list(line)
                    data = {}
                    real_lines = line
                    real_lines.extend(rem_lines)
                    real_lines = sorted(real_lines, key=lambda a: a['sequence_no'])
                    data['lines'] = real_lines
                    data['customer_rfq'] = lead.customer_rfq
                    data['reference'] = lead.reference
                    result.append(data)
        return result

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

report_sxw.report_sxw('report.convertion.report', 'crm.lead', 'addons/hatta_reports/report/convertion_report.rml', parser=convertion_report, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


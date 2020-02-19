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

from openerp.report import report_sxw
from openerp import pooler

class cost_sheet(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(cost_sheet, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time, 
            'get_quote_val_type': self._get_quote_val_type,
            'get_sale_price': self._get_sale_price,
            'get_total_sale_price': self._get_total_sale_price,
            'get_days': self._get_days,
            'get_manfac': self._get_manfac,
            'get_man_country': self._get_man_country,
            'get_sheet_name': self._get_sheet_name,
            'get_option_name': self._get_option_name,
            'get_work_sheet_status': self._get_work_sheet_status,
            'get_line_no': self._get_line_no,
            'get_total_sale_price_round': self._get_total_sale_price_round,
            'get_round_amount': self._get_round_amount,
            'get_shipment_charge': self._get_shipment_charge,
            'get_other_charges': self._get_other_charges,
            'get_bank_int_split': self._get_bank_int_split,
            'get_date': self._get_date
        })

    def _get_date(self, date):
       date = str(date)
       if date != '':
           return date
       else:
           return date

    def _get_quote_val_type(self, type):
        if type == 'weeks':
            return 'Weeks'
        elif type == 'days':
            return 'Days'
        elif type == 'month':
            return 'Month'
        else:
            return ''

    def sort(self, data):
        new_data = []
        for i in data:
            if i not in new_data:
                new_data.append(i)
        return new_data

    def _get_line_no(self, po_obj):
        if po_obj.parent_po_id:
            po_obj = po_obj.parent_po_id
        else:
            po_obj = po_obj
        lines = [x.id for x in po_obj.order_line if x.select_line]
        return len(lines)
    
    def _get_bank_int_split(self, po_obj):
        list = []
        total = 0.00
        for bank_line in po_obj.payment_interest_ids:
            line = "INTEREST = %s ON %s FOR %s DAYS,"%(str(round(bank_line.int_amount, 2)),
                                                      str(round(bank_line.amount)),
                                                      str(round(bank_line.days)))
            list.append(line)
            total += bank_line.int_amount
        tot_line = "TOTAL = %s"%(str(round(total)))
        list.append(tot_line)
        return "\n".join(list)
    
    def _get_other_charges(self, po_obj):
        res = [x for x in po_obj.charge_ids if x.charge_id.charge_type != 'freight']
        return res
    
    def _get_shipment_charge(self, po_obj):
        result = []
        if po_obj.weight:
            result.append("WEIGHT : %s"%(po_obj.weight))
        if po_obj.volume:
            result.append("VOLUME : %s"%(po_obj.volume))
        if po_obj.dimension:
            result.append("DIMENSION : %s"%(po_obj.dimension))
        if po_obj.zone:
            result.append("ZONE : %s"%(po_obj.zone))
        return ", ".join(result)

    def _get_sheet_name(self, po_object):
        pool = pooler.get_pool(self.cr.dbname)
        po_pool = pool.get('purchase.order')
        sheet_name = po_pool._get_sheet_name(self.cr, self.uid, po_object, filter_select=[True], context={})
        return sheet_name and "(" + str(sheet_name) + ")" or ""
#         curr_id = False
#         curr_obj = False
#         line_string_list = []
#         line_string = ""
#         temp_list = []
#         seq_data = {}
#         seq_list = []
#         if po_object.parent_po_id:
#             po_boj = po_object.parent_po_id
#         else:
#             po_boj = po_object
#         for line in po_boj.order_line:
#             if line.select_line:
#                 ref_id = line.id
#                 if line.lead_product_id:
#                     ref_id = line.lead_product_id.id
#                 seq_list.append(ref_id)
#                 seq_data[ref_id] = line.sequence_no
#         for id in seq_list:
#             if not curr_id:
#                 curr_id = id
#                 temp_list.append(seq_data.get(id, ''))
#             else:
#                 if id != curr_id + 1:
#                     temp_list = self.sort(temp_list)
#                     if len(temp_list) > 1:
#                         line_string = str(temp_list[0]) + " - "  + str(temp_list[-1])
#                         line_string_list.append(line_string)
#                     elif len(temp_list) == 1:
#                         line_string = str(temp_list[0])
#                         line_string_list.append(line_string)
#                     temp_list = [seq_data.get(id, '')]
#                     curr_id = id
#                 else:
#                     temp_list.append(seq_data.get(id, ''))
#                     curr_id = id
#         temp_list.append(seq_data.get(id, ''))
#         temp_list = self.sort(temp_list)
#         if len(temp_list) > 1:
#             line_string = str(temp_list[0]) + " - " + str(temp_list[-1])
#             line_string_list.append(line_string)
#         elif len(temp_list) == 1:
#             line_string = str(temp_list[0])
#             line_string_list.append(line_string)
#         name = ','.join(line_string_list)
#         return "( Item " + name + " )"
# 
    def _get_option_name(self, po_obj):
        pool = pooler.get_pool(self.cr.dbname)
        po_pool = pool.get('purchase.order')
        option_name = po_pool.get_option_number(self.cr, self.uid, po_obj, context={})
        if option_name:
            return " - (OPTION %s)"%(str(option_name))
        return ''

    def _get_work_sheet_status(self, po_obj):
        line = [x.id for x in po_obj.order_line if x.select_line]
        if po_obj.direct_sale_id:
            line = [x.id for x in po_obj.direct_sale_id.order_line]
        if len(line) > 1:
            return False
        return True

    def _get_sale_price(self, po_obj):
        total = 0.00
        for line in po_obj.order_line:
            if line.select_line:
                total += line.sale_price or 0.00
        if po_obj.direct_sale_id:
            total = 0.00
            for line in po_obj.direct_sale_id.order_line:
                total += line.price_unit or 0.00
        return total

    def _get_round_amount(self, po_obj):
        val = 0.00
        val = self._get_total_sale_price(po_obj) - self._get_total_sale_price_round(po_obj)
        return val

    def _get_total_sale_price_round(self, po_obj):
        total = 0.00
        product_ids = []
        for line in po_obj.order_line:
            if line.select_line:
                if line.product_id:
                    product_ids.append(line.product_id.id)
                total += float(line.sale_price) * float(line.product_qty or 0.00)
        if po_obj.direct_sale_id and total == 0.00:
            for sale_line in po_obj.direct_sale_id.order_line:
                if sale_line.product_id:
                    if sale_line.product_id.id in product_ids:
                        total += sale_line.price_subtotal
                else:
                    total += sale_line.price_subtotal
#             total = po_obj.direct_sale_id.amount_total or 0.00
        return round(total)

    def _get_total_sale_price(self, po_obj):
        total = 0.00
        product_ids = []
        for line in po_obj.order_line:
            if line.select_line:
                if line.product_id:
                    product_ids.append(line.product_id.id)
                total += float(line.sale_price) * float(line.product_qty or 0.00)
        if po_obj.direct_sale_id and total == 0.00:
            for sale_line in po_obj.direct_sale_id.order_line:
                if sale_line.product_id:
                    if sale_line.product_id.id in product_ids:
                        total += sale_line.price_subtotal
                else:
                    total += sale_line.price_subtotal
        return total

    def _get_man_country(self, po_obj):
        res = [x.name for x in po_obj.supplier_country_id]
        return ','.join(res)

    def _get_days(self, po_obj):
        count = 0
        for line in po_obj.payment_interest_ids:
            
            count += line.days or 0
        return count

    def _get_manfac(self, po_obj):
        man_list = []
        for man in po_obj.manufacturer:
            man_list.append(man.name)
        return ','.join(list(set(man_list)))

    def _get_product_quoted(self, po_obj):
        prod_name_list = []
        for line in po_obj.order_line:
            if line.product_id and line.select_line:
                prod_name_list.append(line.product_id.name)
        return ','.join(list(set(prod_name_list)))

report_sxw.report_sxw('report.cost.sheet', 'purchase.order', 'addons/hatta_reports/report/cost_sheet.rml', parser=cost_sheet, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


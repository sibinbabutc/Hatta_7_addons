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
import cStringIO
import PIL.Image
import base64
from operator import itemgetter

class remarks_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(remarks_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_remarks': self._get_remarks,
            'get_remarks_image': self._get_remarks_image
        })

    def _get_remarks(self, claim_obj):
        res = []
        lines = []
        image_lines = []
        po_objs = []
        general_remark = ""
        for line in claim_obj.product_lines:
            for pol in line.pol_ids:
                if pol.order_id and pol.order_id.state != 'cancel' and (pol.remark or pol.remark_image_ids):
                    if pol.remark:
                        sequence_float = 0.00
                        remark = pol.remark
                        remark = remark.replace('\t', '    ')
                        try:
                            sequence_float = float(line.sequence_no or 0.00)
                        except:
                            sequence_float = 0.00
                        line_data = {
                                     'sequence_float': sequence_float,
                                     'sequence': line.sequence_no or '',
                                     'product': line.product_id and line.product_id.name or '',
                                     'remark': remark or '',
                                     'id': pol.order_id.id
                                     }
                        lines.append(line_data)
                    if pol.remark_image_ids:
                        for image in pol.remark_image_ids:
                            sequence_float = 0.00
                            try:
                                sequence_float = float(line.sequence_no or 0.00)
                            except:
                                sequence_float = 0.00
                            img_data = {
                                        'sequence_float': sequence_float,
                                        'sequence': line.sequence_no or '',
                                        'product_name': line.product_id and line.product_id.name or '',
                                        'image': image.datas,
                                        'id': pol.order_id.id
                                        }
                            image_lines.append(img_data)
                if pol.order_id:
                    po_objs.append(pol.order_id)
        done_po_objs = []
        for po in po_objs:
            if not po in done_po_objs:
                general_remark += po.remark or ''
                done_po_objs.append(po)
        if claim_obj.sort_sl_no:
            lines = sorted(lines, key=itemgetter('sequence_float'))
            image_lines = sorted(image_lines, key=itemgetter('sequence_float'))
        else:
            lines = sorted(lines, key=itemgetter('sequence_float', 'id'))
            image_lines = sorted(image_lines, key=itemgetter('sequence_float', 'id'))
        return {'general_remark': general_remark, 'line': lines,'image':image_lines}
    
    def _get_remarks_image(self, claim_obj):
        res = []
        for line in claim_obj.product_lines:
            data = {}
            if line.selected_pol_id and line.selected_pol_id.remark_image_ids:
                data = {
                        'sequence': line.sequence_no or '',
                        'product_name': line.selected_pol_id.product_id and \
                                                line.selected_pol_id.product_id.name or '',
                        'images': []
                        }
                for image in line.selected_pol_id.remark_image_ids:
#                     image_data = base64.b64encode(image.datas)
#                     file_like = cStringIO.StringIO(image_data)
                    data['images'].append(image.datas)
                res.append(data)
        return res

report_sxw.report_sxw('report.webkit.remark.report', 'crm.lead', 'addons/hatta_reports/report/remark_webkit_html.mako', parser=remarks_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


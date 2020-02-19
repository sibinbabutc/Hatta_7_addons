# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 ZestyBeanz Technologies Pvt. Ltd.
#    (http://www.zbeanztech.com)
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

from hatta_reports import JasperDataParser
from jasper_reports import jasper_report

import pooler
from osv import fields, osv
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import amount_to_text_en
import time
from datetime import datetime


class remark_report(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(remark_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        result={}
        return result
    
    def generate_records(self, cr, uid, ids, data, context):
        pool= pooler.get_pool(cr.dbname)
        claim_pool = pool.get('crm.lead')
        result=[]
        for claim_obj in claim_pool.browse(cr, uid, ids, context=context):
            vals = {
                    'lead_id': claim_obj.id,
                    'cust_ref': claim_obj.customer_rfq or '',
                    'our_ref': claim_obj.reference,
                    }
            lines = []
            image_lines = []
            for line in claim_obj.product_lines:
                for pol in line.pol_ids:
                    if pol.order_id and pol.order_id.state != 'cancel' and (pol.remark or pol.remark_image_ids):
                        if pol.remark:
                            remark = pol.remark
                            remark = remark.replace('\t', '    ')
                            line_data = {
                                         'sequence': line.sequence_no or '',
                                         'product': line.product_id and line.product_id.name or '',
                                         'remark': remark or '',
                                         'id': line.order_id.id
                                         }
                            lines.append(line_data)
                        if pol.remark_image_ids:
                            for image in pol.remark_image_ids:
                                img_data = {
                                            'sequence': line.sequence_no or '',
                                            'product_name': line.product_id and line.product_id.name or '',
                                            'image': image.datas
                                            }
                                image_lines.append(img_data)
            lines = sorted(lines, key=lambda a: a['id'])
            vals['lines'] = lines
            vals['image_lines'] = image_lines
            result.append(vals)
        print result
        return result
    
jasper_report.report_jasper('report.remarks.report.jasper', 'crm.lead', parser=remark_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

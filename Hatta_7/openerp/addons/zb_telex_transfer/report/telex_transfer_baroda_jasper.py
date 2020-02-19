# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
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

import JasperDataParser
from openerp.addons.jasper_reports import jasper_report

from osv import fields, osv
import time
import datetime
from datetime import datetime

class telex_transfer_baroda_jasper(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        #print '1'*555
        super(telex_transfer_baroda_jasper, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'

    def generate_parameters(self, cr, uid, ids, data, context):
        vals = {} 
        if data['report_type']=='xls':
            vals.update({'IS_IGNORE_PAGINATION':True})
        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#         run_date = datetime.date.today()
        run_time = time.strftime("%d/%m/%Y")
#         start_date = datetime.strptime(run_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        vals.update({
                'company_name': user_obj.company_id and user_obj.company_id.name or '',
                'run_time': run_time,
                })
        return vals

    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true'
            }
    
    def generate_records(self, cr, uid, ids, data, context=None):
        result = []
        telex_pool = self.pool.get('telex.transfer')
        telex_ids = data.get('form',False)
        for telex in telex_pool.browse(cr, uid, telex_ids, context=context):
            val={}
            template_type =  dict(telex_pool.fields_get(cr, uid, allfields=['template_type'], context=context)['template_type']['selection'])[telex.template_type]
            address = ''
            ben_address =''
            ref1=''; ref2=''
            bank_address = ''
            our_ref1 = ''; our_ref2 = ''; our_ref3 = '';
            your_ref1 = ''; your_ref2 = ''; your_ref3 = '';
#             if telex.partner_id:
#                 address += telex.partner_id.name
#                 if telex.partner_id.street:
#                     address += ', ' + telex.partner_id.street
#                 if telex.partner_id.street2:
#                     address += ', ' + telex.partner_id.street2
#                 if telex.partner_id.city:
#                     address += ', ' + telex.partner_id.city
#                 if telex.partner_id.state_id:
#                     address += ', ' + telex.partner_id.state_id.name
#                 if telex.partner_id.country_id:
#                     address += ', ' + telex.partner_id.country_id.name
#                 if telex.partner_id.phone:
#                     address += ', Ph : ' + telex.partner_id.phone
#             if telex.beneficiary_address:
#                 ben_address = ", ".join(telex.beneficiary_address.split('\n'))
            if telex.ref1:
                ref1 = ", ".join(telex.ref1.split('\n'))
            if telex.ref2:
                ref2 = ", ".join(telex.ref2.split('\n'))
#             if telex.bank_address:
#                 bank_address = ", ".join(telex.bank_address.split('\n'))
            if telex.our_ref1:
                our_ref1 = ", ".join(telex.our_ref1.split('\n'))
            if telex.our_ref2:
                our_ref2 = ", ".join(telex.our_ref2.split('\n'))
            if telex.our_ref3:
                our_ref3 = ", ".join(telex.our_ref3.split('\n'))
            if telex.your_ref1:
                your_ref1 = ", ".join(telex.your_ref1.split('\n'))
            if telex.your_ref2:
                your_ref2 = ", ".join(telex.your_ref2.split('\n'))
            if telex.your_ref3:
                your_ref3 = ", ".join(telex.your_ref3.split('\n'))
            
            val.update({
                         'ref': telex.name,
                         'to': telex.to,
                         'address_line1': telex.address_line1,
                         'introduction': telex.introduction,
                         'attn': telex.attn,
                         'template_type': template_type,
                         'beneficiary_name': telex.beneficiary_name,
                         'beneficiary_address':  telex.beneficiary_address,
                         'sub': telex.sub,
                         'ref1': ref1,
                         'ref2': ref2,
                         'desc1': telex.desc1,
                         'account_no': telex.account_no,
                         'iban_no': telex.iban_no,
                         'bank_name': telex.bank_name,
                         'bank_address': telex.bank_address,
                         'branch': telex.branch,
                         'swift_bic_code': telex.swift_bic_code,
                         'amount_transferred': telex.amount_transferred,
                         'message_head1': telex.message_head1,
                         'our_ref1': telex.our_ref1,
                         'our_ref2': telex.our_ref2,
                         'our_ref3': telex.our_ref3,
                         'message_head2': telex.message_head2,
                         'your_ref1': telex.your_ref1,
                         'your_ref2': telex.your_ref2,
                         'your_ref3': telex.your_ref3,
                         'message_head3': telex.message_head3,
                         'message3_ref1': telex.message3_ref1,
                         'message3_ref2': telex.message3_ref2,
                         'message3_ref3': telex.message3_ref3,
                         'purpose_remmittence': telex.purpose_remmittence,
                         'note_head': telex.note_head,
                         'note': telex.note,
                         'partner': telex.partner_address,
                         'report_head': telex.report_head,
                         'fax_no': telex.fax_no,
                         'tel_no': telex.tel_no,
                         'email': telex.email,
                        })
                #print 'val', val
            result.append(val)

        return result
        
        
jasper_report.report_jasper('report.telex_transfer_baroda_jasper', 'telex.transfer', 
                            parser=telex_transfer_baroda_jasper)
jasper_report.report_jasper('report.telex_transfer_al_rostamani_jasper', 'telex.transfer', 
                            parser=telex_transfer_baroda_jasper)
jasper_report.report_jasper('report.telex_transfer_emirates_india_jasper', 'telex.transfer', 
                            parser=telex_transfer_baroda_jasper)
jasper_report.report_jasper('report.telex_transfer_euro_iban_jasper', 'telex.transfer', 
                            parser=telex_transfer_baroda_jasper)
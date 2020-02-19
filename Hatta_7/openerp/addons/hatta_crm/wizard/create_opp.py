# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 ZestyBeanz Technologies Pvt. Ltd.
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

import time
import requests
import os
import tempfile
import base64

class create_opp(osv.osv):
    _name = 'create.opp'
    _description = 'Create Opportunity'
    
    def onchange_transaction_type(self, cr, uid, ids, transaction_type_id, context=None):
        res = {'value': {}}
        transaction_type_pool = self.pool.get('transaction.type')
        if transaction_type_id:
            transaction_type_obj = transaction_type_pool.browse(cr, uid, transaction_type_id,
                                                                context=context)
            res['value']['analytic_account_id'] = transaction_type_obj.cost_center_id and \
                                                        transaction_type_obj.cost_center_id.id or False
            res['value']['partner_seq'] = transaction_type_obj.partner_seq or False
        return res
    
    _columns = {
                'partner_id': fields.many2one('res.partner', 'Customer'),
                'email': fields.char('Email', size=128),
                'customer_rfq': fields.char('Customer RFQ', size=128),
                'phone': fields.char('Phone', size=128),
                'date_closing': fields.date('Expected Closing Date'),
                'creation_date': fields.date('Creation Date'),
                'note': fields.text('Internal Note'),
                'datas_fname': fields.char('File Name',size=256),
                'datas': fields.binary('File'),
                'user_id': fields.many2one('res.users', 'Salesperson'),
                'lead_id': fields.many2one('crm.lead', 'Enquiry'),
                'call_no': fields.char('Coll. RFQ NO.', size=128),
                'state': fields.selection([('start', 'Start'), ('end', 'End')], 'State'),
                'coll_no_type': fields.selection([('coll', 'Coll. RFQ NO.'),
                                          ('buyer', 'Buyer Ref.')],
                                         'Type'),
                'transaction_type_id': fields.many2one('transaction.type', 'Transaction Type'),
                'analytic_account_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'partner_seq': fields.boolean('Partner Based Seq. Sufix'),
                'supplier_id': fields.many2one('res.partner', 'Principal suppliers')
                }
    _defaults = {
                 'state': 'start',
                 'creation_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'user_id': lambda self, cr, uid, context=None: uid,
                 'coll_no_type': 'coll'
                 }
    
    def check_opp(self, cr, uid, ids, context=None):
        lead_pool = self.pool.get('crm.lead')
        param_pool = self.pool.get('ir.config_parameter')
        attachment_pool = self.pool.get('ir.attachment')
        partner_pool = self.pool.get('res.partner')
        tran_pool = self.pool.get('transaction.type')
        data = self.read(cr, uid, ids, context=context)[0]
        partner_id = False
        address_data = {}
        if data.get('partner_id', False):
            partner_id = data['partner_id'][0]
            address_data = partner_pool.address_get(cr, uid, [partner_id],
                                                adr_pref=['procure', 'delivery'], context={})
        user_id = False
        if data.get('user_id', False):
            user_id = data['user_id'][0]
        procure_address_id = address_data.get('procure', False)
        del_address_id = address_data.get('delivery', False)
        tran_obj = tran_pool.browse(cr, uid, data.get('transaction_type_id', [])[0], context=context)
        vals = {
                'partner_id': partner_id,
                'inquiry_id': partner_id,
                'partner_delivery_id': del_address_id,
                'partner_procure_id': procure_address_id,
                'email_from': data.get('email', ''),
                'customer_rfq': data.get('customer_rfq', ''),
                'phone': data.get('phone', ''),
                'date_deadline': data.get('date_closing'),
                'creation_date': data.get('creation_date'),
                'description': data.get('note', ''),
                'call_no': data.get('call_no', ''),
                'coll_no_type': data.get('coll_no_type', 'coll'),
                'user_id': user_id,
                'supplier_id': data.get('supplier_id', False) and data.get('supplier_id', False)[0],
                'partner_seq': data.get('partner_seq', False),
                'transaction_type_id': data.get('transaction_type_id', [])[0],
                'analytic_account_id': data.get('analytic_account_id', [])[0],
                'track_revision': tran_obj.track_revision or False
                }
        default_value = lead_pool.default_get(cr, uid, ['description'], context=context)
        if default_value:
            vals.update(default_value)
        lead_id = lead_pool.create(cr, uid, vals, context=context)
        lead_pool.convert_opportunity(cr, uid, [lead_id], partner_id,
                                      user_ids=False,
                                      section_id=False, context=context)
        self.write(cr, uid, ids, {'state': 'end', 'lead_id': lead_id},
                   context=context)
        filename = data.get('datas_fname', '')
        datas = data.get('datas', False)
#         api_key = param_pool.get_param(cr, uid,
#                                        "pdf.doc.api.key",
#                                         context=context)
        if datas and lead_id:
#             fname,ext = filename and os.path.splitext(filename) or ('','')
#             if ext == '.pdf' and api_key:
#                 temp_file_dir = tempfile.gettempdir()
#                 file_path = os.path.join(temp_file_dir, "mail_pdf_download" + ".pdf")
#                 doc_file_path = os.path.join(temp_file_dir, "mail_pdf_download" + ".doc")
#                 f = open(file_path, 'w')
#                 f.write(base64.b64decode(datas))
#                 f.close()
#                 r = requests.post("https://api.cloudconvert.com/convert?apikey=%s&input=upload&download=inline&inputformat=pdf&outputformat=doc"%(api_key),
#                                   files = {'file': open(file_path, 'rb')})
#                 with open(doc_file_path, 'wb') as fd:
#                     for chunk in r.iter_content(1024):
#                         fd.write(chunk)
#                 f = open(doc_file_path, 'r')
#                 data = f.read()
#                 vals = {
#                         'name': fname + ".doc",
#                         'datas': base64.b64encode(data),
#                         'datas_fname': fname + ".doc",
#                         'res_model': 'crm.lead',
#                         'res_id': lead_id,
#                         'type': 'binary'
#                         }
#                 attach_id = attachment_pool.create(cr, uid, vals, context=context)
#                 f.close()
            vals = {
                    'name': filename,
                    'datas': datas,
                    'datas_fname': filename,
                    'res_model': 'crm.lead',
                    'res_id': lead_id,
                    'type': 'binary'
                    }
            attach_id = attachment_pool.create(cr, uid, vals, context=context)
        return {
                'res_id': ids[0],
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'create.opp',
                'type': 'ir.actions.act_window',
                'target':'new',
                }
    
create_opp()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

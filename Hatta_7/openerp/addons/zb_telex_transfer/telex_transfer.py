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

from osv import osv, fields

class telex_transfer(osv.osv):
    _name = "telex.transfer"
    _description = "Telex Transfer"
    _order = "id desc"
    
    _columns = { 
                'name': fields.char('Ref'),
                'to': fields.char('To'),
                'introduction': fields.char('Introduction'),
                'attn': fields.char('Attn'),
                'sub': fields.char('Sub'),
                'ref1': fields.text('Ref1'),
                'ref2': fields.text('Ref2'),
                'desc1': fields.text('Description1'),
                'beneficiary_name': fields.char('Beneficiary Name'),
                'beneficiary_address': fields.text('Beneficiary Address'),
                'account_no': fields.char('Account No'),
                'iban_no': fields.char('Iban No'),
                'bank_name': fields.char('Bank Name'),
                'bank_address': fields.text('Bank Address'),
                'branch': fields.char('Branch'),
                'swift_bic_code': fields.char('Swift/BIC Code'),
                'amount_transferred': fields.char('Amount to be transferred'),
                'message_head1': fields.char('Message Header1'),
                'message_head2': fields.char('Message Header2'),
                'message_head3': fields.char('Message Header3'),
                'our_ref1': fields.text('Message1 Ref1'),
                'our_ref2': fields.text('Message1 Ref2'),
                'our_ref3': fields.text('Message1 Ref3'),
                'your_ref1': fields.text('Message2 Ref1'),
                'your_ref2': fields.text('Message2 Ref2'),
                'your_ref3': fields.text('Message2 Ref3'),
                'message3_ref1': fields.text('Message3 Ref1'),
                'message3_ref2': fields.text('Message3 Ref2'),
                'message3_ref3': fields.text('Message3 Ref3'),
                'purpose_remmittence': fields.text('Purpose of Remmittence'),
                'note_head': fields.text('Note Head'),
                'note': fields.text('Notes'),
                'partner_id': fields.many2one('res.partner','Partner'),
                'template_type': fields.selection(string='Template Type',selection=[('baroda','Bank of Baroda'),
                                                            ('al_rostamani','Al Rostamani'),
                                                            ('emirates_india','Emirates India'),
                                                            ('euro_iban','Euro Iban')]),
                'address_line1': fields.char('To Address Line1'),
                'report_head': fields.char('Report Tittle'),
                'fax_no': fields.char('Fax No'),
                'tel_no': fields.char('Tel No'),
                'email': fields.char('Email'),
                'partner_address': fields.text('To Address  '),
        }
    
    def onchange_template_type(self, cr, uid, ids, template_type, context=None):
        res = {}
        line_ids = []
        if template_type:
            address = dict(self.fields_get(cr, uid, allfields=['template_type'], context=context)['template_type']['selection'])[template_type]
            res.update({'address_line1': address})
        return {'value': res}
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = {}
        line_ids = []
        partner_pool = self.pool.get('res.partner')
        if partner_id:
            partner_obj  = partner_pool.browse(cr, uid, partner_id, context=context)
            address = ''
            if partner_obj:
                address += partner_obj.name
                if partner_obj.street:
                    address += ', ' + partner_obj.street
                if partner_obj.street2:
                    address += ', ' + partner_obj.street2
                if partner_obj.city:
                    address += ', ' + partner_obj.city
                if partner_obj.state_id:
                    address += ',\n' + partner_obj.state_id.name
                if partner_obj.country_id:
                    address += ', ' + partner_obj.country_id.name
                if partner_obj.phone:
                    address += ',\nPh : ' + partner_obj.phone
                if partner_obj.fax:
                    address += ', Fax : ' + partner_obj.fax
            res.update({'partner_address': address})
        return {'value': res}
    
    def button_print(self, cr, uid, ids, context=None): 
        if context is None:
           context = {}
        record_ids = ids
        for telex in self.browse(cr, uid, ids, context=context):
            if telex.template_type == 'baroda':
                report_name = 'telex_transfer_baroda_jasper'
            if telex.template_type == 'al_rostamani':
                report_name = 'telex_transfer_al_rostamani_jasper'
            if telex.template_type == 'emirates_india':
                report_name = 'telex_transfer_emirates_india_jasper'
            if telex.template_type == 'euro_iban':
                report_name = 'telex_transfer_euro_iban_jasper'
        report = {
           'type' : 'ir.actions.report.xml',
           'datas': {
               'model':'telex.transfer',
               'id': context.get('active_ids') and context.get('active_ids')[0] or False,
               'ids': context.get('active_ids') and context.get('active_ids') or [],
               'report_type': 'pdf',
               'form': record_ids,
               
               },
           'report_name': report_name,
           'nodestroy': False
        }
        #print '>' * 333, report
        return report
    
telex_transfer()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
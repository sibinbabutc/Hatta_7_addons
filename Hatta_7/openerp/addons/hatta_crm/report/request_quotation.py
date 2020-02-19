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
from openerp.osv import osv
from openerp import pooler

class request_quotation(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(request_quotation, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'user': self.pool.get('res.users').browse(cr, uid, uid, context),
            'get_certificate_details': self._get_certificate_details,
            'get_contact_address': self._get_contact_person,
            'get_end_user_address': self._get_end_user_address
        })
    
    def _get_certificate_details(self, certificate_ids):
        res = []
        for certificate in certificate_ids:
            res.append(certificate.name)
        return '\n'.join(res)
    
    def _get_contact_person(self, partner_obj):
        partner_pool = pooler.get_pool(self.cr.dbname).get('res.partner')
        contact_partner_ids = partner_pool.search(self.cr, self.uid, [('parent_id', '=', partner_obj.id),
                                                                      ('type', '=', 'contact')])
        partner_name_list = []
        for contact_partner_obj in partner_pool.browse(self.cr, self.uid, contact_partner_ids):
            partner_name_list.append(contact_partner_obj.name)
        partner_name_list = list(set(partner_name_list))
        return partner_name_list and '/'.join(partner_name_list) or False
    
    def _get_end_user_address(self, partner_obj):
        partner_pool = pooler.get_pool(self.cr.dbname).get('res.partner')
        address = partner_pool._display_address(self.cr, self.uid, partner_obj, context={})
        return address.upper()
    
report_sxw.report_sxw('report.purchase.quotation.inherit','purchase.order','addons/hatta_crm/report/request_quotation.rml',parser=request_quotation)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


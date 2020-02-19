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

class covering_letter(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(covering_letter, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_procurement_address': self._get_procurement_address
        })

    def _get_procurement_address(self, claim_obj):
        partner_pool = self.pool.get('res.partner')
        partner_obj = claim_obj.partner_id or False
        address = ""
        if claim_obj.partner_procure_id:
                address_obj = claim_obj.partner_procure_id
                if address_obj.name:
                    address += address_obj.name + "\n"
                if address_obj.parent_id:
                    address += address_obj.parent_id.name + "\n"
                if address_obj.street:
                    address += address_obj.street + "\n"
                if address_obj.street2:
                    address += address_obj.street2 + "\n"
                if address_obj.city or address_obj.country_id:
                    country_name = address_obj.country_id and address_obj.country_id.name or False
                    string = ''
                    if address_obj.city:
                        string += address_obj.city
                    if country_name:
                        if address_obj.city:
                            string += ", "
                        string += country_name
                    address += string + "\n"
                if address_obj.fax:
                    address += "Fax : " + address_obj.fax
                if address_obj.mobile or address_obj.phone:
                    address += '\n'
                    if address_obj.mobile:
                        address += "Mobile : " + address_obj.mobile + ' ,  '
                    if address_obj.phone:
                        address += "Phone : " + address_obj.phone
        return address

report_sxw.report_sxw('report.covering.letter', 'crm.lead', 'addons/hatta_reports/report/covering_letter.rml', parser=covering_letter, header=False)
report_sxw.report_sxw('report.covering.letter.tech', 'crm.lead', 'addons/hatta_reports/report/covering_letter_tech.rml', parser=covering_letter, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


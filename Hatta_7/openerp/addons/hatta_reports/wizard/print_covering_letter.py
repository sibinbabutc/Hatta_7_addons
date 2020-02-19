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

class print_covering_letter(osv.osv_memory):
    _name = 'print.covering.letter'
    _description = 'Print Covering Letter'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        lead_pool = self.pool.get('crm.lead')
        res = super(print_covering_letter, self).default_get(cr, uid, fields, context=context)
        lead_id = context.get('active_id', False)
        if lead_id:
            lead_obj = lead_pool.browse(cr, uid, lead_id, context=context)
            res['lead_id'] = lead_obj.id
            res['date'] = lead_obj.date_deadline
        return res
    
    _columns = {
                'date': fields.date('Submission Date'),
                'report_type': fields.selection([('comm', 'COMMERCIAL'), ('tech', 'TECHNICAL')],
                                                'Report Type'),
                'lead_id': fields.many2one('crm.lead', 'Lead REF'),
                'duty_exemtion': fields.boolean('Duty Exemption?'),
                'duty_exemtion_letter': fields.selection([('Required', 'Required'),
                                                          ('Not Required', 'Not Required')],
                                                         'Duty Exemption Letter'),
                'revised': fields.boolean('Revised ?'),
                'user_format' : fields.boolean('User Format'),
                'note': fields.char('Note', size=128),
                'add_note': fields.char('Additional Note', size=128),
                'sec1' : fields.text('Section 1'),
                'sec2' : fields.text('Section 2')
                }
    _defaults = {
                 'report_type': 'comm',
                 'sec1' : "We thank you for your valued enquiry and are pleased to submit our offer as per enclosed.",
                 'sec2' : '''In case of any changes in the quantities, please contact us for confirmation of validity of prices with our principal supplier/s.\n\nHope our offer meets your requirements and if any further clarification, we are at your disposal.\n\nWe assure our best service at all times.'''
                 }
    
    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids)[0]
        datas = {
                 'ids': [data.get('lead_id', [False])[0]],
                 'active_ids': [data.get('lead_id', [False])[0]],
                 'model': 'crm.lead',
                 'form': self.read(cr, uid, ids)[0]
                 }
        vals = {
                'type': 'ir.actions.report.xml',
                'datas': datas,
                }
        report_type = data.get('report_type', 'comm')
        if report_type == 'comm':
            vals.update({'report_name': 'covering.letter'})
        else:
            vals.update({'report_name': 'covering.letter.tech'})
        return vals
    
print_covering_letter()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

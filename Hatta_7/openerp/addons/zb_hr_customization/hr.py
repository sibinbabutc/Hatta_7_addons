# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
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

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _order = "join_date"
    _columns = {
        'blood_group': fields.char('Blood Group', size=64),
        'emp_no': fields.char('Employee Number', size=64),
        'local_address': fields.char('Local Address', size=128),
        'local_contact_no': fields.char('Local Contact No', size=64),
        'home_contact_no': fields.char('Home Contact No', size=128),
        'join_date': fields.date('Joining Date'),
        'local_contact_no': fields.char('Local Contact No', size=64),
        'home_address': fields.char('Home Address', size=128),
        
#         'passport_no': fields.char('Passport No', size=64),
        'passport_issue_date': fields.date('Passport Issue Date'),
        'passport_expiry_date': fields.date('Passport Expiry Date'),
        'place_issue': fields.char('Place of Issue', size=64),
        
        'visa_no': fields.char('Visa No', size=64),
        'visa_issue_date': fields.date('Visa Issue Date'),
        'visa_expiry_date': fields.date('Visa Expiry Date'),
        
        'labour_card_no': fields.char('Labour Card No', size=64),
        'labour_card_issue_date': fields.date('Labour Card Issue Date'),
        'labour_card_expiry_date': fields.date('Labour Card Expiry Date'),
        
        'insurance_no': fields.char('Insurance No', size=64),
        'insurance_issue_date': fields.date('Insurance Issue Date'),
        'insurance_expiry_date': fields.date('Insurance Expiry Date'),
        
        'emirates_id_no': fields.char('Emirates Id No', size=64),
        'emirates_id_issue_date': fields.date('Emirates Id Issue Date'),
        'emirates_id_expiry_date': fields.date('Emirates Id Expiry Date'),
        
        'license_no': fields.char('UAE Driving License', size=64),
        'license_issue_date': fields.date('DL Issue Date'),
        'license_expiry_date': fields.date('DL Expiry Date'),
        
        'timesheet_ids': fields.one2many('hr.analytic.timesheet', 'emp_id', 'Child Categories'),
}
    
    
    def action_open_window(self, cr, uid, ids, context=None):
        domain = []
        for obj in self.browse(cr, uid, ids):
            domain = [('emp_id','=',obj.id)]
        return {
              'name': _('Timesheet Activities2'),
              'view_type': 'tree',
              "view_mode": 'tree',
              "target": 'current',
              'res_model': 'hr.analytic.timesheet',
              'type': 'ir.actions.act_window',
              'domain': domain,
              }    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
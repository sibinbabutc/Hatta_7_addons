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

class hr_analytic_timesheet(osv.osv):
    _inherit = "hr.analytic.timesheet"

    def _total_hrs(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            total_hrs = line.unit_amount + line.travel_hrs + line.idle_hrs + line.ot_hrs 
            res[line.id] = total_hrs
        return res

    
    _columns = {
        'emp_id': fields.many2one('hr.employee','Employee'),
        'emp_no': fields.char('Employee Number', size=64),
        'travel_hrs': fields.float('Travelling HRS'),
        'idle_hrs': fields.float('Idle HRS'),
        'ot_hrs': fields.float('OT HRS'),
        'ot_type': fields.selection([('regular_ot','Regular OT'),('holiday_ot','Holiday OT')],'OT Type'),
        'total_hrs': fields.function(_total_hrs, string='Total HRS'),
#         'emp_timesheet_wiz_id': fields.many2one('employe.timesheet.wiz','Time Sheet Wiz'),
        
}
    
    def onchange_emp_id(self, cr, uid, ids, emp_id, date, context=None):
        """
        Load Employee number on change of emp_id.
        @param emp_id: changed value of partner id
        """
        if not emp_id:
            return {'value': {'emp_no': ''}}
        emp = self.pool['hr.employee'].browse(cr, uid, emp_id, context=context)
        emp_no = emp and emp.emp_no or ''
        return {'value': {'emp_no': emp_no,'name': '/'}}
    
    
    
    _defaults = {
        'name': '/'
    }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 ZestyBeanz Technologies Pvt. Ltd.
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

class hr_payslip_employees(osv.osv_memory):
    _inherit ='hr.payslip.employees'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        payroll_run_pool = self.pool.get('hr.payslip.run')
        res = super(hr_payslip_employees, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        payroll_run_obj = payroll_run_pool.browse(cr, uid, active_id, context=context)
        res['company_id'] = payroll_run_obj.company_id.id
        return res
    
    _columns = {
                'company_id': fields.many2one('res.company', 'Company')
                }
    
    def compute_sheet(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        payroll_pool = self.pool.get('hr.payslip.run')
        sal_line_pool = self.pool.get('payroll.emp.line')
        payroll_id = context.get('active_id', False)
        if payroll_id:
            payroll_obj = payroll_pool.browse(cr, uid, payroll_id, context=context)
            for line in payroll_obj.slip_ids:
                line.unlink()
        res = super(hr_payslip_employees, self).compute_sheet(cr, uid, ids, context=context)
        payroll_id = context.get('active_id', False)
        if payroll_id:
            exist_line_ids = sal_line_pool.search(cr, uid, [('payroll_id', '=', payroll_id)],
                                                  context=context)
            if exist_line_ids:
                sal_line_pool.unlink(cr, uid, exist_line_ids, context=context)
            payroll_obj = payroll_pool.browse(cr, uid, payroll_id, context=context)
            for line in payroll_obj.slip_ids:
                vals = {
                        'employee_id': line.employee_id.id,
                        'days_payable': line.total_days or 0.00,
                        'payslip_id': line.id,
                        'payroll_id': payroll_id
                        }
                sal_line_pool.create(cr, uid, vals, context=context)
        return res
    
hr_payslip_employees()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from openerp.tools.safe_eval import safe_eval

class hr_config_settings(osv.osv_memory):
    _inherit = 'hr.config.settings'
    _columns = {
                'salary_earned_code': fields.char('Salary Earned Code', size=32),
                'total_deduction_code': fields.char('Total Deduction Code', size=32),
                'salary_advance_code': fields.char('Salary Advance Code', size=32),
                'allowance_code': fields.char('Allowance Code', size=32),
                'overtime_code': fields.char('Overtime Code', size=32),
                'net_salary_code': fields.char('Net Salary Earned Code', size=32),
                'basic_salary_code': fields.char('Basic Code', size=32),
                'emp_adv_account_id': fields.many2one('account.account', 'Emp. Advance Control Account'),
                'parent_earning_categ': fields.many2one('hr.salary.rule.category', 'Salary Earning Category'),
                'parent_ded_categ': fields.many2one('hr.salary.rule.category', 'Salary Deduction Category')
                }
    
    def get_default_parent_earning_categ(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'parent_earning_categ': icp.get_param(cr, uid,
                                                    'hatta_hr_management.parent_earning_categ',
                                                    False)}
    
    def set_default_parent_earning_categ(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.parent_earning_categ:
            icp.set_param(cr, uid, 'hatta_hr_management.parent_earning_categ',
                          config.parent_earning_categ and \
                                 config.parent_earning_categ.id or False)
    
    def get_default_basic_salary_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'basic_salary_code': icp.get_param(cr, uid,
                                                    'hatta_hr_management.basic_salary_code',
                                                    False)}
    
    def set_default_basic_salary_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.basic_salary_code:
            icp.set_param(cr, uid, 'hatta_hr_management.basic_salary_code',
                          config.basic_salary_code or False)
    
    def get_default_parent_ded_categ(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'parent_ded_categ': icp.get_param(cr, uid,
                                                    'hatta_hr_management.parent_ded_categ',
                                                    False)}
    
    def set_default_parent_ded_categ(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.parent_ded_categ:
            icp.set_param(cr, uid, 'hatta_hr_management.parent_ded_categ',
                          config.parent_ded_categ and \
                                 config.parent_ded_categ.id or False)
    
    def get_default_net_salary_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'net_salary_code': icp.get_param(cr, uid,
                                                    'hatta_hr_management.net_salary_code',
                                                    'False')}
    
    def set_default_net_salary_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.net_salary_code:
            icp.set_param(cr, uid, 'hatta_hr_management.net_salary_code',
                          config.net_salary_code or '')
    
    
    
    
    
    
    
    def get_default_emp_account_id(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'emp_adv_account_id': icp.get_param(cr, uid,
                                                    'hatta_hr_management.emp_adv_account_id',
                                                    False)}
    
    def set_default_emp_account_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.emp_adv_account_id:
            icp.set_param(cr, uid, 'hatta_hr_management.emp_adv_account_id',
                          config.emp_adv_account_id and \
                                 config.emp_adv_account_id.id or False)
    
    def get_default_salary_earned_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'salary_earned_code': icp.get_param(cr, uid,
                                                    'hatta_hr_management.salary_earned_code',
                                                    'False')}
    
    def set_default_salary_earned_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.salary_earned_code:
            icp.set_param(cr, uid, 'hatta_hr_management.salary_earned_code',
                          config.salary_earned_code or False)
    
    def get_default_total_deduction_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'total_deduction_code': icp.get_param(cr, uid,
                                                      'hatta_hr_management.total_deduction_code',
                                                      'False')}
    
    def set_default_total_deduction_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.total_deduction_code:
            icp.set_param(cr, uid, 'hatta_hr_management.total_deduction_code',
                          config.total_deduction_code or False)
    
    def get_default_salary_advance_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'salary_advance_code': icp.get_param(cr, uid,
                                                     'hatta_hr_management.salary_advance_code',
                                                     'False')}
    
    def set_default_salary_advance_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.salary_advance_code:
            icp.set_param(cr, uid, 'hatta_hr_management.salary_advance_code',
                          config.salary_advance_code or False)
    
    def get_default_allowance_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'allowance_code': icp.get_param(cr, uid,
                                                'hatta_hr_management.allowance_code',
                                                'False')}
    
    def set_default_allowance_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.allowance_code:
            icp.set_param(cr, uid, 'hatta_hr_management.allowance_code',
                          config.allowance_code or False)
    
    def get_default_overtime_code(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {'overtime_code': icp.get_param(cr, uid,
                                               'hatta_hr_management.overtime_code',
                                               'False')}
    
    def set_default_overtime_code(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        icp = self.pool.get('ir.config_parameter')
        if config.overtime_code:
            icp.set_param(cr, uid, 'hatta_hr_management.overtime_code',
                          config.overtime_code or False)
    
hr_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

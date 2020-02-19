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

{
    'name': 'Hatta HR Management',
    'version': '1.73',
    'category': 'HR Management',
    'sequence': 14,
    'summary': 'Hatta HR Management',
    'description': """This Module manage payslip generation in Hatta""",
    'author': 'ZestyBeanz Technologies',
    'website': 'http://www.zbeanztech.com',
    'images': [],
    'depends': ['hr_payroll', 'zb_hr_customization'],
    'data': [
             'wizard/print_wps_view.xml',
             'hr_view.xml',
             'hatta_report.xml',
             'wizard/hr_config_view.xml',
             'wizard/hr_payroll_payslips_by_employees.xml',
             'security/ir.model.access.csv'
             ],
    'js': [],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

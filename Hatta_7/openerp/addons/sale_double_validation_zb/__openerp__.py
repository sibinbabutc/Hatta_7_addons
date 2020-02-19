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

{
    'name': 'Sale Double Validation',
    'version': '1.0',
    'category': 'Sales Management',
    'sequence': 14,
    'summary': 'Add an extra level of validation in sales',
    'description': """This Module enables to add a level of validation to user based on limit set to the user""",
    'author': 'ZestyBeanz Technologies',
    'website': 'http://www.zbeanztech.com',
    'images': [],
    'depends': ['sale_stock'],
    'data': [
             'res_users_view.xml',
             'sale_workflow.xml',
             'sale_view.xml',
             'product_view.xml',
             'wizard/sale_validate_view.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

{
    'name': 'Telephone Expense Tracker',
    'version': '1.25',
    'category': 'custom',
    'summary': '',
    'description': """
Customized Module for Telephone Expense Tracker
==================================

    """,
    'author': 'ZestyBeanz Technologies Pvt.Ltd',
    'website': 'https://www.zbeanztech.com',
    'depends': ['account'],
    'data': [
             'security/ir.model.access.csv',
             'report.xml',
             'sequence.xml',
             'telephone_directory_view.xml',
             'telephone_expense_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

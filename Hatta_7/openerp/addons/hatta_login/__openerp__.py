# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
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
    'name': 'HATTA Login Customization',
    'version': '1.01',
    'category': '',
    'description': """
    This module is to add additional features in Login.
    
    """,
    'author': 'ZestyBeanz Technologies Pvt Ltd',
    'website': 'http://www.zbeanztech.com',
    'depends': ['base', 'email_template'],
    'data': ['security/hatta_security.xml',
             'security/ir.model.access.csv',
             'user_view.xml',
             'wizard/generate_otp_view.xml',
             'wizard/login_log_view.xml',
             'user_data.xml',
             'hatta_report.xml',
             'login_log_view.xml',
             'wizard/login_log_view.xml'
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

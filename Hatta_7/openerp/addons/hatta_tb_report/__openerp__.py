# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2012 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
#    conatct@zbeanztech.com
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
    'name': 'Trial Balance Report',
    'version': '2.1',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """
    """,
    'author': 'Zesty Beanz Technologies Pvt. Ltd.',
    'depends': [
        'account_financial_report_webkit',
        'jasper_reports'
        ],
    'init_xml': [],
    'update_xml': [
        'wizard/tb_report_view.xml',
        'wizard/account_report_trial_balance_wizard_view.xml',
        'tb_report_view.xml'
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

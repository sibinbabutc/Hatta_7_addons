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
    'name': 'Hatta Rejection Management',
    'version': '1.04',
    'category': 'Rejection Management',
    'sequence': 14,
    'summary': 'Hatta Rejection Management',
    'description': """This Module manage rejections Ecore""",
    'author': 'ZestyBeanz Technologies',
    'website': 'http://www.zbeanztech.com',
    'images': [],
    'depends': [
                'stock',
                'purchase',
                'hatta_crm'
                ],
    'data': [
             'security/hatta_security.xml',
             'wizard/create_delivery_view.xml',
             'reject_picking_view.xml',
             'rej_workflow.xml',
             'wizard/stock_return_picking.xml',
             'stock_view.xml',
             'account_invoice_view.xml',
             'hatta_report.xml',
             'wizard/rejection_report_view.xml',
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

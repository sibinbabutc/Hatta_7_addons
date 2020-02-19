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
    'name': 'HATTA Purchase Customization',
    'version': '1.14.4',
    'category': 'custom',
    'description': """
    This module is to add additional features in Request for Quotations, POs,  
    --Modification in Purchase
    
    """,
    'author': 'ZestyBeanz Technologies Pvt Ltd',
    'website': 'http://www.zbeanztech.com',
    'depends': ['purchase','document', 'mail', 'hatta_account'],
    'data': [
             'security/hatta_security.xml',
             'wizard/assign_awb_no_view.xml',
             'shipment_method_view.xml',
             'shipping_quotation_view.xml',
             'cargo_company_view.xml',
             'stock_view.xml',
             'hatta_report.xml',
             'wizard/exchange_rate_change_view.xml',
             'wizard/bank_charge_calc_view.xml',
             'purchase_data.xml',
             'purchase_view.xml',
             'report/supplier_delivery_status_view.xml',
             'security/ir.model.access.csv',
             ],
    'js': ['static/src/js/hatta.js'],
    'qweb': [
             'static/src/xml/hatta_purchase.xml'
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

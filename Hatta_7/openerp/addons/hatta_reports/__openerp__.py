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
    'name': 'Hatta Report Modification',
    'version': '1.40',
    'category': 'Reporting',
    'sequence': 14,
    'summary': 'Hatta Report Management',
    'description': """This Module is used to generate report from OpenERP""",
    'author': 'ZestyBeanz Technologies',
    'website': 'http://www.zbeanztech.com',
    'images': [],
    'depends': ['sale', 'hatta_crm', 'hatta_account', 'hatta_purchase',
                'sale_crm', 'jasper_reports',
                'report_webkit', 'report_docx',
                'hatta_rejection_management'],
    'data': [
             'security/hatta_security.xml',
             'hatta_report.xml',
             'wizard/purchase_status_view.xml',
             'wizard/purchase_order_status_view.xml',
             'wizard/print_covering_letter_view.xml',
             'wizard/po_summary_view.xml',
             'wizard/invoice_summary_view.xml',
             'wizard/sale_summary_view.xml',
             'wizard/quotation_send_status_report.xml',
             'wizard/upcoming_quo.xml',
             'wizard/purchase_invoice_summary_view.xml',
             'wizard/upcoming_delivery_wizard_view.xml',
             'wizard/shipping_payment_view.xml',
             'wizard/supplier_invoice_details_view.xml',
             'wizard/consolidated_so_view.xml',
             'wizard/invoice_uploadation_view.xml',
             'wizard/sales_return_view.xml',
             'wizard/delivery_order_summery.xml',
             'wizard/sale_purchase_analysis_view.xml',
             'lead_view.xml',
#              'sale.xml'
            'sale_order_view.xml'
             ],
    'js': [],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

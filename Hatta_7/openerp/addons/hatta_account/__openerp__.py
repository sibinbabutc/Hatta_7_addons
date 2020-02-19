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
    'name': 'HATTA Account Customization',
    'version': '1.59',
    'category': 'Accounting',
    'description': """
    This module is to add additional features in Accounts.
    
    """,
    'author': 'ZestyBeanz Technologies Pvt Ltd',
    'website': 'http://www.zbeanztech.com',
    'depends': ['account', 'sale', 'purchase', 'crm', 'jasper_reports', 'hatta_invoice_double_validation'],
    'data': [
             'security/hatta_security.xml',
             'wizard/account_config_view.xml',
             'wizard/assign_job_no_view.xml',
             'wizard/day_book_wizard_view.xml',
             'wizard/self_billing_number.xml',
             'invoice_workflow.xml',
             'wizard/cost_sheet_component_view.xml',
             'wizard/stock_partial_picking_view.xml',
             'wizard/subledger_print_view.xml',
             'wizard/general_ledger_print_view.xml',
             'wizard/purchase_matching_view.xml',
             'wizard/settle_tr_wizard_view.xml',
             'wizard/tr_status_report_view.xml',
             'wizard/daily_bank_reconciliation_view.xml',
             'wizard/local_po_wizard_view.xml',
             'wizard/invoice_upload_wizard_view.xml',
             'wizard/wizard_upcoming_payable_view.xml',
             'wizard/wizard_upcoming_receivable_view.xml',
             'wizard/wizard_pdc_report_view.xml',
             'job_account_view.xml',
             'tr_details_view.xml',
             'tr_data.xml',
             'upcoming_payable_data.xml',
             'transaction_type_view.xml',
             'local_purchase_order_view.xml',
             'stock_view.xml',
             'partner_view.xml',
             'sale_view.xml',
             'purchase_view.xml',
             'account_view.xml',
             'account_move_view.xml',
             'security/ir.model.access.csv',
             'edi/tr_notify_mail_data.xml',
             'hatta_report.xml',
             'edi/upcoming_payable_data_mail.xml',
             'user_view.xml',
             'wizard/voucher_copy_view.xml',
             'wizard/tr_report_wizard_view.xml'
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

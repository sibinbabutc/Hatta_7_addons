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
    'name': 'HATTA CRM Customization',
    'version': '1.26',
    'category': 'custom',
    'description': """
    This module is to add additional features in Leads, Opportunities, Phone Calls, 
    --Modification in Opportunities
    
    """,
    'author': 'ZestyBeanz Technologies Pvt Ltd',
    'website': 'http://www.zbeanztech.com',
    'depends': ['crm',
                'portal_crm',
                'hatta_purchase',
                'stock',
                'document',
                'sale_crm',
                'hatta_account',
                'jasper_reports',
                'hr',
                'account_cancel',
                'stock_picking_cancel',
                'stock_picking_invoice_link',
                'web_ckeditor4',
                'hatta_tb_report',
                'hatta_direct_discount',
                'hatta_ageing_report',
                'web_m2x_options'
                ],
    'data': [
             'res_users_view.xml',
             'quotation_status_send_mail_format.xml',
             'purchase_report.xml',
             'security/hatta_security.xml',
             'res_currency_view.xml',
             'purchase_workflow.xml',
             'sale_workflow.xml',
             'product_certificate_view.xml',
             'account_invoice_view.xml',
             'product_view.xml',
             'api_config.xml',
             'stock_view.xml',
             'security/ir.model.access.csv',
             'wizard/option_create_view.xml',
             'wizard/create_rfq_view.xml',
             'wizard/pol_select_qty_adjust_view.xml',
             'wizard/pol_cost_price_update_view.xml',
             'wizard/sale_confirm_wizard_view.xml',
             'wizard/purchase_confirm_wizard_view.xml',
             'wizard/quantity_change_view.xml',
             'wizard/so_create_view.xml',
             'wizard/create_opp_view.xml',
             'wizard/calc_sale_price_view.xml',
             'wizard/crm_sale_purchase_history_view.xml',
             'wizard/pol_mass_select_view.xml',
             'wizard/confirm_po_view.xml',
             'wizard/create_direct_purchase_view.xml',
             'wizard/enq_duplicate_view.xml',
             'wizard/purchase_type_selection_view.xml',
             'wizard/find_supplier_view.xml',
             'quotation_status_report.xml',
             'wizard/exp_additional_info.xml',
             'crm_lead_view.xml','crm_sequence.xml',
             'sale_view.xml',
            'report/profit_analysis_view.xml',
             'purchase_view.xml',
             'lead_server_action.xml',
             'partner_view.xml',
             'po_email_data.xml',
            'menu_security.xml'
             ],
    'css': [
            'static/src/css/hatta.css'
            ],
    'js': [
           'static/src/js/share.js',
           'static/src/js/web_shortcut.js'
           ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

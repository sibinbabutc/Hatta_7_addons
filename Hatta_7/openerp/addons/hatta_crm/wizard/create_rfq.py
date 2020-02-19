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
from openerp.tools.translate import _

from osv import fields, osv
from datetime import datetime, date
import openerp.addons.decimal_precision as dp

class create_rfq(osv.osv_memory):
    _name = 'create.rfq'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        lead_pool = self.pool.get('crm.lead')
        res = super(create_rfq, self).default_get(cr, uid, fields, context=context)
        oppor_id = context.get('active_ids')
        if oppor_id :
            res.update({'lead_id': oppor_id[0]})
            opportunity = lead_pool.browse(cr, uid, oppor_id[0], context=context)
            res.update({'analytic_account_id': opportunity.analytic_account_id and \
                                                    opportunity.analytic_account_id.id or False })
            if opportunity.reference:
                res.update({'reference': opportunity.reference})
            if opportunity.partner_id:
                res.update({'partner_id': opportunity.partner_id.id})
            if opportunity.date_deadline:
                res.update({'closing_date': opportunity.date_deadline})
            if opportunity.supplier_id:
                res.update({'supplier_ids': [opportunity.supplier_id.id]})
            res.update({'enq_date': str(datetime.now().date())})
            product_list = []
            for product_line in opportunity.product_lines:
                if product_line.select:
                    product_list.append((0, 0, {
                                                'sequence_no': product_line.sequence_no,
                                                'product_id': product_line.product_id and \
                                                                product_line.product_id.id or False,
                                                'uom_id': product_line.uom_id.id,
                                                'name': product_line.description or '',
                                                'product_qty': product_line.product_uom_qty or 0.00,
                                                'crm_product_line_ref': product_line.id,
                                                'manufacturer_id': product_line.manufacturer_id and \
                                                                    product_line.manufacturer_id.id or \
                                                                    False
                                                }))
            if not product_list:
                raise osv.except_osv(_('Error!!'), _('Please select some products to create RFQ'))
            res['product_ids'] = product_list
        return res
    _columns = {
        'lead_id': fields.many2one('crm.lead', 'Lead'),
        'reference': fields.char('Enquiry', size=128),
        'enq_date': fields.date('Enquiry Date'),
        'supplier_closing_date': fields.date('Supplier Closing Date'),
        'partner_id':fields.many2one('res.partner', 'Customer'),
        'closing_date': fields.date('Closing Date'),
        'product_ids': fields.one2many('create.rfq.product.line', 'create_rfq_wiz_id', 'Products'),
        'supplier_ids': fields.many2many('res.partner', 'create_rfq_partner_rel', 'supplier_id', 'create_rfq_id', 'Suppliers'),
        'state': fields.selection([('start', 'Start'), ('end', 'End')], 'State'),
        'warning': fields.text('Warning'),
        'pol_ids': fields.many2many('purchase.order.line', 'pol_wizard_rel',
                                    'wizard_id', 'pol_id', 'Purchase Lines')
        }
    _defaults = {
                 'state': 'start'
                 }
    
    def check_rfqs(self, cr, uid, ids, context=None):
        pol_pool = self.pool.get('purchase.order.line')
        data = self.read(cr, uid, ids, context=context)[0]
        product_data_ids = data.get('product_ids', [])
        partner_ids = data.get('supplier_ids', [])
        line_pool = self.pool.get('create.rfq.product.line')
        lead_id = data.get('lead_id', (False))[0]
        product_ids = []
        for product_data in line_pool.browse(cr, uid, product_data_ids, context=context):
            product_ids.append(product_data.product_id.id)
        purchase_line_ids = pol_pool.search(cr, uid, [('order_id.partner_id', 'in', partner_ids),
                                                      ('product_id', 'in', product_ids),
                                                      ('order_id.lead_id', '=', lead_id),
                                                      ('state', '!=', 'cancel')],
                                            context=context)
        if purchase_line_ids:
            warning = "<b>RFQ for some of the products has been created for same supplier before. Do you want to continue?</b>"
            self.write(cr, uid, ids, {'pol_ids': [(6, 0, purchase_line_ids)],
                                      'warning': warning,
                                      'state': 'end'},
                       context=context)
            return {
                    'res_id': ids[0],
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': 'create.rfq',
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    }
        return self.create_rfqs(cr, uid, ids, context=context)
    
    def create_rfqs(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        purchase_order_obj = self.pool.get('purchase.order')
        purchase_orderline_obj = self.pool.get('purchase.order.line')
        product_pricelist_obj = self.pool.get('product.pricelist')
        attachment_pool = self.pool.get('ir.attachment')
        wizard_product_pool = self.pool.get('create.rfq.product.line')
        transaction_type_pool = self.pool.get('transaction.type')
        period_pool = self.pool.get('account.period')
        user_pool = self.pool.get('res.users')
        lead_id = data['lead_id'][0]
        supplier_ids = data['supplier_ids']
        customer_id = data['partner_id']
        date_order = data['enq_date']
        date_closing = data['closing_date']
        supplier_closing_date = data['supplier_closing_date']
        product_ids = data['product_ids']
        lead = self.pool.get('crm.lead').browse(cr, uid, lead_id)
        analytic_account_id = lead.analytic_account_id and \
                                    lead.analytic_account_id.id or False
        liquid_damage_note = lead.analytic_account_id and \
                                    lead.analytic_account_id.id and lead.analytic_account_id.liquid_damage_note or False
        transaction_type_id = False
        if analytic_account_id:
            transaction_type_ids = transaction_type_pool.search(cr, 1, [('cost_center_id', '=', analytic_account_id),
                                                                          ('model_id.model', '=', 'purchase.order')])
            if transaction_type_ids:
                transaction_type_id = transaction_type_ids[0]
        if not transaction_type_id:
            raise osv.except_osv(_("Error !!!"),
                                 _("Please configure transaction type."))
        period_id = False
        if date_order:
            period_ids = period_pool.find(cr, uid, date_order, context=context)
            period_id = period_ids and period_ids[0] or False
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        company_id = user_obj.company_id.id
        po_ids = []
        if not customer_id:
            raise osv.except_osv(_('Warning!'), _('Cannot process without customer details. Please enter customer'))
        selected_lines = False
        for product_line in wizard_product_pool.browse(cr, uid, product_ids, context=context):
            if product_line.select_product:
                selected_lines = True
                break
            else:
                selected_lines = False
        if not selected_lines:
            raise osv.except_osv(_('Warning!'), _('No products. Please select atleast one product'))
        if supplier_ids:
            for supplier_id in supplier_ids:
                if lead.product_lines:
                    supplier = self.pool.get('res.partner').browse(cr, uid, supplier_id)
                    display_end_name = False
                    supplier_country_id = supplier.country_id and supplier.country_id or False
                    if supplier_country_id and supplier_country_id != company_id:
                        display_end_name = True
                    po_dict = {
                    'partner_id': supplier_id and supplier_id or False,
                    'supplier_ref': supplier.name,
                    'sp_note_duty_exemption': supplier.sp_note_duty_exemption and supplier.sp_note_duty_exemption or False,
                    'date_order': date_order and date_order or False,
                    'period_id': period_id,
                    'state':'draft',
                    'enquiry': data['reference'],
                    'product_type': lead.product_type,
                    'enquiry_date': date_order,
                    'supplier_closing_date': supplier_closing_date,
                    'enquiry_closing_date': date_closing,
                    'customer_rfq': lead.customer_rfq,
                    'lead_id': lead.id,
                    'display_end_user_name': display_end_name,
                    'pricelist_id':supplier.property_product_pricelist_purchase.id and supplier.property_product_pricelist_purchase.id or False,
                    'currency_id': supplier.property_product_pricelist_purchase.currency_id.id and supplier.property_product_pricelist_purchase.currency_id.id or False,
                    'exchange_rate': 1/supplier.property_product_pricelist_purchase.currency_id.rate,
                    'foreign_currency': lead.company_currency and lead.company_currency.id or False,
                    'analytic_account_id': analytic_account_id,
                    'transaction_type_id': transaction_type_id,
                    'liquid_damage_note': liquid_damage_note,
                    }
                    def_values = purchase_order_obj.default_get(cr, uid, ['warehouse_id', 'date_order', 'location_id', 'invoice_method'])
                    po_dict.update(def_values)
                    onchange_warehouse_data = purchase_order_obj.onchange_warehouse_id(cr, uid, ids, po_dict.get('warehouse_id', False))
                    po_dict.update(onchange_warehouse_data.get('value', {}))
                    onchange_partner_data = purchase_order_obj.onchange_partner_id(cr, uid, ids, supplier_id)
                    po_dict.update(onchange_partner_data.get('value', {}))
                    po_id = purchase_order_obj.create(cr, uid, po_dict, context=context)
                    po_ids.append(po_id)
                    
                    for product_lines in wizard_product_pool.browse(cr, uid, product_ids, context=context):
                        if product_lines.select_product:
                            line = product_lines.crm_product_line_ref
    #                         price_lists = product_pricelist_obj.price_get(cr, uid, [supplier.property_product_pricelist_purchase.id], line.product_id.id, line.product_uom_qty, supplier_id, context=context)
    #                         cost_price = price_lists[supplier.property_product_pricelist_purchase.id]
                            cost_price = product_lines.crm_product_line_ref.cost_price or 0.00
                            certificate_data = [(4, x.id) for x in line.certificate_ids]
                            product_obj = line.product_id
                            po_line_dict = {
                                    'sequence_no': line.sequence_no or 1,
                                    'product_id': line.product_id.id,
                                    'account_id': product_obj.property_account_expense and \
                                                    product_obj.property_account_expense.id or \
                                                    product_obj.categ_id and \
                                                    product_obj.categ_id.property_account_expense_categ and \
                                                    product_obj.categ_id.property_account_expense_categ.id or False,
                                    'name': line.description,
                                    'date_planned': supplier_closing_date,
                                    'product_uom': line.uom_id.id,
                                    'product_qty': product_lines.product_qty or 0.00,
                                    'price_unit': cost_price,
                                    'order_id': po_id,
                                    'taxes_id': line.taxes_id and [tax.id for tax in line.taxes_id] or False,
                                    'price_subtotal': line.price_subtotal,
                                    'certificate_ids': certificate_data,
                                    'lead_product_id': line and line.id or False,
                                    'manufacturer_id': product_lines.manufacturer_id and \
                                                            product_lines.manufacturer_id.id or False
                                    }
                            purchase_orderline_obj.create(cr, uid, po_line_dict,context=context)
                    po =  purchase_order_obj.browse(cr, uid, po_id)
                    lead_attachment_ids  = attachment_pool.search(cr, uid, [('res_model', '=', 'crm.lead'), ('res_id', '=', lead.id)], context=context)
                    if lead_attachment_ids:
                        for lead_attachment_id in lead_attachment_ids:
                            lead_attachment = attachment_pool.browse(cr, uid, lead_attachment_id)
                            dict_attachment = {
                                    'name': lead_attachment.name,
                                    'type': lead_attachment.type,
                                    'datas': lead_attachment.datas,
                                    'user_id': lead_attachment.user_id.id,
                                    'res_model':'purchase.order',
                                    'res_id': po.id,
                                    'res_name': po.name,
                                    'partner': po.dest_address_id.name,
                                    
                                    }
                            attachment_pool.create(cr, uid, dict_attachment)
                else:
                    raise osv.except_osv(_('Warning!'), _('No lines in enquired products. So you cannot request for quotation'))
        else:
            raise osv.except_osv(_('Warning!'), _('No suppliers. Please enter atleast one supplier'))    
        context.update({
                'tree_view_ref': 'hatta_purchase.purchase_order_tree_inherit',
                })
        return {
                'name': 'Request For Quotations',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'domain': [('lead_id', '=', lead_id)],
                'res_id': po_ids and po_ids[0] or False,
                'context': context,
                }
        
    def button_select_all(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        wizard_product_pool = self.pool.get('create.rfq.product.line')
        product_ids = data['product_ids']
        for product_data in wizard_product_pool.browse(cr, uid, product_ids, context=context):
            product_data.write({'select_product': True})
        return {
                'name': _('Create RFQ'),
                'res_id': ids[0],
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'create.rfq',
                'type': 'ir.actions.act_window',
                'target':'new',
                }
            
create_rfq()

class create_rfq_product_line(osv.osv_memory):
    _name = 'create.rfq.product.line'
    _description = 'Create RFQ Product Line'
    _columns = {
                'sequence_no': fields.char('Sequence', size=64, select=True),
                'product_id': fields.many2one('product.product', 'Product'),
                'name': fields.char('Description', size=256),
                'uom_id': fields.many2one('product.uom', 'Unit of Measure'),
                'product_qty': fields.float('Quantity',
                                            digits_compute= dp.get_precision('Product Unit of Measure')),
                'create_rfq_wiz_id': fields.many2one('create.rfq', 'Wizard'),
                'crm_product_line_ref': fields.many2one('crm.product.lines', 'CRM Product Line Ref'),
                'manufacturer_id': fields.many2one('res.partner', 'Manufacturer'),
                'select_product': fields.boolean('Select'),
                }
create_rfq_product_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

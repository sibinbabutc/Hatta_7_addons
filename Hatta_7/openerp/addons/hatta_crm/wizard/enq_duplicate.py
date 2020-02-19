# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 ZestyBeanz Technologies Pvt. Ltd.
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

from osv import osv, fields

from openerp import netsvc
import time

class enq_duplicate(osv.osv_memory):
    _name = 'enq.duplicate'
    _description = 'Enquiry Duplicate'
    
    def default_get(self, cr, uid, field_name, context=None):
        if context is None:
            context = {}
        res = super(enq_duplicate, self).default_get(cr, uid, field_name, context=context)
        active_id = context.get('active_id', False)
        if active_id:
            res['lead_id'] = active_id
        return res
    
    _columns = {
                'lead_id': fields.many2one('crm.lead', 'Enquiry'),
                'closing_date': fields.date('Closing Date'),
                'customer_ids': fields.many2many('res.partner', 'partner_wizard_rel', 'wizard_id',
                                                 'partner_id', 'Customer(s)')
                }
    
    def duplicate_enq(self, cr, uid, ids, context=None):
        lead_pool = self.pool.get('crm.lead')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        line_pool = self.pool.get('crm.product.lines')
        purchase_pool = self.pool.get('purchase.order')
        purchase_line_pool = self.pool.get('purchase.order.line')
        data = self.read(cr, uid, ids, [], context=context)[0]
        closing_date = data.get('closing_date', False)
        customer_ids = data.get('customer_ids', [])
        lead_id = data.get('lead_id', False)[0]
        wf_service = netsvc.LocalService('workflow')
        lead_obj = lead_pool.browse(cr, uid, lead_id, context=context)
        lead_ids = []
        result = mod_obj.get_object_reference(cr, uid, 'crm', 'crm_case_category_act_oppor11')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        lead_line_map = {}
        purchase_state_map = {}
        for customer in customer_ids:
            default = {
                       'partner_id': customer,
                       'date_deadline': closing_date,
                       'product_lines': [],
                       'creation_date': time.strftime("%Y-%m-%d")
                       }
            onchange_partner_data = lead_pool.onchange_partner_id(cr, uid, ids, customer, '')
            default.update(onchange_partner_data.get('value', {}))
            new_lead_id = lead_pool.copy(cr, uid, lead_id, default, context=context)
            new_lead_obj = lead_pool.browse(cr, uid, new_lead_id, context=context)
#             line_ids = [x.id for x in new_lead_obj.product_lines]
#             line_pool.unlink(cr, uid, line_ids, context=context)
            purchase_ids = purchase_pool.search(cr, uid, [('lead_id', '=', lead_id)])
            for line in lead_obj.product_lines:
                line_default = {
                                'sequence_no': line.sequence_no,
                                'lead_id': new_lead_id,
                                'pol_ids': []
                                }
                new_line_id = line_pool.copy(cr, uid, line.id, line_default, context=context)
                lead_line_map[line.id] = new_line_id
            new_purchase_ids = []
            for purchase_obj in purchase_pool.browse(cr, uid, purchase_ids, context=context):
                new_purchase_id = purchase_pool.copy(cr, uid, purchase_obj.id, {'lead_id': new_lead_id,
                                                                                'order_line': [],
                                                                                'unused_seq': ''})
                new_purchase_ids.append(new_purchase_id)
                for line in purchase_obj.order_line:
                    lead_line_id = line.lead_product_id and line.lead_product_id.id or False
                    default = {}
                    if lead_line_id and lead_line_map.get(lead_line_id, False):
                        default = {'lead_product_id': lead_line_map[lead_line_id],
                                   'order_id': new_purchase_id}
                    purchase_line_pool.copy(cr, uid, line.id, default)
                purchase_state_map[new_purchase_id] = purchase_obj.state
            for new_purchase_obj in purchase_pool.browse(cr, uid, new_purchase_ids, context=context):
                for line in new_purchase_obj.order_line:
                    lead_line_id = line.lead_product_id and line.lead_product_id.id or False
                    if lead_line_id and lead_line_map.get(lead_line_id, False):
                        line.write({'lead_line_id': lead_line_map[lead_line_id]})
                if purchase_state_map.get(new_purchase_obj.id, '') == 'bid':
                    wf_service.trg_validate(uid, 'purchase.order', \
                                            new_purchase_obj.id, 'bid_received', cr)
            lead_ids.append(new_lead_id)
        result['domain'] = "[('id','in',["+','.join(map(str, lead_ids))+"])]"
        return result
    
enq_duplicate()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

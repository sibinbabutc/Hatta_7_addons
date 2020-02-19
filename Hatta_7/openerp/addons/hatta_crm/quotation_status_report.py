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

import time

class quotation_status(osv.osv):
    _name = 'quotation.status'
    _description = 'Quotation Status'
    
    def _get_count(self, cr, uid, ids, fields, args, context=None):
        res = {}
        for status in self.browse(cr, uid, ids, context=context):
            tb = 0
            email = 0
            late = 0
            regret = 0
            revi = 0
            other = 0
            for line in status.line_ids:
                if line.submission_type == 'tb':
                    tb += 1
                elif line.submission_type == 'email':
                    email += 1
                elif line.submission_type == 'late_quote':
                    late += 1
                elif line.submission_type == 'regret':
                    regret += 1
                elif line.submission_type == 'revised':
                    revi += 1
                else:
                    other += 1
            res[status.id] = {
                              'tb_count': tb,
                              'email_count': email,
                              'late_count': late,
                              'regret': regret,
                              'revised': revi,
                              'other': other
                              }
        return res
    
    _columns = {
                'date': fields.date('Submission Date'),
                'user_id': fields.many2one('res.users', 'Created User'),
                'line_ids': fields.one2many('quotation.status.line', 'status_id', 'Line(s)'),
                'state': fields.selection([('open', 'Open'), ('closed', 'Closed')], 'State'),
                'tb_count': fields.function(_get_count, type="integer", string="T.B Quote Submission", multi='count'),
                'email_count': fields.function(_get_count, type="integer", string="Email Quote Submission", multi='count'),
                'late_count': fields.function(_get_count, type="integer", string="Late Quote Submission", multi='count'),
                'regret': fields.function(_get_count, type="integer", string="Regret Quote", multi='count'),
                'revised': fields.function(_get_count, type="integer", string="Revised Quote Submission", multi='count'),
                'other': fields.function(_get_count, type="integer", string="Others", multi='count')
                }
    _defaults = {
                 'state': 'open',
                 'user_id': lambda self, cr, uid, context=None: uid,
                 'date': lambda *a: time.strftime('%Y-%m-%d')
                 }
    _rec_name = 'date'
    _sql_constraints = [
                        ('date', 'unique(date)', 'Another status report for the same date already exist!!!'),
    ]
    
    def get_quote_data(self, cr, uid, ids, context=None):
        lead_pool = self.pool.get('crm.lead')
        line_pool = self.pool.get('quotation.status.line')
        old_line_ids = line_pool.search(cr, uid, [('status_id', 'in', ids)], context=context)
        if old_line_ids:
            line_pool.unlink(cr, uid, old_line_ids, context=context)
        for stat_obj in self.browse(cr, uid, ids, context=context):
            date = stat_obj.date
            lead_ids = lead_pool.search(cr, uid, [('date_deadline', '=', date),
                                                  ('analytic_account_id.cons_quo_stat_report', '=', True)],
                                        order='creation_date,reference', context=context)
            lines = []
            for lead_id in lead_ids:
                onchange_data = line_pool.onchange_lead_id(cr, uid, ids, lead_id, context=context)
                data = onchange_data.get('value', {})
                data.update({'lead_id': lead_id})
                lines.append((0, 0, data))
            if lines:
                stat_obj.write({'line_ids': lines})
        return True
    
    def submit(self, cr, uid, ids, context=None):
        template_pool = self.pool.get('email.template')
        model_data_pool = self.pool.get('ir.model.data')
        template_id = model_data_pool.get_object_reference(cr, uid, 'hatta_crm',
                                                           'quotation_mail_template')[1]
        for id in ids:
            template_pool.send_mail(cr, uid, template_id, id, force_send=True, context=context)
        return self.write(cr, uid, ids, {'state': 'closed'}, context=context)
    
    def set_to_draft(self, cr, uid, ids, context=None):
        
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)
    
quotation_status()

class quotation_status_line(osv.osv):
    _name = 'quotation.status.line'
    _description = 'Quotation Status Line'
    
    def onchange_lead_id(self, cr, uid, ids, lead_id, context=None):
        res = {'value': {}}
        lead_pool = self.pool.get('crm.lead')
        if lead_id:
            lead_obj = lead_pool.browse(cr, uid, lead_id, context=context)
            vals = {
                    'received_date': lead_obj.creation_date,
                    'client_ref_no': lead_obj.customer_rfq,
                    'partner_id': lead_obj.partner_id and lead_obj.partner_id.id or False,
                    'closing_date': lead_obj.date_deadline,
                    }
            res['value'].update(vals)
        return res
    
    _columns = {
                'received_date': fields.date('Received Date'),
                'lead_id': fields.many2one('crm.lead', 'Our Ref. No.'),
                'client_ref_no': fields.char('Client Ref. No.', size=128),
                'partner_id': fields.many2one('res.partner', 'Client Name'),
                'closing_date': fields.date('Closing Date'),
                'submission_type': fields.selection([('tb', 'T.B'), ('email', 'Email'),
                                                     ('late_quote', 'Late Quote'),
                                                     ('regret', 'Regret'), ('revised', 'Revised Bid'),
                                                     ('online', 'Online'), ('other', 'Other')],
                                                    'Sb. Type'),
                'remark': fields.text('Remark'),
                'status_id': fields.many2one('quotation.status', 'Status Rel')
                }
quotation_status_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

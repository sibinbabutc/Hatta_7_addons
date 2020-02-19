# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 ZestyBeanz Technologies Pvt. Ltd.
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

class mail_message(osv.osv):
    _inherit = 'mail.message'
    
    def _get_default_author(self, cr, uid, context=None):
        return False
mail_message()

class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        message_pool = self.pool.get('mail.message')
        res = super(mail_compose_message, self).default_get(cr, uid, fields, context=context)
        if context.get('forward_message_id', False):
            message_obj = message_pool.browse(cr, uid, context['forward_message_id'], context=context)
            body = res.get('body', '')
            old_body = message_obj.body
            to_address = []
            partner_ids = []
            partner_objs = []
            email_list =[]
            for partner in message_obj.partner_ids:
                if partner.email in email_list:
                    continue
                email_list.append(partner.email)
                to_address.append("%s<%s>"%(partner.name or '', partner.email or ''))
                partner_ids.append(partner.id)
            for partner in message_obj.notified_partner_ids:
                if partner.email in email_list:
                    continue
                email_list.append(partner.email)
                to_address.append("%s<%s>"%(partner.name or '', partner.email or ''))
                partner_ids.append(partner.id)
            old_details = "<br>From: %s<br>Date: %s<br>Subject: %s<br>To: %s<br>"%(message_obj.email_from, message_obj.date, message_obj.subject, ','.join(to_address))
            body += "<br><br>-----------------------ORGINAL MESSAGE-----------------------\n" + old_details + old_body
            res['attachment_ids'] = [x.id for x in message_obj.attachment_ids]
            res['body'] = body
            res['subject'] = "FWD: " + message_obj.subject
            res['partner_ids'] = partner_ids
        return res
    
    def send_mail(self, cr, uid, ids, context=None):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """
        if context is None:
            context = {}
        ir_attachment_obj = self.pool.get('ir.attachment')
        active_ids = context.get('active_ids')
        user_pool = self.pool.get('res.users')
        is_log = context.get('mail_compose_log', False)
        user_obj = user_pool.browse(cr, uid, uid, context=context)

        for wizard in self.browse(cr, uid, ids, context=context):
            mass_mail_mode = wizard.composition_mode == 'mass_mail'
            active_model_pool_name = wizard.model if wizard.model else 'mail.thread'
            active_model_pool = self.pool.get(active_model_pool_name)

            # wizard works in batch mode: [res_id] or active_ids
            res_ids = active_ids if mass_mail_mode and wizard.model and active_ids else [wizard.res_id]
            for res_id in res_ids:
                # mail.message values, according to the wizard options
                post_values = {
                    'subject': wizard.subject,
                    'body': wizard.body,
                    'email_from': '%s <%s>'%(user_obj.company_id.name, user_obj.company_id.email or ''),
                    'parent_id': wizard.parent_id and wizard.parent_id.id,
                    'partner_ids': [partner.id for partner in wizard.partner_ids],
                    'attachment_ids': [attach.id for attach in wizard.attachment_ids],
                    'attachments': [],
                }
                # mass mailing: render and override default values
                if mass_mail_mode and wizard.model:
                    email_dict = self.render_message(cr, uid, wizard, res_id, context=context)
                    post_values['partner_ids'] += email_dict.pop('partner_ids', [])
                    for filename, attachment_data in email_dict.pop('attachments', []):
                        # decode as render message return in base64 while message_post expect binary
                        post_values['attachments'].append((filename, base64.b64decode(attachment_data)))
                    attachment_ids = []
                    for attach_id in post_values.pop('attachment_ids'):
                        new_attach_id = ir_attachment_obj.copy(cr, uid, attach_id, {'res_model': self._name, 'res_id': wizard.id}, context=context)
                        attachment_ids.append(new_attach_id)
                    post_values['attachment_ids'] = attachment_ids
                    post_values.update(email_dict)
                # post the message
                subtype = 'mail.mt_comment'
                if is_log:  # log a note: subtype is False
                    subtype = False
                elif mass_mail_mode:  # mass mail: is a log pushed to recipients, author not added
                    subtype = False
                    context = dict(context, mail_create_nosubscribe=True)  # add context key to avoid subscribing the author
                msg_id = active_model_pool.message_post(cr, uid, [res_id], type='comment', subtype=subtype, context=context, **post_values)
                # mass_mailing: notify specific partners, because subtype was False, and no-one was notified
                if mass_mail_mode and post_values['partner_ids']:
                    self.pool.get('mail.notification')._notify(cr, uid, msg_id, post_values['partner_ids'], context=context)

        return {'type': 'ir.actions.act_window_close'}
    
mail_compose_message()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

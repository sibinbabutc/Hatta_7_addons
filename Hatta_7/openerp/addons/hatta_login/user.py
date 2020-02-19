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

import random
from datetime import datetime
import pooler
from openerp import SUPERUSER_ID

class hatta_login_otp(osv.osv):
    _name = 'hatta.login.otp'
    _rec_name = 'user_id'
    
    def _get_now(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in ids:
            res[id] = datetime.strftime(datetime.now(), "%d/%m/%Y")
        return res
    
    _columns = {
                'user_id': fields.many2one('res.users','User'),
                'user_otp': fields.char('Password', size=32),
                'active': fields.boolean('Active'),
                'date_today': fields.function(_get_now, string='Today', size=128),
                'manual_reset': fields.boolean('Manual Reset')
                }
    _defaults = {
                 'active': True
                 }
    
    _sql_constraints = [
        ('user_uniq', 'unique(user_id)', 'User already exists!!'),
    ]
    
    def reset_password(self,cr, uid, ids, context=None):
        if context is None:
            context={}
            
        for user in self.browse(cr, uid, ids,context=context):
            password=random.randrange(10001,99999)
            cr.execute('update res_users set password=%s where id=%s',(password, user.user_id.id))
            cr.execute('update hatta_login_otp set user_otp=%s where user_id=%s',(password, user.user_id.id))
        
        return True
    
    def generate_otp_cron(self,cr, uid, ids, context=None):
        if context is None:
            context={}
        otp_user_ids = self.search(cr, uid, [], context=context)
        for otp_user_obj in self.browse(cr, uid, otp_user_ids, context=context):
            if otp_user_obj.manual_reset:
                otp_user_obj.write({'manual_reset': False})
            else:
                self.reset_password(cr, uid, otp_user_ids, context=context)
        return True
    
    def generate_otp_cron_email(self,cr, uid, ids, context=None):
        if context is None:
            context={}
        template_pool = self.pool.get('email.template')
        model_data_pool = self.pool.get('ir.model.data')
        login_otp_pool = self.pool.get('hatta.login.otp')
        otp_user_ids = self.search(cr, uid, [], context=context)
#         self.reset_password(cr, uid, otp_user_ids, context=context)
        template_id = model_data_pool.get_object_reference(cr, uid, 'hatta_login',
                                                           'email_user_password')[1]
        context['current_date'] = datetime.strftime(datetime.now(), "%d/%m/%Y")
        login_otp_ids = login_otp_pool.search(cr, uid, [], limit=1, context=context)
        if login_otp_ids:
            template_pool.send_mail(cr, uid, template_id, login_otp_ids[0], force_send=True, context=context)
        return True
    
hatta_login_otp()

class res_users(osv.osv):
    _inherit = 'res.users'
    
    def login(self, db, login, password):
        log_pool = self.pool.get('login.log.view')
        cr = pooler.get_db(db).cursor()
        res = super(res_users, self).login(db, login, password)
        if res:
            pending_logout = log_pool.search(cr, SUPERUSER_ID, [('user_id', '=', res),
                                                                ('logout_date', '=', False)],
                                             context={})
            if not pending_logout:
                cr.autocommit(True)
                now = datetime.now()
                vals = {
                        'user_id': res,
                        'login_date': now
                        }
                log_pool.create(cr, SUPERUSER_ID, vals)
        return res
    
    def logout(self, cr, uid):
        log_pool = self.pool.get('login.log.view')
        pending_logout = log_pool.search(cr, SUPERUSER_ID, [('user_id', '=', uid),
                                                            ('logout_date', '=', False)],
                                         context={})
        if pending_logout:
            now = datetime.now()
            log_pool.write(cr, uid, pending_logout, {'logout_date': now, 'status': 'proper'})
        return True
res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

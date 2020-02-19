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

from datetime import datetime
from web import http
openerpweb = http

class login_log_view(osv.osv):
    _name = 'login.log.view'
    _description = 'Login Log'
    
    def _get_now(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in ids:
            res[id] = datetime.strftime(datetime.now(), "%d/%m/%Y")
        return res
    
    _columns = {
                'user_id': fields.many2one('res.users', 'User'),
                'login_date': fields.datetime('Login Date'),
                'logout_date': fields.datetime('Logout Date'),
                'status': fields.selection([('proper', 'User Logout'),
                                            ('im_proper', 'System Logout'),
                                            ('in_use', 'In Use')],
                                           'Logout Type'),
                'date_today': fields.function(_get_now, string='Today', size=128)
                }
    
    def logout_users(self, cr, uid, ids, context=None):
        template_pool = self.pool.get('email.template')
        model_data_pool = self.pool.get('ir.model.data')
        otp_log_pool = self.pool.get('hatta.login.otp')
        otp_ids = otp_log_pool.search(cr, uid, [], context=context)
        otp_user_ids = [x.user_id.id for x in otp_log_pool.browse(cr, uid, otp_ids, context=context)]
        pending_logout = self.search(cr, uid, [('logout_date', '=', False),
                                               ('user_id', 'in', otp_user_ids)], context=context)
        inuse_logout = self.search(cr, uid, [('logout_date', '=', False),
                                             ('user_id', 'not in', otp_user_ids)], context=context)
        now = datetime.now()
        if pending_logout:
            self.write(cr, uid, inuse_logout, {'logout_date': now, 'status': 'im_proper'})
        if inuse_logout:
            self.write(cr, uid, inuse_logout, {'logout_date': now, 'status': 'in_use'})
        all_log = self.search(cr, uid, [], limit=1, context=context)
        if all_log:
             template_id = model_data_pool.get_object_reference(cr, uid, 'hatta_login',
                                                                'user_access_email')[1]
             template_pool.send_mail(cr, uid, template_id, all_log[0], force_send=True, context=context)
        return True
    
login_log_view()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

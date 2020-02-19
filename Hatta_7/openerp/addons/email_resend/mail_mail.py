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

from osv import osv

class mail_mail(osv.osv):
    _inherit = 'mail.mail'
    
    def retry_mail_sending(self, cr, uid, context=None):
        mail_obj = self.pool.get('mail.mail')
        mail_ids = mail_obj.search(cr, uid, [('state', '=', 'exception')],
                                   context=context)
        for mail in mail_obj.browse(cr, uid, mail_ids, context=context):
            mail.write({'state': 'outgoing'})
            if mail.type == 'comment':
                mail.send()
        return True
    
mail_mail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from tools.translate import _

class share_wizard(osv.osv):
    _inherit = 'share.wizard'
    
    def go_step_2(self, cr, uid, ids, context=None):
        res = super(share_wizard, self).go_step_2(cr, uid, ids, context=context)
        for wizard in self.browse(cr, uid, ids, context=context):
            mail = wizard.new_users
            mail_list = mail.split('\n')
            for email in mail_list:
                m = email.split('@')
                m = m[-1]
                m = m.split('.')
                m = m[0]
                if m.upper() != 'HATTA':
                    raise osv.except_osv(_("Error !!!"),
                                         _("Invalid email !!!"))
        return res

share_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

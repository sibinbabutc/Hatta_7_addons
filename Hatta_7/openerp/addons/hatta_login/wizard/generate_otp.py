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

import openerp.addons.decimal_precision as dp
from tools.translate import _
import math

class generate_otp_wiz(osv.osv_memory):
    _name = 'generate.otp.wiz'
    
    def generate_otp(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        log_pool = self.pool.get('hatta.login.otp')
        log_ids = log_pool.search(cr, uid, [], context=context)
        self.pool.get('hatta.login.otp').reset_password(cr, uid, log_ids,context=context)
        log_pool.write(cr, uid, log_ids, {'manual_reset': True}, context=context)
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'user.password.jasper',
                }
    
generate_otp_wiz()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

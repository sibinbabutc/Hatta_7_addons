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

class voucher_unmatch(osv.osv_memory):
    _name = 'voucher.unmatch'
    _description = 'Unmatching Voucher'
    _columns = {
                'voucher_id': fields.many2one('account.voucher', 'Select Voucher',
                                              domain="[('state', '=', 'posted')]")
                }
voucher_unmatch()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

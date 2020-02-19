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

class account_financial_report(osv.osv):
    _inherit = 'account.financial.report'
    _columns = {
                'display_total': fields.boolean('Display Total'),
                'report_type': fields.selection([('bl', 'Balance Sheet'), ('pl', 'Profit & Loss')],
                                                'Report Type'),
                'total_label': fields.char('Total Label', size=128)
                }
account_financial_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

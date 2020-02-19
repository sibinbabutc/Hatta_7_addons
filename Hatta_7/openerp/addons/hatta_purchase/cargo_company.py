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
from openerp.tools.translate import _

class cargo_company(osv.osv):
    _name = 'cargo.company'
    _description = 'Cargo Company Model'
    _rec_name = 'cargo_company'
     
    _columns = {
        'start_date' : fields.date('Scheme Start Date'),
        'end_date' : fields.date('Scheme End Date'),
        'agent_name' : fields.char('Agent Name'),
        'policy_no' : fields.char('Insurance Policy No.'),
        'cargo_company' : fields.char('Cargo Company'),
        'max_value' : fields.float(string="Maximum Value"),
        'turn_over' : fields.float(string="Annual Turnover"),
        'company_id' : fields.many2one('res.company', string="Company"),
                }

cargo_company()

class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'company_ids' : fields.one2many('cargo.company', 'company_id', string="Companies")
                }
res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
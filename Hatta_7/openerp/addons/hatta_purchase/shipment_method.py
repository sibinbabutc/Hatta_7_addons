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

class hatta_shipment_method(osv.osv):
    _name = 'hatta.shipment.method'
    _columns = {
                'name': fields.char('Name', size=128),
                'communication_charges': fields.float('Communication Charges', digits_compute= dp.get_precision('Account')),
                'bank_charges': fields.float('Bank Charges', digits_compute= dp.get_precision('Account')),
                'bank_interest': fields.float('Bank Interest Rate', digits_compute= dp.get_precision('Account')),
                'insurance_charges': fields.float('Insurance Charges', digits_compute= dp.get_precision('Account')),
                'customs_duty': fields.float('Customs Duty Percent', digits_compute= dp.get_precision('Account')),
                'clg_agent_charges': fields.float('Clearing Agent Charges', digits_compute= dp.get_precision('Account')),
                'clearing_expenses': fields.float('Clearing Expenses at port', digits_compute= dp.get_precision('Account')),
                'transport_delivery_expenses': fields.float('Transport and Delivery Expenses', digits_compute= dp.get_precision('Account')),
                'misc_expenses': fields.float('Misc. Expenses if any', digits_compute= dp.get_precision('Account')),
                }
hatta_shipment_method()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

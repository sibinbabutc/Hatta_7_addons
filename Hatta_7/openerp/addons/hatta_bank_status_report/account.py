# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
import openerp.addons.decimal_precision as dp

class account_journal(osv.osv):
    _inherit = 'account.journal'
    
    _columns = {
                'is_deposit': fields.boolean('Is a Deposit Journal ?',  help="Tick if Deposit Journal."),
                'is_withdrawal': fields.boolean('Is a Withdrawal Journal ?', help="Tick if Withdrawal Journal."),
    }
    
account_journal()

class account_account(osv.osv):
    _inherit = 'account.account'
    
    _columns = {
                'is_bank': fields.boolean('Bank',  
                                          help="This field should be set Ticked in order to available in the bank status report"),
    }
    
account_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

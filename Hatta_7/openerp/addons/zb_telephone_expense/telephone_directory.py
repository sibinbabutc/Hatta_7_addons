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
import openerp.exceptions
from openerp.tools.translate import _

class telephone_directory(osv.osv):
    _name = "telephone.directory"
    _description = "Telephone Directory"
    _order = "id desc"
    
    _columns = { 
                'name': fields.char('Name'),
                'mobile': fields.char('Mobile'),
                'service_provider_id': fields.many2one('tel.service.provider', 'Service Provider'),
                'allowed_amount': fields.float('Allowed Amount', digits_compute=dp.get_precision('Account')),
                'account_allocation_ids': fields.one2many('tel.account.allocation', 'directory_id', 'Account Allocation'),
                'group_allocation_ids': fields.one2many('tel.group.allocation', 'directory_id', 'Group Allocation'),
        }
    
    _sql_constraints = [
        ('number_uniq', 'unique(mobile)', 'Mobile Number must be unique!'),
    ]
    
    def create(self, cr, uid, vals, context=None):
        result = super(telephone_directory, self).create(cr, uid, vals, context=context)
        directory_obj = self.browse(cr, uid, result, context=context)
        account_perc_total = 0.0
        group_perc_total = 0.0
        for account_line_obj in directory_obj.account_allocation_ids:
            account_perc_total += account_line_obj.percentage
        for group_line_obj in directory_obj.group_allocation_ids:
            group_perc_total += account_line_obj.percentage
        if directory_obj.account_allocation_ids and account_perc_total != 100:
            raise openerp.exceptions.Warning(_('Total Account allocation Percentage should be 100!'))
        if directory_obj.group_allocation_ids and group_perc_total != 100:
            raise openerp.exceptions.Warning(_('Total Group allocation Percentage should be 100!'))
        return result
    
    def write(self, cr, uid, ids, vals, context=None):
        result = super(telephone_directory, self).write(cr, uid, ids, vals, context=context)
        for directory_obj in self.browse(cr, uid, ids, context=context):
            account_perc_total = 0.0
            group_perc_total = 0.0
            for account_line_obj in directory_obj.account_allocation_ids:
                account_perc_total += account_line_obj.percentage
            for group_line_obj in directory_obj.group_allocation_ids:
                group_perc_total += group_line_obj.percentage
            if directory_obj.account_allocation_ids and account_perc_total != 100:
                raise openerp.exceptions.Warning(_('Total Account allocation Percentage should be 100!'))
            if directory_obj.group_allocation_ids and group_perc_total != 100:
                raise openerp.exceptions.Warning(_('Total Group allocation Percentage should be 100!'))
        return result
    
    def copy(self, cr, uid, id, default=None, context=None):
        default['mobile'] = False
        res = super(telephone_directory, self).copy(cr, uid, id, default, context=context)
        return res
    
telephone_directory()

class tel_account_allocation(osv.osv):
    _name = "tel.account.allocation"
    _description = "Telephone Account Allocation"
    _order = "id desc"
    _rec_name = 'account_id'
    
    _columns = { 
                'directory_id': fields.many2one('telephone.directory', 'Telephone Directory'),
                'account_id': fields.many2one('account.account', 'Account'),
                'analytic_account_id': fields.many2one('account.analytic.account', 'Cost Center'),
                'percentage': fields.float('Percentage', digits_compute=dp.get_precision('Account'),),
                'expense_id': fields.many2one('telephone.expense', 'Telephone Expense'),
                'value': fields.float('Value', digits_compute=dp.get_precision('Account'),),
        }
    
    
tel_account_allocation()

class tel_group_allocation(osv.osv):
    _name = "tel.group.allocation"
    _description = "Telephone Group Allocation"
    _order = "id desc"
    _rec_name = 'group_id'
    
    _columns = { 
                'directory_id': fields.many2one('telephone.directory', 'Telephone Directory'),
                'group_id': fields.many2one('telephone.group', 'Telephone Group'),
                'percentage': fields.float('Percentage', digits_compute=dp.get_precision('Account'),),
                'expense_id': fields.many2one('telephone.expense', 'Telephone Expense'),
                'value': fields.float('Value', digits_compute=dp.get_precision('Account'),),
        }
    
tel_group_allocation()

class tel_service_provider(osv.osv):
    _name = "tel.service.provider"
    _description = "Service Provider"
    _order = "id desc"
    
    _columns = { 
                'name': fields.char('Name'),
                'partner_id': fields.many2one('res.partner', 'Party'),
        }
    
tel_service_provider()

class telephone_group(osv.osv):
    _name = "telephone.group"
    _description = "Telephone Group"
    _order = "id desc"
    
    _columns = { 
                'name': fields.char('Name'),
        }
    
telephone_group()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: fernandoL (fernando_ld@vauxoo.com)
############################################################################
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


from openerp.osv import osv, fields


class account_move_line(osv.Model):
    _inherit = "account.move.line"

    """
    """

    _columns = {
        'stock_move_id': fields.many2one('stock.move', 'Stock move ID'),
    }


class account_move(osv.Model):
    _inherit = "account.move"

    """
    """

    _columns = {
        'stock_move_id': fields.many2one('stock.move', 'Stock move ID'),
    }


class stock_move(osv.Model):
    _inherit = "stock.move"

    """
    """

    def _create_account_move_line(self, cr, uid, move, src_account_id,
            dest_account_id, reference_amount, reference_currency_id,
            context=None):
        res = super(stock_move, self)._create_account_move_line(
            cr, uid, move, src_account_id, dest_account_id, reference_amount,
            reference_currency_id, context=context)
        for line in res:
            line[2]['stock_move_id'] = move.id
        return res


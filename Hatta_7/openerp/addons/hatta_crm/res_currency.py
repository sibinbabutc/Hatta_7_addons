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

from openerp.tools.amount_to_text_en import english_number

class res_currency(osv.osv):
    _inherit = 'res.currency'
    _columns = {
                'sec_curr_name': fields.char('Secondary Currency', size=32),
                }
    
    def amount_word(self, cr, uid, curr_obj, amount, context=None):
        words = ''
        amount = '%.2f' % amount
        if curr_obj:
            if curr_obj.name.upper() == 'BRL':
                currency_name = 'reais'
            else:
                currency_name = curr_obj.name
            list = str(amount).split('.')
            start_word = english_number(int(list[0]))
            end_word = english_number(int(list[1]))
            cents_number = int(list[1])
            cents_name = (cents_number > 1) and 'Cents' or 'Cent'
            if curr_obj.sec_curr_name:
                cents_name = curr_obj.sec_curr_name
            if cents_number > 0.00:
                words = ' '.join([currency_name, start_word, 'AND' ,cents_name, end_word])
            else:
                words = ' '.join([currency_name, start_word])
        words = words.replace(",", "")
        words = words.replace("AED", "DIRHAMS")
        return words + " Only"
    
res_currency()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

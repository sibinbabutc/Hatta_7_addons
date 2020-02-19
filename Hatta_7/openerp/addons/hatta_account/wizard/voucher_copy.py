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

class voucher_copy(osv.osv_memory):
    _name = 'voucher.copy'
    _description = 'Voucher Copy'
    _columns = {
                'move_id': fields.many2one('account.move', 'Voucher', required="True")
                }
    
    def get_real_default_data(self, cr, uid, data, add_default, context=None):
        real_data = {}
        if data.get('id', False):
            del data['id']
        if data.get('create_date', False):
            del data['create_date']
        if data.get('write_date', False):
            del data['write_date']
        if data.get('create_uid', False):
            del data['create_uid']
        if data.get('write_uid', False):
            del data['write_uid']
        if data.get('analytic_lines', False):
            del data['analytic_lines']
        if data.get('skip_check', False):
            data['skip_check'] = False
        if data.get('reconcile_id', False):
            data['reconcile_id'] = False
        if data.get('reconcile_partial_id', False):
            data['reconcile_partial_id'] = False
        if data.has_key('rec_date'):
            del data['rec_date']
        if data.has_key('bank_credit'):
            del data['bank_credit']
        if data.has_key('bank_debit'):
            del data['bank_debit']
        if data.has_key('voucher_id'):
            del data['voucher_id']
        if data.has_key('doc_no'):
            del data['doc_no']
        for ele in data:
            ele_value = data[ele]
            if isinstance(ele_value, tuple):
                ele_value = ele_value[0]
            if add_default:
                real_data["default_%s"%(ele)] = ele_value
            else:
                real_data[ele] = ele_value
        return real_data
    
    def copy_voucher(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        data = self.read(cr, uid, ids, context=None)[0]
        move_id = data.get('move_id', False)[0]
#         move_obj = move_pool.browse(cr, uid, move_id, context=context)
        ctx = context.copy()
        field_names = move_pool._columns.keys()
        print field_names
        move_data = move_pool.read(cr, uid, move_id, field_names, context=context)
        print move_data
        real_move_data = self.get_real_default_data(cr, uid, move_data, True, context=context)
        move_line = []
        if real_move_data.get('default_line_id', []):
            move_line_ids = real_move_data['default_line_id']
            move_line_fields = move_line_pool._columns.keys()
            move_line_datas = move_line_pool.read(cr, uid, move_line_ids, move_line_fields, context=context)
            for move_line_data in move_line_datas:
                real_move_line_data = self.get_real_default_data(cr, uid, move_line_data, False,
                                                                 context=context)
                move_line.append((0, 0, real_move_line_data))
        real_move_data['default_line_id'] = move_line
        if real_move_data.get('default_name', False):
            del real_move_data['default_name']
        if real_move_data.get('default_state', False):
            del real_move_data['default_state']
        if real_move_data.get('voucher_id', False):
            del real_move_data['voucher_id']
        if real_move_data.get('reconcile_id', False):
            del real_move_data['reconcile_id']
        if real_move_data.get('reconcile_partial_id', False):
            del real_move_data['reconcile_partial_id']
        ctx.update(real_move_data)
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_move_journal_line')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        res = mod_obj.get_object_reference(cr, uid, 'account', 'view_move_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['context'] = real_move_data
        return result
    
voucher_copy()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

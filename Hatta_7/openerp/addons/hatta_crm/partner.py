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

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
                'partner_code': fields.char('Partner Code', size=64),
                'is_manufac': fields.boolean('Manufacturer'),
                'pric_supplier': fields.boolean('Principal Supplier'),
                'reviewed': fields.boolean('Reviewed?', readonly = True),
                'create_uid': fields.many2one('res.users', 'Created User'),
                'type': fields.selection([('default', 'Default'), ('invoice', 'Invoice'),
                                          ('delivery', 'Shipping'), ('contact', 'Contact'),
                                          ('other', 'Other'), ('procure', 'Procurement')],
                                         'Address Type',
                                         help="Used to select automatically the right address according to the context in sales and purchases documents."),
                'sp_note_duty_exemption': fields.text('Special Notes for Duty Exemption'),
                'manufacturer_ids': fields.many2many('res.partner', 'supp_man_rel',
                                                     'supplier_id', 'man_id',
                                                     'Manufacturers')
                }
    
    def review_user(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'reviewed': True}, context=context)
    
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('partner_code',False)
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        result = []
        ids = [x for x in ids if x]
        for partner in self.browse(cr, user, ids, context=context):
            mydict = {
                      'id': partner.id,
                      'name': partner.name,
                      'partner_code': partner.partner_ac_code,
                      }
            result.append(_name_get(mydict))
        return result
    
    def check_duplicate_name(self, cr, uid, ids, name, context=None):
        """"checks partner name duplication"""
        name1 = name.replace(".", " ")
        name2 = name.replace(" ", '.')
        name3 = name.replace(".", "")
        name4 = name.replace(",", "")
        name5 = name.replace(",", ".")
        name6 = name.replace(",", " ")
        name_ids = self.search(cr, uid, ['|', '|', '|', '|', '|',
                        ('name', 'ilike', name1), ('name', 'ilike', name2),
                        ('name', 'ilike', name3), ('name', 'ilike', name4),
                        ('name', 'ilike', name5), ('name', 'ilike', name6),
                        ('id', 'not in', ids)], context=context)
        return (name_ids and True) or  False
    
    def write(self, cr, uid, ids, vals, context=None):
        """sets reviewed to False when partner name is edited (no duplicate)"""
        res = super(res_partner, self).write(cr, uid, ids, vals, context=context)
        if vals.get('name'):
            if self.check_duplicate_name(cr, uid, ids, vals.get('name'), context=context):
                cr.execute ("UPDATE res_partner SET reviewed = False WHERE id = '%s'" % (ids[0]))
        return res    
    
    def _check_partner_name(self, cr, uid, ids, context=None):
        """allows specific group users to duplicate partner names and review"""
        partner_obj = self.browse(cr, uid, ids, context=context)
        for partner in partner_obj:
            if partner.name and (partner.supplier or partner.customer) and not partner.parent_id:
                if self.check_duplicate_name(cr, uid, ids, partner.name, context=context):
                    can_create = False
                    view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hatta_crm', 'group_partner_duplicate')
                    if view_id:
                        user_obj = self.pool.get('res.users').search(cr, uid, [('id', '=', uid), ('groups_id', '=', view_id[1])], context = context)
                        if not user_obj:
                            if partner.reviewed:
                                return True
                            else:
                                return False
        return True
                 
    _constraints = [(_check_partner_name, '\n You are not authorized to duplicate partner name', ['name'])]
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

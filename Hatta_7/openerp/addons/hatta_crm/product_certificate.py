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

class product_certificate(osv.osv):
    _name = 'product.certificate'
    _columns = {
                'name': fields.char('Name', size=128),
                'code': fields.char('Code', size=32),
                'note': fields.text('Note')
                }
    
    def create(self, cr, uid, vals, context=None):
        charge_pool = self.pool.get('charge.type')
        res = super(product_certificate, self).create(cr, uid, vals, context=context)
        charge_vals = {
                       'name': vals.get('name', ''),
                       'charge_type': 'other',
                       'related_cert_id': res
                       }
        charge_pool.create(cr, uid, charge_vals, context=context)
        return res
    
product_certificate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 ZestyBeanz Technologies Pvt. Ltd.
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

import pooler
import base64

class data_template_wizard(osv.osv):
    _name = 'jasper.data.template'
    _description = 'Model to create xml data template'
    _columns = {
                'model_id': fields.many2one('ir.model', 'Model', required=True),
                'data': fields.binary('Date'),
                'filename': fields.char('File Name', size=128),
                'depth': fields.integer('Depth'),
                'state': fields.selection([('end', 'End'), ('create', 'Create')], string='State')
                }
    _defaults = {
                 'depth': 1,
                 'state': 'create'
                 }
    
    def action_create(self, cr, uid, ids, context=None):
        pool = pooler.get_pool(cr.dbname)
        data = self.read(cr, uid, ids)[0]
        values = pool.get('ir.model').read(cr, uid, data['model_id'][0], ['model'], context)
        model = values['model']
        xml = pool.get('ir.actions.report.xml').create_xml(cr, uid, model, data['depth'], context)
        file_data = base64.encodestring( xml )
        self.write(cr, uid, ids, {'data': file_data, 'state': 'end', 'filename': 'Jasper_Template_zb.xml'}, context=context)
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_create_data_tempate_form')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name': 'Create Data Template',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'jasper.data.template',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'new',
                'nodestroy': True,
                'res_id': ids[0] or False,
                }
        return True

data_template_wizard

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class base_config_settings(osv.osv_memory):
    _inherit = 'base.config.settings'

    _columns = {
                'pdf_doc_api_key': fields.text('PDF To Doc API Key'),
                }

    def get_default_pdf_doc_api_key(self, cr, uid, ids, context=None):
        param_pool = self.pool.get('ir.config_parameter')
        pdf_doc_api_key = param_pool.get_param(cr, uid, "pdf.doc.api.key", context=context)
        return {'pdf_doc_api_key': pdf_doc_api_key}

    def set_pdf_doc_api_key(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for record in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, "pdf.doc.api.key",
                                        record.pdf_doc_api_key or '',
                                        context=context)
base_config_settings()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

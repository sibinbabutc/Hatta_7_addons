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

import tools
import base64
import cStringIO
import pooler
from osv import fields,osv
from tools.translate import _
from tools.misc import get_iso_codes
import time
from datetime import datetime
import csv
from openerp.tools.safe_eval import safe_eval

class payslip_batch_export_sif(osv.osv_memory):

    def act_getfile(self, cr, uid, ids, context=None):
        now = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
#         now = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        icp = self.pool.get('ir.config_parameter')
        user_pool = self.pool.get('res.users')
        this = self.browse(cr, uid, ids)[0]
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        rows=[]
        count=0
        total=0.0
        salary_earned_code = icp.get_param(cr, uid,
                                           'hatta_hr_management.salary_earned_code',
                                           'False')
        deduction_code = icp.get_param(cr, uid,
                                       'hatta_hr_management.total_deduction_code',
                                       'False')
        sal_advance_code = icp.get_param(cr, uid,
                                         'hatta_hr_management.salary_advance_code',
                                         'False')
        allowance_code = icp.get_param(cr, uid,
                                       'hatta_hr_management.allowance_code',
                                       'False')
        overtime_code = icp.get_param(cr, uid,
                                      'hatta_hr_management.overtime_code',
                                      'False')
        if not salary_earned_code or not deduction_code or not sal_advance_code or \
                     not allowance_code or not overtime_code:
            raise osv.except_osv(_("Error!!!"),
                                 _("Please configure code in HR settings !!!!"))
        total = 0.00
        company_obj = this.payslip_run_id.company_id
        for slip in this.payslip_run_id.slip_ids:
            salary_earned = 0.00
            deduction = 0.00
            sal_advance = 0.00
            allowance = 0.00
            overtime = 0.00
            if slip.employee_id.sal_transfer_mode != 'WPS':
                continue
            count+=1
            for line in slip.line_ids:
                if line.code == salary_earned_code:
                    salary_earned += line.total or 0.00
                if line.code == deduction_code:
                    deduction += line.total or 0.00
                if line.code == sal_advance_code:
                    sal_advance += line.total or 0.00
                if line.code == allowance_code:
                    allowance += line.total
                if line.code == overtime_code:
                    overtime += line.total
            allowance += sal_advance + allowance + overtime
            employee_bank = slip.employee_id.bank_account_id and \
                                    slip.employee_id.bank_account_id.acc_number or ''
            total += ((salary_earned - deduction) + allowance)
            data=['EDR',slip.employee_id.labour_card_no, 
                  company_obj.comp_bank_number or '',
                  employee_bank.replace(" ", ''),
                  slip.date_from, slip.date_to,
                  int(slip.days_payable), int(salary_earned - deduction), int(allowance),
                  int(slip.total_days - slip.days_payable)]
            rows.append(data)
        company= ['SCR', company_obj.labor_number or '',
                  company_obj.comp_bank_number or '',
                  now.strftime('%Y-%m-%d'), now.strftime('%H%M'), 
                  this.payslip_run_id.date_start[5:7]+ this.payslip_run_id.date_start[:4],
                  count, int(total), 'AED', company_obj.name ]
        rows.append(company)

        buf=cStringIO.StringIO()       
        writer=csv.writer(buf, dialect='excel')
        for row in rows:
            writer.writerow(row)
        out=base64.encodestring(buf.getvalue())
        buf.close()
        self.write(cr, uid, ids, {'state':'get', 'data':out, 'file_name':this.name},
                   context=context)
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payslip_batch.export.sif',
                'type': 'ir.actions.act_window',
                'res_id': ids[0],
                'target': 'new',
                'context': context
                }

    _name = "payslip_batch.export.sif"
    _columns = {
            'payslip_run_id': fields.many2one('hr.payslip.run', 'Payslip Batch'),
            'company_id': fields.many2one('res.company', 'Company'),
            'file_name': fields.char('Filename', size=128, readonly=True),
            'name': fields.char('Filename', size=128, readonly=True),
            'data': fields.binary('File', readonly=True),
            'state': fields.selection( ( ('choose','choose'),   # choose language
                                         ('get','get'),         # get the file
                                       ) ),
    }
    def default_get(self, cr, uid, field, context=None):
        now = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
#         now = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        user_pool = self.pool.get('res.users')
        payslip_run_pool = self.pool.get('hr.payslip.run')
        res = super(payslip_batch_export_sif, self).default_get(cr, uid, field, context=context)
        data = payslip_run_pool.browse(cr, uid, context['active_ids'], context)[0]
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        if 'company_id' in field:
            res.update({'company_id':user_obj.company_id.id})
        if 'payslip_run_id' in field:
            res.update({'payslip_run_id':data.id})
        if 'name' in field:
            filename= (data.company_id.mol_no or '')+now.strftime('%d%m%y%H%M%S')+'.SIF'
            res.update({'name':filename})
        res['state']='choose'
        return res
    
payslip_batch_export_sif()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

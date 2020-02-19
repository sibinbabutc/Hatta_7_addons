# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 ZestyBeanz Technologies Pvt. Ltd.
#    (http://www.zbeanztech.com)
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

from hatta_account import JasperDataParser
from collections import defaultdict
from jasper_reports import jasper_report
from account_financial_report_webkit.report.common_reports import CommonReportHeaderWebkit

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime


class general_ledger(JasperDataParser.JasperDataParser, CommonReportHeaderWebkit):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(general_ledger, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true',
            'net.sf.jasperreports.export.xls.detect.cell.type': 'true',
            'net.sf.jasperreports.export.xls.white.page.background': 'true',
            'net.sf.jasperreports.export.xls.show.gridlines': 'true',
            }
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        pool= pooler.get_pool(cr.dbname)
        user_pool = pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)
        start_date = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
        end_date = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
        vals = {
                'company_name': comp_obj.name or '',
                'run_time': fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context),
                'curr': comp_obj.currency_id.name or '',
                'report_name': "GENERAL LEDGER REPORT FOR THE PERIOD %s - %s"%(str(start_date), str(end_date))
                }
        if data['report_type']=='xls':
            vals.update({'IS_IGNORE_PAGINATION':True})
        return vals
    
    def _compute_account_ledger_lines(self, accounts_ids, init_balance_memoizer, main_filter,
                                      target_move, start, stop, cost_center_id):
        res = {}
        for acc_id in accounts_ids:
            move_line_ids = self.get_move_lines_ids(acc_id, main_filter, start, stop, cost_center_id,
                                                    target_move)
            if not move_line_ids:
                res[acc_id] = []
                continue

            lines = self._get_ledger_lines(move_line_ids, acc_id)
            res[acc_id] = lines
        return res

    def get_move_lines_ids(self, account_id, main_filter, start, stop, cost_center_id,
                           target_move,mode='include_opening'):
        """Get account move lines base on form data"""
        if mode not in ('include_opening', 'exclude_opening'):
            raise osv.except_osv(_('Invalid query mode'), _('Must be in include_opening, exclude_opening'))

        if main_filter in ('filter_period', 'filter_no'):
            return self._get_move_ids_from_periods(account_id, start, stop, target_move)

        elif main_filter == 'filter_date':
            return self._get_move_ids_from_dates(account_id, start, stop, cost_center_id, target_move)
        else:
            raise osv.except_osv(_('No valid filter'), _('Please set a valid time filter'))

    def _get_move_ids_from_dates(self, account_id, date_start, date_stop, cost_center_id, target_move,
                                 mode='include_opening'):
        # TODO imporve perfomance by setting opening period as a property
        move_line_obj = self.pool.get('account.move.line')
        search_period = [('date', '>=', date_start),
                         ('date', '<=', date_stop),
                         ('account_id', '=', account_id),
                         ('move_id.skip_check', '=', False)]

        # actually not used because OpenERP itself always include the opening when we
        # get the periods from january to december
        if mode == 'exclude_opening':
            opening = self._get_opening_periods()
            if opening:
                search_period += ['period_id', 'not in', opening]

        if target_move == 'posted':
            search_period += [('move_id.state', '=', 'posted')]
        if cost_center_id:
            search_period += [('analytic_account_id', '=', cost_center_id)]

        return move_line_obj.search(self.cursor, self.uid, search_period)

    def _get_ledger_lines(self, move_line_ids, account_id):
        if not move_line_ids:
            return []
        res = self._get_move_line_datas(move_line_ids)
        ## computing counter part is really heavy in term of ressouces consuption
        ## looking for a king of SQL to help me improve it
        move_ids = [x.get('move_id') for x in res]
        counter_parts = self._get_moves_counterparts(move_ids, account_id)
        for line in res:
            line['counterparts'] = counter_parts.get(line.get('move_id'), '')
        return res
    
    def _compute_init_balance(self,account_id,start_date,cost_center_id=None):
        try:
            open_periods =  self.pool.get('account.period').search(self.cursor, self.uid, [('special', '=', True)])
            if cost_center_id:
                self.cursor.execute("SELECT sum(debit) AS debit, "
                                    " sum(credit) AS credit, "
                                    " sum(debit)-sum(credit) AS balance, "
                                    " sum(amount_currency) AS curr_balance"
                                    " FROM account_move_line aml"
                                    " WHERE aml.date < %s"
                                    " AND account_id = %s"
                                    " AND period_id not in %s"
                                    " AND aml.analytic_account_id = %s", (start_date, account_id,tuple(open_periods,),cost_center_id))
            else:
                self.cursor.execute("SELECT sum(debit) AS debit, "
                                    " sum(credit) AS credit, "
                                    " sum(debit)-sum(credit) AS balance, "
                                    " sum(amount_currency) AS curr_balance"
                                    " FROM account_move_line aml"
                                    " WHERE aml.date < %s"
                                    " AND period_id not in %s"
                                    " AND account_id = %s", (start_date, tuple(open_periods,),account_id))
            res = self.cursor.dictfetchone()
        except Exception, exc:
            self.cursor.rollback()
            raise
        return {#'debit': res.get('debit') or 0.0,
                #'credit': res.get('credit') or 0.0,
                'init_balance': res.get('balance') or 0.0,
                'init_balance_currency': res.get('curr_balance') or 0.0,
                #'state': mode
                }
    
    def _get_move_line_datas(self, move_line_ids, order='per.special DESC, l.date ASC, per.date_start ASC, m.name ASC'):
        # Possible bang if move_line_ids is too long
        # We can not slice here as we have to do the sort.
        # If slice has to be done it means that we have to reorder in python
        # after all is finished. That quite crapy...
        # We have a defective desing here (mea culpa) that should be fixed
        #
        # TODO improve that by making a better domain or if not possible
        # by using python sort
        if not move_line_ids:
            return []
        if not isinstance(move_line_ids, list):
            move_line_ids = [move_line_ids]
        monster = """
SELECT l.id AS id,
            l.date AS ldate,
            j.code AS jcode ,
            j.type AS jtype,
            l.currency_id,
            l.account_id,
            l.amount_currency,
            l.ref AS lref,
            l.name AS lname,
            i.number as invoice_number,
            COALESCE(l.debit, 0.0) - COALESCE(l.credit, 0.0) AS balance,
            l.debit,
            l.credit,
            l.period_id AS lperiod_id,
            ja.name as job_ac,
            aaa.code as cc,
            per.code as period_code,
            per.special AS peropen,
            l.partner_id AS lpartner_id,
            p.name AS partner_name,
            p.partner_ac_code as partner_account,
            m.name AS move_name,
            COALESCE(partialrec.name, fullrec.name, '') AS rec_name,
            COALESCE(partialrec.id, fullrec.id, NULL) AS rec_id,
            m.id AS move_id,
            c.name AS currency_code,
            i.id AS invoice_id,
            i.type AS invoice_type,
            i.number AS invoice_number,
            l.date_maturity
FROM account_move_line l
    JOIN account_move m on (l.move_id=m.id)
    LEFT JOIN res_currency c on (l.currency_id=c.id)
    LEFT JOIN account_move_reconcile partialrec on (l.reconcile_partial_id = partialrec.id)
    LEFT JOIN account_move_reconcile fullrec on (l.reconcile_id = fullrec.id)
    LEFT JOIN res_partner p on (l.partner_id=p.id)
    LEFT JOIN account_invoice i on (m.id =i.move_id)
    LEFT JOIN account_period per on (per.id=l.period_id)
    LEFT JOIN job_account ja on (ja.id = l.job_id)
    LEFT JOIN account_analytic_account aaa on (aaa.id = l.analytic_account_id)
    JOIN account_journal j on (l.journal_id=j.id)
    WHERE l.id in %s"""
        monster += (" ORDER BY %s" % (order,))
        try:
            self.cursor.execute(monster, (tuple(move_line_ids),))
            res = self.cursor.dictfetchall()
        except Exception, exc:
            self.cursor.rollback()
            raise
        return res or []
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        account_pool = self.pool.get('account.account')
        main_filter = 'filter_date'
        account_ids = data['form'].get('account_ids', [])
        start_date = data['form']['date_from']
        stop_date = data['form']['date_to']
        cost_center_data = data['form'].get('cost_center_id', False)
        cost_center_id = False
        if cost_center_data:
            cost_center_id = cost_center_data[0]
            
        ledger_lines_memoizer = self._compute_account_ledger_lines(account_ids, {},
                                                                   main_filter, 'posted', start_date,
                                                                   stop_date, cost_center_id)
        
        for account in ledger_lines_memoizer:
            check_first_move_line = True
            move_lines = ledger_lines_memoizer[account]
            init_bal = self._compute_init_balance(account,start_date,cost_center_id)['init_balance']
            init_bal_curr = self._compute_init_balance(account,start_date,cost_center_id)['init_balance_currency']
            if not move_lines and init_bal:
                account_obj = account_pool.browse(cr, uid, account, context=context)
                init_month = ""
                init_month = datetime.strptime(start_date, '%Y-%m-%d').strftime("%B")
                init_vals = {
                             'vr_no': False,
                            'vr_date': datetime.strptime(start_date, '%Y-%m-%d'),
                            'vr_type': False,
                            'partner_name': False,
                            'gl_code': False,
                            'job_ac': False,
                            'cost_center': False,
                            'debit': float(init_bal) > 0 and float(init_bal) or 0.00,
                            'credit': float(init_bal) < 0 and float(abs(init_bal)) or 0.00,
                            'balance': float(init_bal) or float(0.00),#init_bal or 0.00,
                            'remark': "OP. BALANCE",
                            'account_name':"%s / %s"%(account_obj.code, account_obj.name),
                            'amount_curr': float(init_bal_curr),
                            'curr': '',
                            'month': init_month and init_month.upper(),
                             }
                result.append(init_vals)
            for line in move_lines:
                print line,"--------------->LINE"
                account_id = line.get('account_id', False)
                account_obj = account_pool.browse(cr, uid, account_id, context=context)
                partner_code = line.get('partner_ac_code', False)
                partner_name = partner_code and "[" + partner_code + "]" + line.get('partner_name', '') or \
                                    line.get('partner_name', '')
                line_date = line.get('ldate', False) and \
                                        datetime.strptime(line['ldate'], '%Y-%m-%d')
                month = ""
                if line_date:
                    month = line_date.strftime("%B")
                if check_first_move_line and init_bal:
                    check_first_move_line = False
                    init_month = ""
#                     if line_date:
                    init_month = datetime.strptime(start_date, '%Y-%m-%d').strftime("%B")
                    init_vals = {
                                 'vr_no': False,
                                'vr_date': datetime.strptime(start_date, '%Y-%m-%d'),
                                'vr_type': False,
                                'partner_name': False,
                                'gl_code': False,
                                'job_ac': False,
                                'cost_center': False,
                                'debit': float(init_bal) > 0 and float(init_bal) or 0.00,
                                'credit': float(init_bal) < 0 and float(abs(init_bal)) or 0.00,
                                'balance': float(init_bal) or float(0.00),#init_bal or 0.00,
                                'remark': "OP. BALANCE",
                                'account_name':"%s / %s"%(account_obj.code, account_obj.name),
                                'amount_curr': float(init_bal_curr),
                                'curr': '',
                                'month': init_month and init_month.upper(),
                                 }
                    result.append(init_vals)
                vals = {
                        'vr_no': line.get('invoice_number', False) and \
                                        line.get('invoice_number', '') or line.get('move_name', ''),
                        'vr_date': line.get('ldate', False) and \
                                                datetime.strptime(line['ldate'], '%Y-%m-%d'),
                        'vr_type': line.get('jcode', ''),
                        'partner_name': partner_name and partner_name.upper() or '',
                        'gl_code': account_obj.code or '',
                        'job_ac': line.get('job_ac', False) and line['job_ac'] or False,
                        'cost_center': line.get('cc', ''),
                        'debit': line.get('debit', 0.00),
                        'credit': line.get('credit', 0.00),
                        'balance': line.get('balance', 0.00),
                        'remark': line.get('lname', ''),
                        'account_name':"%s / %s"%(account_obj.code, account_obj.name),
                        'amount_curr': line.get('amount_currency', 0.00),
                        'curr': line.get('currency_code', 'AED'),
                        'month': month and month.upper(),
                        }
                result.append(vals)
        return result
    
jasper_report.report_jasper('report.general_ledger.jasper', 'general.ledger.print', parser=general_ledger)
jasper_report.report_jasper('report.general_ledger_fc.jasper', 'general.ledger.print', parser=general_ledger)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

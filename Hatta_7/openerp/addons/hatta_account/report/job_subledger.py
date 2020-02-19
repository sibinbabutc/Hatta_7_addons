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
from account_financial_report_webkit.report.common_partner_reports import CommonPartnersReportHeaderWebkit

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime


class jobledger_report(JasperDataParser.JasperDataParser, CommonPartnersReportHeaderWebkit):
    def __init__(self, cr, uid, ids, data, context):
        self.cursor = cr
        super(jobledger_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        vals={}
        show_match = data['form']['include_matching_tran']
        pool= pooler.get_pool(cr.dbname)
        user_pool = pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        comp_obj = user_obj.company_id
        address = "Phone : " + comp_obj.phone + ", Fax : " + comp_obj.fax + " - P.O. Box : " + \
                            comp_obj.zip + " - " + (comp_obj.country_id and comp_obj.country_id.name)
        date_today = datetime.today().strftime("%d/%m/%Y")
        fiscalyear_id = data['form'].get('fiscalyear_id')[0]
        start_period = self._get_st_fiscalyear_period(fiscalyear_id)
        start_date = data['form']['start_date']#start_period.date_start
        job_ledger = data['form']['job_subledger']
        start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        end_date = data['form']['end_date']
        end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        report_heading = show_match and "STATEMENT OF ACCOUNT (%s - %s)"%(str(start_date), str(end_date)) or \
                                        "OUTSTANDING STATEMENT OF ACCOUNT ( %s )"%(str(end_date)) or ''
        if job_ledger:
            report_heading = show_match and "JOB LEDGER( %s)"%(str(end_date)) or \
                                    "PROFIT AND LOSS JOB LEDGER(%s - %s)"%(str(start_date), str(end_date))
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                'curr_name': comp_obj.currency_id.name,
                'report_heading': report_heading
                }
        return vals
    
    def generate_properties(self, cr, uid, ids, data, context):
        return {
            'net.sf.jasperreports.export.xls.one.page.per.sheet':'true',
            'net.sf.jasperreports.export.ignore.page.margins':'true',
            'net.sf.jasperreports.export.xls.remove.empty.space.between.rows':'true',
            'net.sf.jasperreports.export.xls.detect.cell.type': 'true',
            'net.sf.jasperreports.export.xls.white.page.background': 'true',
            'net.sf.jasperreports.export.xls.show.gridlines': 'true',
            }
    
    def _get_st_fiscalyear_period(self, fiscalyear, special=False, order='ASC'):
        period_obj = self.pool.get('account.period')
        p_id = period_obj.search(self.cr,
                                 self.uid,
                                 [('special', '=', special),
                                  ('fiscalyear_id', '=', fiscalyear)],
                                 limit=1,
                                 order='date_start %s' % (order,))
        if not p_id:
            raise osv.except_osv(_('No period found'), '')
        return period_obj.browse(self.cr, self.uid, p_id[0])
    
    def get_all_accounts(self, account_ids, exclude_type=None, only_type=None, filter_report_type=None,
                         context=None):
        """Get all account passed in params with their childrens

        @param exclude_type: list of types to exclude (view, receivable, payable, consolidation, other)
        @param only_type: list of types to filter on (view, receivable, payable, consolidation, other)
        @param filter_report_type: list of report type to filter on
        """
        context = context or {}
        accounts = []
        if not isinstance(account_ids, list):
            account_ids = [account_ids]
        acc_obj = self.pool.get('account.account')
        for account_id in account_ids:
            accounts.append(account_id)
            accounts += acc_obj._get_children_and_consol(self.cursor, self.uid, account_id, context=context)
        res_ids = list(set(accounts))
        res_ids = self.sort_accounts_with_structure(account_ids, res_ids, context=context)

        if exclude_type or only_type or filter_report_type:
            sql_filters = {'ids': tuple(res_ids)}
            sql_select = "SELECT a.id FROM account_account a"
            sql_join = ""
            sql_where = "WHERE a.id IN %(ids)s"
            if exclude_type:
                sql_where += " AND a.type not in %(exclude_type)s"
                sql_filters.update({'exclude_type': tuple(exclude_type)})
            if only_type:
                sql_where += " AND a.type IN %(only_type)s"
                sql_filters.update({'only_type': tuple(only_type)})
            if filter_report_type:
                sql_join += "INNER JOIN account_account_type t" \
                            " ON t.id = a.user_type"
                sql_join += " AND t.report_type IN %(report_type)s"
                sql_filters.update({'report_type': tuple(filter_report_type)})

            sql = ' '.join((sql_select, sql_join, sql_where))
            self.cursor.execute(sql, sql_filters)
            fetch_only_ids = self.cursor.fetchall()
            if not fetch_only_ids:
                return []
            only_ids = [only_id[0] for only_id in fetch_only_ids]
            # keep sorting but filter ids
            res_ids = [res_id for res_id in res_ids if res_id in only_ids]
        return res_ids
    
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
            aa.type as account_type,
            l.amount_currency,
            l.ref AS lref,
            l.name AS lname,
            l.doc_no AS doc_no,
            COALESCE(l.debit, 0.0) - COALESCE(l.credit, 0.0) AS balance,
            l.debit,
            l.credit,
            l.period_id AS lperiod_id,
            per.code as period_code,
            per.special AS peropen,
            l.partner_id AS lpartner_id,
            p.name AS partner_name,
            p.partner_ac_code as partner_account_code,
            m.name AS move_name,
            m.cheque_no as ref,
            COALESCE(partialrec.name, fullrec.name, '') AS rec_name,
            COALESCE(fullrec.id, NULL) AS rec_id,
            partialrec.id as prec_id,
            m.id AS move_id,
            c.name AS currency_code,
            i.id AS invoice_id,
            i.type AS invoice_type,
            i.number AS invoice_number,
            l.date_maturity,
            po.name as purchase_name
FROM account_move_line l
    JOIN account_move m on (l.move_id=m.id)
    LEFT JOIN res_currency c on (l.currency_id=c.id)
    LEFT JOIN account_account aa on aa.id = l.account_id
    LEFT JOIN account_move_reconcile partialrec on (l.reconcile_partial_id = partialrec.id)
    LEFT JOIN account_move_reconcile fullrec on (l.reconcile_id = fullrec.id)
    LEFT JOIN res_partner p on (l.partner_id=p.id)
    LEFT JOIN account_invoice i on (m.id =i.move_id)
    LEFT JOIN account_period per on (per.id=l.period_id)
    LEFT JOIN purchase_order po on po.id = i.purchase_id
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
    
    def get_partners_move_lines_ids(self, account_id, main_filter, start, stop, target_move,
                                    exclude_reconcile=False,
                                    partner_filter=False, job_id=False, cost_center=False):
        filter_from = False
        if main_filter in ('filter_period', 'filter_no'):
            filter_from = 'period'
        elif main_filter == 'filter_date':
            filter_from = 'date'
        if filter_from:
            return self._get_partners_move_line_ids(filter_from,
                                                    account_id,
                                                    start,
                                                    stop,
                                                    target_move,
                                                    exclude_reconcile=exclude_reconcile,
                                                    partner_filter=partner_filter, job_id=job_id,
                                                    cost_center=cost_center)
    
    def _get_partners_move_line_ids(self, filter_from, account_id, start, stop,
                                    target_move, opening_mode='exclude_opening',
                                    exclude_reconcile=False, partner_filter=None, job_id=False, 
                                    cost_center=False):
        """

        :param str filter_from: "periods" or "dates"
        :param int account_id: id of the account where to search move lines
        :param str or browse_record start: start date or start period
        :param str or browse_record stop: stop date or stop period
        :param str target_move: 'posted' or 'all'
        :param opening_mode: deprecated
        :param boolean exclude_reconcile: wether the reconciled entries are
            filtred or not
        :param list partner_filter: list of partner ids, will filter on their
            move lines
        """
        final_res = defaultdict(list)

        sql_select = "SELECT account_move_line.id, account_move_line.partner_id FROM account_move_line"
        sql_joins = ''
        sql_where = " WHERE account_move_line.account_id = %(account_ids)s " \
                    " AND account_move_line.state = 'valid' "

        method = getattr(self, '_get_query_params_from_' + filter_from + 's')
        sql_conditions, search_params = method(start, stop)

        sql_where += sql_conditions

        if exclude_reconcile:
            sql_where += ("  AND ((account_move_line.reconcile_id IS NULL)"
                         "   OR (account_move_line.reconcile_id IS NOT NULL AND account_move_line.last_rec_date > date(%(date_stop)s)))")

        if partner_filter:
            sql_where += "   AND account_move_line.partner_id in %(partner_ids)s"

        if target_move == 'posted':
            sql_joins += "INNER JOIN account_move ON account_move_line.move_id = account_move.id"
            sql_where += " AND account_move.state = %(target_move)s"
            search_params.update({'target_move': target_move})
        if job_id:
            sql_where += " AND account_move_line.job_id = %(job_id)s"
            search_params.update({'job_id': job_id})
            
        if cost_center:
            sql_where += " AND account_move_line.analytic_account_id = %(cost_center)s"
            search_params.update({'cost_center': cost_center})

        search_params.update({
            'account_ids': account_id,
            'partner_ids': tuple(partner_filter),
        })

        sql = ' '.join((sql_select, sql_joins, sql_where))
        self.cursor.execute(sql, search_params)
        res = self.cursor.dictfetchall()
        if res:
            for row in res:
                final_res[row['partner_id']].append(row['id'])
        return final_res
    
    def _compute_partners_initial_balances(self, account_ids, start_date, partner_filter=None,
                                           exclude_reconcile=False, force_period_ids=False, job_id=False,
                                           cost_center_id=False):
        """We compute initial balance.
        If form is filtered by date all initial balance are equal to 0
        This function will sum pear and apple in currency amount if account as no secondary currency"""
        
        if isinstance(account_ids, (int, long)):
            account_ids = [account_ids]
        move_line_ids = self._partners_initial_balance_line_ids(account_ids, start_date, partner_filter,
                                                                exclude_reconcile=exclude_reconcile,
                                                                force_period_ids=force_period_ids)
        if not move_line_ids:
            move_line_ids = [{'id': -1}]
        if not job_id:
            job_ids = self.pool.get('job.account').search(self.cr, self.uid, [])
            sql = ("SELECT ml.account_id, ml.partner_id,"
                       "       sum(ml.debit) as debit, sum(ml.credit) as credit,"
                       "       sum(ml.debit-ml.credit) as init_balance,"
                       "       CASE WHEN a.currency_id ISNULL THEN 0.0 ELSE sum(ml.amount_currency) END as init_balance_currency, "
                       "       c.name as currency_name "
                       "FROM account_move_line ml "
                       "INNER JOIN account_account a "
                       "ON a.id = ml.account_id "
                       "LEFT JOIN res_currency c "
                       "ON c.id = a.currency_id "
                       "WHERE ml.id in %(move_line_ids)s and ml.job_id in %(job_ids)s"
                       "GROUP BY ml.account_id, ml.partner_id, a.currency_id, c.name")
            
            search_param = {'move_line_ids': tuple([move_line['id'] for move_line in move_line_ids]),
                        'job_ids': tuple(job_ids)}
        else:
            sql = ("SELECT ml.account_id, ml.partner_id,"
                       "       sum(ml.debit) as debit, sum(ml.credit) as credit,"
                       "       sum(ml.debit-ml.credit) as init_balance,"
                       "       CASE WHEN a.currency_id ISNULL THEN 0.0 ELSE sum(ml.amount_currency) END as init_balance_currency, "
                       "       c.name as currency_name "
                       "FROM account_move_line ml "
                       "INNER JOIN account_account a "
                       "ON a.id = ml.account_id "
                       "LEFT JOIN res_currency c "
                       "ON c.id = a.currency_id "
                       "WHERE ml.id in %(move_line_ids)s and ml.job_id = %(job_id)s"
                       "GROUP BY ml.account_id, ml.partner_id, a.currency_id, c.name")
            
            search_param = {'move_line_ids': tuple([move_line['id'] for move_line in move_line_ids]),
                        'job_id': job_id}
        self.cursor.execute(sql, search_param)
        res = self.cursor.dictfetchall()
        return self._tree_move_line_ids(res)
    
    def _partners_initial_balance_line_ids(self, account_ids, start_date, partner_filter,
                                           exclude_reconcile=False, force_period_ids=False,
                                           date_stop=None, job_id=False, costcenter_id=False):
        # take ALL previous periods
#         period_ids = force_period_ids \
#                      if force_period_ids \
#                      else self._get_period_range_from_start_period(start_period, fiscalyear=False, include_opening=False)
# 
#         if not period_ids:
#             period_ids = [-1]
        search_param = {
                'date_stop': date_stop,
                'date_start': start_date.strftime("%Y-%m-%d"),
                #'period_ids': tuple(period_ids),
                'account_ids': tuple(account_ids),
            }
        sql = ("SELECT ml.id, ml.account_id, ml.partner_id "
               "FROM account_move_line ml "
               "INNER JOIN account_account a "
               "ON a.id = ml.account_id "
               "WHERE ml.account_id in %(account_ids)s and ml.date < %(date_start)s")
#         if exclude_reconcile:
#             if not date_stop:
#                 raise Exception("Missing \"date_stop\" to compute the open invoices.")
#             search_param.update({'date_stop': date_stop})
#             sql += ("AND ((ml.reconcile_id IS NULL)"
#                    "OR (ml.reconcile_id IS NOT NULL AND ml.last_rec_date > date(%(date_stop)s))) ")
        if partner_filter:
            sql += "AND ml.partner_id in %(partner_ids)s "
            search_param.update({'partner_ids': tuple(partner_filter)})
        if job_id:
            sql += "AND ml.job_id = %(job_id)s"
            search_param.update({'job_id': job_id})
        if costcenter_id:
            sql += " AND ml.analytic_account_id = %(cost_center)s"
            search_params.update({'cost_center': costcenter_id})
        self.cursor.execute(sql, search_param)
        return self.cursor.dictfetchall()
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        partner_pool = self.pool.get('res.partner')
        move_line_pool = self.pool.get('account.move.line')
        job_pool = self.pool.get('job.account')
        form_data = data['form']
        job_ledger= form_data['job_subledger']
        job_data = form_data['job_id']
        date_start = form_data['start_date']
        date_end = form_data['end_date']
        cost_center = form_data['cost_center_id'] and form_data['cost_center_id'][0] or False
        job_id = False
        if job_ledger and job_data:
            job_id=job_data[0]
            job_obj = job_pool.browse(cr, uid, job_id, context=context)
        account_ids = []
        account_data = form_data.get('account_id', False)
        chart_id = form_data['chart_account_id'][0]
        filter_type = ('income', 'expense')
        if account_data:
            account_ids = [account_data[0]]
        else:
            account_ids = self.get_all_accounts(chart_id, exclude_type=['view'],
                                                filter_report_type=filter_type)
        partner_ids = []
        partner_data = form_data.get('partner_id', False)
        if partner_data:
            partner_ids = [partner_data[0]]
        self.cursor = cr
        partner_balance = {}
        ini_bal_done = {}
        for account in account_ids:
            partner_move_line_data = self.get_partners_move_lines_ids(account, 'filter_date', date_start,
                                                                      date_end, 'all', False,
                                                                      partner_ids, job_id, cost_center)
            for partner_id in partner_move_line_data:
                initial_line = {}
                real_partner_name = ''
                if job_id:
                    real_partner_name = job_obj.name
                if not ini_bal_done.get(partner_id, False):
                    start_date = datetime.strptime(date_start, "%Y-%m-%d")
                    ini_bal_done[partner_id] = True
                    filter_partner_ids = []
#                     if partner_id:
#                         filter_partner_ids= [partner_id]
                    initial_balance = self._compute_partners_initial_balances(account_ids,
                                                                              start_date,
                                                                              partner_filter=filter_partner_ids,
                                                                              job_id=job_id,
                                                                              exclude_reconcile=False)
                    open_debit = 0.00
                    open_credit = 0.00
                    for open_account in account_ids:
                        partner_data = initial_balance.get(open_account, {})
                        move_data = partner_data.get(partner_id, {})
                        open_debit += move_data.get('debit', 0.00)
                        open_credit += move_data.get('credit', 0.00)
                    if open_debit != 0.00 or open_credit != 0.00:
                        balance = open_credit - open_debit
                        credit = debit = 0.00
                        if balance > 0.00:
                            credit = balance
                        elif balance < 0.00:
                            debit = balance
                        initial_line = {
                                        'customer_name': real_partner_name,
                                        'date': start_date,
                                        'curr': 'AED',
                                        'amount_curr': 0.00,
                                        'debit': abs(debit),
                                        'credit': abs(credit),
                                        'balance': balance,
                                        'remark': "OPENING BALANCE",
                                        }
                        result.append(initial_line)
                if not partner_balance.has_key(partner_id):
                    partner_balance[partner_id] = 0.00
                partner_line_ids = partner_move_line_data.get(partner_id, [])
                lines = self._get_move_line_datas(list(set(partner_line_ids)))
                partner_address = ''
                if job_ledger and job_id:
                    partner_address = job_obj.job_short_desc or ''
                cumm_balance = partner_balance[partner_id]
                reconsile_line = []
                real_line = []
                proceed_line = []
                review_line = []
                review_dict = {}
                for line in lines:
                    move_id = line.get('id', False)
                    move_line_obj = move_line_pool.browse(cr, uid, move_id, context=context)
                    account_move_id = move_line_obj.move_id.id
                    debit = line.get('debit', 0.00)
                    credit = line.get('credit', 0.00)
                    balance = debit - credit
                    sign = 1.00
                    balance = balance * sign
                    if move_line_obj.move_id.journal_id.display_in_voucher:
                        real_line.append(line)
                    else:
                        if account_move_id not in review_line:
                            review_vals = line.copy()
                            review_vals.update({
                                                'lname': move_line_obj.move_id.ref
                                                })
                            review_line.append(account_move_id)
                            review_dict[account_move_id] = review_vals
                        else:
                            debit = move_line_obj.debit or 0.00
                            credit = move_line_obj.credit or 0.00
                            amount_curr = move_line_obj.amount_currency or 0.00
                            review_dict[account_move_id]['credit'] += credit
                            review_dict[account_move_id]['debit'] += debit
                            review_dict[account_move_id]['amount_currency'] += amount_curr
                real_line.extend([review_dict[x] for x in review_dict])
                for line in real_line:
                    debit = line.get('debit', 0.00)
                    credit = line.get('credit', 0.00)
                    balance = credit - debit
                    if round(balance, 2) != 0.00:
#                         balance = balance * sign
                        credit = debit = 0.00
                        if balance > 0.00:
                            credit = balance
                        else:
                            debit = balance
                        partner_name = line.get('partner_name', '') and line.get('partner_name', '').upper()
                        partner_code = line.get('partner_account_code', '') and \
                                                 line.get('partner_account_code', '').upper()
                        real_partner_name = ''
                        if not job_ledger:
                            if partner_code:
                                real_partner_name += partner_code + "\n" + partner_name
                            else:
                                real_partner_name = partner_name
                        elif job_ledger and job_id:
                            real_partner_name = job_obj.name or ''
                        purchase_no = line.get('purchase_name', False)
                        if purchase_no:
                            line_name = "PURCHASE #: %s, SUPPLIER : %s"%(purchase_no,
                                                                         partner_name)
                        else:
                            line_name = line.get('lname', '')
                        vals = {
                                'customer_name': real_partner_name,
                                'date': line.get('ldate', False) and \
                                               datetime.strptime(line['ldate'], '%Y-%m-%d'),
                                'doc_no': line.get('invoice_number', False) or line.get('doc_no', False) or \
                                            line.get('move_name', False) or '',
                                'curr': line.get('currency_code', False) or 'AED',
                                'amount_curr': line.get('amount_currency', 0.00),
                                'debit': abs(debit) or 0.00,
                                'credit': abs(credit) or 0.00,
                                'balance': balance,
                                'remark': line_name,
                                'ref': line.get('ref', '') or '',
                                'partner_address': partner_address and partner_address.upper() or '',
                                'd_30': 0.00,
                                'd_60': 0.00,
                                'd_90': 0.00,
                                'd_120': 0.00,
                                'other': 0.00,
                                }
                        due_date = line.get('ldate', False)
                        date_maturity = line.get('date_maturity', False)
                        if date_end and date_maturity:
                            date_end = datetime.strptime(str(date_end)[:10], '%Y-%m-%d')
                            due_date = datetime.strptime(due_date, '%Y-%m-%d')
                            
                            due_days = (date_end - due_date).days
                            if float(due_days) <= 30.00:
                                vals['d_30'] += balance
                            elif float(due_days) <= 60.00 and float(due_days) >= 31.00:
                                vals['d_60'] += balance
                            elif float(due_days) <= 90.00 and float(due_days) >= 61.00:
                                vals['d_90'] += balance
                            elif float(due_days) <= 120.00 and float(due_days) >= 91.00:
                                vals['d_120'] += balance
                            elif float(due_days) >= 121.00:
                                vals['other'] += balance
                        result.append(vals)
        return result
    
jasper_report.report_jasper('report.job.subledger.jasper', 'subledger.print', parser=jobledger_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

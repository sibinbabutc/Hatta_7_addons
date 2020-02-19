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
from jasper_reports import jasper_report

import pooler
from osv import fields, osv
from openerp.tools import amount_to_text_en
import time
from datetime import datetime
from operator import itemgetter
import operator
from account.report.account_aged_partner_balance import aged_trial_report
from openerp.tools import float_is_zero


class subledger_report(JasperDataParser.JasperDataParser, aged_trial_report):
    def __init__(self, cr, uid, ids, data, context):
        self.total_account = []
        super(subledger_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
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
                                    "OUTSTANDING JOB LEDGER(%s - %s)"%(str(start_date), str(end_date))
        vals = {
                'company_name': comp_obj.name or '',
                'company_address': address,
                'company_email': "E-mail :" + comp_obj.email or '',
                'curr_name': comp_obj.currency_id.name,
                'report_heading': report_heading
                }
        if data['report_type'] == 'xls':
            vals['IS_IGNORE_PAGINATION'] = True
        return vals
    
    def _get_lines(self, form):
        res = []
        opening_bal_dict = {}
        partner_pool = self.pool.get('res.partner')
        show_match = form['include_matching_tran']
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        self.cr.execute('SELECT DISTINCT res_partner.id AS id,\
                    res_partner.name AS name \
                FROM res_partner,account_move_line AS l, account_account, account_move am\
                WHERE (l.account_id=account_account.id) \
                    AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s OR account_account.include_subledger=TRUE)\
                    AND account_account.active\
                    AND (l.partner_id=res_partner.id)\
                    AND (l.date <= %s)\
                    AND ' + self.query + ' \
                ORDER BY res_partner.name', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from,))
        partners = self.cr.dictfetchall()
        ## mise a 0 du total
        for i in range(7):
            self.total_account.append(0)
        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [x['id'] for x in partners]
        if not partner_ids:
            return []
        # This dictionary will store the debit-credit for all partners, using partner_id as key.
        totals = {}
        self.cr.execute('SELECT l.partner_id, SUM(l.debit-l.credit), l.id \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s OR account_account.include_subledger=TRUE)\
                    AND (l.partner_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND ' + self.query + '\
                    AND account_account.active\
                    AND (l.date <= %s)\
                    GROUP BY l.partner_id,l.id ', (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(partner_ids), self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            totals[i[0]] = i[1]

        # This dictionary will store the future or past of all partners
        future_past = {}
        if self.direction_selection == 'future':
            self.cr.execute('SELECT l.partner_id, SUM(l.debit-l.credit), l.id \
                        FROM account_move_line AS l, account_account, account_move am \
                        WHERE (l.account_id=account_account.id) AND (l.move_id=am.id) \
                        AND (am.state IN %s)\
                        AND (account_account.type IN %s  OR account_account.include_subledger=TRUE)\
                        AND (COALESCE(l.date_maturity, l.date) < %s)\
                        AND (l.partner_id IN %s)\
                        AND ((l.reconcile_id IS NULL)\
                        OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                        AND '+ self.query + '\
                        AND account_account.active\
                    AND (l.date <= %s)\
                        GROUP BY l.partner_id,l.id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(partner_ids),self.date_from, self.date_from,))
            t = self.cr.fetchall()
            for i in t:
                future_past[i[0]] = i[1]
        elif self.direction_selection == 'past': # Using elif so people could extend without this breaking
            self.cr.execute('SELECT l.partner_id, SUM(l.debit-l.credit), l.id \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id=account_account.id) AND (l.move_id=am.id)\
                        AND (am.state IN %s)\
                        AND (account_account.type IN %s OR account_account.include_subledger=TRUE)\
                        AND (COALESCE(l.date_maturity,l.date) > %s)\
                        AND (l.partner_id IN %s)\
                        AND ((l.reconcile_id IS NULL)\
                        OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                        AND '+ self.query + '\
                        AND account_account.active\
                    AND (l.date <= %s)\
                        GROUP BY l.partner_id, l.id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(partner_ids), self.date_from, self.date_from,))
            t = self.cr.fetchall()
            for i in t:
                future_past[i[0]] = i[1]

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        reconsile_line = []
        real_line = []
        reco_data = {}
        all_data = {}
        for i in range(5):
            args_list = (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(partner_ids))
            dates_query = '(COALESCE(l.date)'
            print form[str(i)]
            if form[str(i)]['start'] and form[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (form[str(i)]['start'], form[str(i)]['stop'])
            elif form[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (form[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (form[str(i)]['stop'],)
            args_list += (self.date_from,)
            print dates_query,"------------->Date Query"
            print args_list,"------------->Args List"
            print self.query
            account_query = ''
            if form['account_id']:
                account_query = 'AND account_account.id = %s'%(str(form['account_id'][0]))
            self.cr.execute('''SELECT rp.name as partner_name,
                    rp.partner_ac_code as partner_code,
                    SUM(l.debit-l.credit) as balance,
                    am.cheque_no as ref,
                    l.name as remark,
                    l.date_maturity as due_date,
                    l.analytic_account_id as cost_center,
                     rp.id as partner_id,
                    l.date as doc_date,
                    account_account.type as account_type,
                    l.reconcile_partial_id as rec_partial_id,
                    l.reconcile_id as rec_id,
                    rc.name as currency_code,
                    l.amount_currency as amount_currency,
                    (case when ai.name is not null and ai.type = 'out_refund' then ai.name
                    else l.name end) as lname, 
                    ai.number as invoice_number,
                    l.doc_no as doc_no,
                    am.name as move_name,
                    am.skip_check as skip_check
                    from account_move_line l
                    left join account_account as account_account on account_account.id = l.account_id
                    left join account_move am on am.id=l.move_id
                    left join res_partner rp on rp.id=l.partner_id
                    left join res_currency rc on rc.id=l.currency_id
                    left join account_invoice ai on ai.move_id = am.id
                    WHERE (am.state IN %s)
                        AND (account_account.type IN %s)
                        AND (l.partner_id IN %s)
                        AND ''' + self.query + '''
                        AND account_account.active
                        AND''' + dates_query + account_query +'''
                    AND (l.date <= %s)
                    GROUP BY rp.name, rp.partner_ac_code, am.cheque_no, l.name, l.date_maturity,
                    l.analytic_account_id, rp.id, l.date, account_account.type, l.reconcile_partial_id,
                    rc.name, l.amount_currency,l.name,ai.number,l.doc_no,am.name,ai.name,ai.type,
                    l.reconcile_id, am.skip_check''', args_list)
            t = self.cr.dictfetchall()
            d = {}
            for j in t:
                account_type = j['account_type']
                sign = 1.00
                if account_type == 'payable':
                    sign = -1.00
                j['range'] = i
                rec_id = j.get('rec_id', False)
                rec_partial_id = j.get('rec_partial_id', False) or rec_id or False
                balance = round(j.get('balance', 0.00), 2)
                if float_is_zero(balance, precision_rounding=0.01):
                    continue
#                 balance = balance * sign
#                 j['balance'] = balance
                if show_match:
                    if not j['skip_check']:
                        real_line.append(j)
                    continue
                if rec_partial_id:
#                     if balance < 0.00:
                    reconsile_line.append(j)
                    if not reco_data.get(rec_partial_id, False):
                        reco_data[rec_partial_id] = 0.00
                    reco_data[rec_partial_id] += balance
#                     else:
#                         real_line.append(j)
                else:
                    real_line.append(j)
            all_data[i] = t
        opening_credit = 0.00
        opening_debit = 0.00
        for j in real_line:
            i = j['range']
            rec_id = j.get('rec_id', False)
            rec_partial_id = j.get('rec_partial_id', False) or rec_id or False
            rec_value = reco_data.get(rec_partial_id, 0.00)
            balance = j.get('balance', 0.00)
            if rec_value == abs(balance):
                balance = 0.00
                reco_data[rec_partial_id] = 0.00
            elif rec_value < abs(balance):
                balance = balance + rec_value
                reco_data[rec_partial_id] = 0.00
            elif rec_value > abs(balance):
                balance = 0.00
                reco_data[rec_partial_id] = rec_value + balance
            if balance != 0.00:
                partner_id = j.get('partner_id', False)
                partner_address = ''
                if partner_id:
                    partner_obj = partner_pool.browse(self.cr, self.uid, partner_id, context={})
                    partner_address = partner_pool._display_address(self.cr, self.uid, partner_obj,
                                                                    context={})
                    partner_address_list = partner_address.split("\n")
                    new_partner_address_list = []
                    for partner in partner_address_list:
                        if partner:
                            new_partner_address_list.append(partner)
                    partner_address = "\n".join(new_partner_address_list)
                partner_name = j.get('partner_name', '')
                partner_code = j.get('partner_code', False)
                if partner_code:
                    partner_name = "[%s] %s"%(partner_code, partner_name)
                cost_center = j.get('cost_center', False)
                account_type = j.get('account_type', '')
                cc_code = ''
                debit = credit = 0.00
                if balance < 0.00:
                    credit = abs(balance)
                elif balance > 0.00:
                    debit = balance
                if cost_center:
                    cost_center_obj = self.pool.get('account.analytic.account').browse(self.cr, self.uid, cost_center)
                    cc_code = cost_center_obj.code or ''
                if j['doc_date'] < form['start_date']:
                    if not opening_bal_dict.has_key(partner_name):
                        opening_bal_dict[partner_name] = {
                                                          'partner_address': partner_address,
                                                          'opening_debit': 0.00,
                                                          'opening_credit': 0.00
                                                          }
                    opening_bal_dict[partner_name]['opening_credit'] += credit
                    opening_bal_dict[partner_name]['opening_debit'] += debit
                    continue
                if debit == 0.00 and credit == 0.00:
                    continue
                vals = {
                        'customer_name': partner_name,
                        'date': j.get('doc_date', False) and \
                                       datetime.strptime(j['doc_date'], '%Y-%m-%d'),
                        'doc_no': j.get('invoice_number', False) or j.get('doc_no', False) or \
                                            j.get('move_name', False) or '',
                        'curr': j.get('currency_code', False) or 'AED',
                        'amount_curr': j.get('amount_currency', 0.00),
                        'debit': debit or 0.00,
                        'credit': credit or 0.00,
                        'balance': debit - credit,
                        'remark': j.get('lname', ''),
                        'ref': j.get('ref', '') or '',
                        'partner_address': partner_address and partner_address.upper() or '',
                        'd_0': 0.00,
                        'd_1': 0.00,
                        'd_2': 0.00,
                        'd_3': 0.00,
                        'd_3': 0.00,
                        'show_match': show_match and "true" or "false"
                        }
                if j.get('due_date'):
                    vals["d_%s"%(str(i))] = abs(balance)
                vals['bal'] = balance
                res.append(vals)
        
        
        
        for j in reconsile_line:
            rec_id = j.get('rec_id', False)
            rec_partial_id = j.get('rec_partial_id', False) or rec_id or False
            balance = reco_data.get(rec_partial_id, 0.00)
            reco_data[rec_partial_id] = 0.00
            if balance != 0.00:
                partner_name = j.get('partner_name', '')
                partner_code = j.get('partner_code', False)
                partner_id = j.get('partner_id', False)
                partner_address = ''
                if partner_id:
                    partner_obj = partner_pool.browse(self.cr, self.uid, partner_id, context={})
                    partner_address = partner_pool._display_address(self.cr, self.uid, partner_obj,
                                                                    context={})
                    partner_address_list = partner_address.split("\n")
                    new_partner_address_list = []
                    for partner in partner_address_list:
                        if partner:
                            new_partner_address_list.append(partner)
                    partner_address = "\n".join(new_partner_address_list)
                if partner_code:
                    partner_name = "[%s] %s"%(partner_code, partner_name)
                cost_center = j.get('cost_center', False)
                account_type = j.get('account_type', '')
                cc_code = ''
                if cost_center:
                    cost_center_obj = self.pool.get('account.analytic.account').browse(self.cr, self.uid, cost_center)
                    cc_code = cost_center_obj.code or ''
                debit = credit = 0.00
                if balance < 0.00:
                    credit = abs(balance)
                elif balance > 0.00:
                    debit = balance
                if j['doc_date'] < form['start_date']:
                    if not opening_bal_dict.has_key(partner_name):
                        opening_bal_dict[partner_name] = {
                                                          'partner_address': partner_address,
                                                          'opening_debit': 0.00,
                                                          'opening_credit': 0.00
                                                          }
                    opening_bal_dict[partner_name]['opening_credit'] += credit
                    opening_bal_dict[partner_name]['opening_debit'] += debit
                    continue
                if debit == 0.00 and credit == 0.00:
                    continue
                vals = {
                        'customer_name': partner_name,
                        'date': j.get('doc_date', False) and \
                                       datetime.strptime(j['doc_date'], '%Y-%m-%d'),
                        'doc_no': j.get('invoice_number', False) or j.get('doc_no', False) or \
                                            j.get('move_name', False) or '',
                        'curr': j.get('currency_code', False) or 'AED',
                        'amount_curr': j.get('amount_currency', 0.00),
                        'debit': debit or 0.00,
                        'credit': credit or 0.00,
                        'balance': debit - credit,
                        'remark': j.get('lname', ''),
                        'ref': j.get('ref', '') or '',
                        'partner_address': partner_address and partner_address.upper() or '',
                        'd_0': 0.00,
                        'd_1': 0.00,
                        'd_2': 0.00,
                        'd_3': 0.00,
                        'd_3': 0.00,
                        'show_match': show_match and "true" or "false"
                        }
#                     balance = j.get('balance', 0.00)
                res.append(vals)
                if j.get('due_date'):
                    vals["d_%s"%(str(i))] = abs(balance)
                vals['bal'] = balance
        for partner_name in opening_bal_dict:
            opening_debit = opening_bal_dict[partner_name]['opening_debit']
            opening_credit = opening_bal_dict[partner_name]['opening_credit']
            partner_address = opening_bal_dict[partner_name]['partner_address']
            if opening_debit != 0.00 or opening_credit != 0.00:
                vals = {
                        'customer_name': partner_name,
                        'date': datetime.strptime(form['start_date'], '%Y-%m-%d'),
                        'doc_no': '',
                        'curr': 'AED',
                        'amount_curr': 0.00,
                        'debit': opening_debit or 0.00,
                        'credit': opening_credit or 0.00,
                        'balance': opening_debit - opening_credit,
                        'remark': "OPENING BALANCE",
                        'ref': '',
                        'partner_address': partner_address and partner_address.upper() or '',
                        'd_0': 0.00,
                        'd_1': 0.00,
                        'd_2': 0.00,
                        'd_3': 0.00,
                        'd_3': 0.00,
                        'show_match': show_match and "true" or "false"
                        }
                res.append(vals)
        return res
    
    def set_context(self, cr, uid, data, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        obj_move = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        ctx.update({'fiscalyear': False, 'all_fiscalyear': True})
        partner_ids = []
        if data['form'].get('partner_id', False) and not data['form'].get('partner_id_to', False):
            partner_ids = [data['form']['partner_id'][0]]
            ctx['partner_ids'] = partner_ids
        if data['form'].get('cost_center_id', False):
            query = """
            select aml.partner_id from account_move_line aml left join account_move am on am.id=aml.move_id left join account_account aa on aa.id=aml.account_id where aa.type in ('receivable', 'payable') and aml.analytic_account_id=%s and aml.partner_id is not null and am.skip_check=false
            """%(str(data['form']['cost_center_id'][0]))
            cr.execute(query)
            partner_ids = map(lambda x: x[0], cr.fetchall())
            partner_ids = list(set(partner_ids))
            if not partner_ids:
                partner_ids = []
            ctx['partner_ids'] = partner_ids
        if not data['form'].get('partner_id', False) and data['form'].get('partner_id_to', False):
            partner_ids = [data['form']['partner_id_to'][0]]
            ctx['partner_ids'] = partner_ids
        if data['form'].get('partner_id', False) and data['form'].get('partner_id_to', False):
            partner_id_from = data['form'].get('partner_id', False)[0]
            partner_id_to = data['form'].get('partner_id_to', False)[0]
            partner_id_from_code = partner_pool.browse(cr, uid, partner_id_from).partner_ac_code
            partner_id_to_code = partner_pool.browse(cr, uid, partner_id_to).partner_ac_code
            full_part_ids = partner_pool.search(cr, uid, [('parent_id', '=', False)], context=context)
            partner_ids = []
            for partner_obj in partner_pool.browse(cr, uid, full_part_ids, context=context):
                code = partner_obj.partner_ac_code
                if partner_id_from_code <= code <= partner_id_to_code:
                    partner_ids.append(partner_obj.id)
            ctx['partner_ids'] = partner_ids
        self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=ctx)
        self.direction_selection = 'past'
        self.target_move = 'all'
        self.date_from = data['form'].get('end_date', time.strftime('%Y-%m-%d'))
        self.ACCOUNT_TYPE = ['payable','receivable']
        display_all = False
        for partner_obj in partner_pool.browse(cr, uid, partner_ids, context=context):
            if partner_obj.is_employee:
                display_all = True
                break
        if data['form']['account_id'] or display_all:
            self.ACCOUNT_TYPE = ['payable', 'receivable']
        return True
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        self.set_context(cr, uid, data, ids, context=context)
        result = self._get_lines(data['form'])
        result = sorted(result, key=operator.itemgetter('customer_name', 'date'))
        return result
    
jasper_report.report_jasper('report.subledger.jasper', 'subledger.print', parser=subledger_report)
jasper_report.report_jasper('report.subledger.jasper.xls', 'subledger.print', parser=subledger_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

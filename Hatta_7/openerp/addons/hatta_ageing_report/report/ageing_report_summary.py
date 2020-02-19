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


class aging_report(JasperDataParser.JasperDataParser, aged_trial_report):
    def __init__(self, cr, uid, ids, data, context):
        self.total_account = []
        data['report_type'] = data['form']['report_type']
        super(aging_report, self).__init__(cr, uid, ids, data, context)
        
    def generate_data_source(self, cr, uid, ids, data, context):
        return 'xml_records'
    
    def generate_parameters(self, cr, uid, ids, data, context):
        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, uid, uid, context=context)
        date_start = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        date = datetime.strptime(data['form']['report_date'], '%Y-%m-%d').strftime("%d/%m/%Y")
        print_type = data['form'].get('print_type', 'customer_supplier')
        if print_type == 'customer':
            header = "DEBTORS AGEING SUMMARY [INCL. PDC] AS ON %s"%(str(date))
        elif print_type == 'supplier':
            header = "CREDITOR AGEING SUMMARY [INCL. PDC] AS ON %s"%(str(date))
        else:
            header = "AGEING SUMMARY [INCL. PDC] AS ON %s"%(str(date))
        vals = {
                'header': header,
                'company_name': user_obj.company_id.name or '',
                'run': date_start,
                'user_name': user_obj.name or ''
                }
        if data['form']['report_type'] == 'xls':
            vals['IS_IGNORE_PAGINATION'] = True
        return vals
    
    def _get_lines(self, form):
        res = []
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        self.cr.execute('SELECT DISTINCT res_partner.id AS id,\
                    res_partner.name AS name \
                FROM res_partner,account_move_line AS l, account_account, account_move am\
                WHERE (l.account_id=account_account.id) \
                    AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s)\
                    AND account_account.active\
                    AND ((reconcile_id IS NULL)\
                       OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND (l.partner_id=res_partner.id)\
                    AND (l.date <= %s)\
                    AND ' + self.query + ' \
                ORDER BY res_partner.name', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, self.date_from,))
        partners = self.cr.dictfetchall()
        ## mise a 0 du total
        for i in range(7):
            self.total_account.append(0)
        #
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
                    AND (account_account.type IN %s)\
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
                        AND (account_account.type IN %s)\
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
                        AND (account_account.type IN %s)\
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
        partner_data = {}
        for i in range(5):
            args_list = (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(partner_ids),self.date_from,)
            dates_query = '(COALESCE(l.date)'
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
            self.cr.execute('''SELECT rp.name as partner_name, rp.partner_ac_code as partner_code,
                    SUM(l.debit-l.credit) as balance, l.doc_no as ref, l.name as remark,
                    l.date_maturity as due_date, l.analytic_account_id as cost_center, rp.id as partner_id,
                    l.date as doc_date, account_account.type as account_type,
                    l.reconcile_partial_id as rec_partial_id, l.reconcile_id as rec_id
                    FROM account_move_line AS l, account_account, account_move am, res_partner rp
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id) and (rp.id=l.partner_id)
                        AND (am.state IN %s)
                        AND (account_account.type IN %s)
                        AND (l.partner_id IN %s)
                        AND ((l.reconcile_id IS NULL)
                          OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))
                        AND ''' + self.query + '''
                        AND account_account.active
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    GROUP BY rp.name, rp.partner_ac_code, l.doc_no, l.name, l.date_maturity, l.analytic_account_id, rp.id, l.date, account_account.type, l.reconcile_partial_id, l.reconcile_id''', args_list)
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
                balance = balance * sign
                j['balance'] = balance
                if rec_partial_id:
                    if balance < 0.00:
                        reconsile_line.append(j)
                        if not reco_data.get(rec_partial_id, False):
                            reco_data[rec_partial_id] = 0.00
                        reco_data[rec_partial_id] += balance
                    else:
                        real_line.append(j)
                else:
                    real_line.append(j)
            all_data[i] = t
        print reco_data
        print real_line
        for j in real_line:
            i = j['range']
            rec_id = j.get('rec_id', False)
            rec_partial_id = j.get('rec_partial_id', False) or rec_id or False
            rec_value = reco_data.get(rec_partial_id, 0.00)
            balance = j.get('balance', 0.00)
            if balance == 0.00:
                continue
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
                partner_name = j.get('partner_name', '')
                partner_code = j.get('partner_code', False)
#                 if partner_code:
#                     partner_name = "[%s] %s"%(partner_code, partner_name)
                if not partner_data.get(partner_name, False):
                    partner_data[partner_name] = {
                                                  'partner': partner_name,
                                                  'code': partner_code and partner_code or '',
                                                  'pt_0': 0.00,
                                                  'pt_1': 0.00,
                                                  'pt_2': 0.00,
                                                  'pt_3': 0.00,
                                                  'pt_4': 0.00,
                                                  'unmatched': 0.00,
                                                  'bal': 0.00
                                                  }
                account_type = j.get('account_type', '')
#                 balance = j.get('balance', 0.00)
#                 if account_type == 'payable' and balance > 0.00:
#                     vals['unmatched'] += balance
#                     balance = 0.00
                if balance < 0.00:
                    partner_data[partner_name]['unmatched'] += balance * -1
                else:
                    partner_data[partner_name]["pt_%s"%(str(i))] += (balance)
                partner_data[partner_name]['bal'] += balance
        for j in reconsile_line:
            rec_id = j.get('rec_id', False)
            rec_partial_id = j.get('rec_partial_id', False) or rec_id or False
            balance = reco_data.get(rec_partial_id, 0.00)
            if balance != 0.00:
                partner_name = j.get('partner_name', '')
                partner_code = j.get('partner_code', False)
                if not partner_data.get(partner_name, False):
                    partner_data[partner_name] = {
                                                  'partner': partner_name,
                                                  'code': partner_code and partner_code or '',
                                                  'pt_0': 0.00,
                                                  'pt_1': 0.00,
                                                  'pt_2': 0.00,
                                                  'pt_3': 0.00,
                                                  'pt_4': 0.00,
                                                  'unmatched': 0.00,
                                                  'bal': 0.00
                                                  }
#                 if partner_code:
#                     partner_name = "[%s] %s"%(partner_code, partner_name)
                cost_center = j.get('cost_center', False)
                account_type = j.get('account_type', '')
                cc_code = ''
                if cost_center:
                    cost_center_obj = self.pool.get('account.analytic.account').browse(self.cr, self.uid, cost_center)
                    cc_code = cost_center_obj.code or ''
                partner_data[partner_name]['unmatched'] += balance * -1
                partner_data[partner_name]['bal'] += balance * -1
        for partner in partner_data:
            real_data = partner_data[partner]
            data = real_data.copy()
            data['partner_name'] = partner
            res.append(data)
        return res
    
    def set_context(self, cr, data, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        obj_move = self.pool.get('account.move.line')
        ctx.update({'fiscalyear': False, 'all_fiscalyear': True})
        if data['form'].get('account_analytic_id', False):
            query = """
            select aml.partner_id from account_move_line aml left join account_move am on am.id=aml.move_id left join account_account aa on aa.id=aml.account_id where aa.type in ('receivable', 'payable') and aml.analytic_account_id=%s and aml.partner_id is not null and am.skip_check is not true
            """%(str(data['form']['account_analytic_id'][0]))
            cr.execute(query)
            partner_ids = map(lambda x: x[0], cr.fetchall())
            partner_ids = list(set(partner_ids))
            if not partner_ids:
                partner_ids = [0]
            ctx['partner_ids'] = partner_ids
        if data['form'].get('partner_id', False):
            ctx['partner_ids'] = [data['form']['partner_id'][0]]
        self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=ctx)
        self.direction_selection = 'past'
#         self.target_move = 'all'
        self.target_move = 'posted'
        self.date_from = data['form'].get('report_date', time.strftime('%Y-%m-%d'))
        if (data['form']['print_type'] == 'customer' ):
            self.ACCOUNT_TYPE = ['receivable']
        elif (data['form']['print_type'] == 'supplier'):
            self.ACCOUNT_TYPE = ['payable']
        else:
            self.ACCOUNT_TYPE = ['payable','receivable']
        return True
    
    def generate_records(self, cr, uid, ids, data, context):
        result = []
        self.set_context(cr, data, ids, context=context)
        result = self._get_lines(data['form'])
        result = sorted(result, key=operator.itemgetter('partner_name'))
        return result
    
jasper_report.report_jasper('report.partner.ageing.summary.jasper', 'partner.ageing.report.wizard', parser=aging_report)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

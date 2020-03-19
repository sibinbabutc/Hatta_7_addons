from openerp.osv import fields, osv

class IrActionsReportXml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    report_type = fields.selection(selection_add=[("docx", "docx")])

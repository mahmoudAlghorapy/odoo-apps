# -*- coding: utf-8 -*-

import base64
from datetime import datetime, time
import xlsxwriter
import io
from werkzeug.urls import url_encode

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class performaHistory(models.TransientModel):
    _name = "daily.journal.wizard"
    _description = "Daily Journal Invoice"

    date_from = fields.Date(string="Date From",  required=True)
    date_to = fields.Date(string="Date To", default=fields.Date.context_today)

    journal_id = fields.Many2one('account.journal', 'Journal', required=True, ondelete='cascade')



    report_name = fields.Char(string="Excel Report Name", required=False, )
    report = fields.Binary(string="Excel Report")

    def action_view_report(self):

        self.ensure_one()
        if not self.journal_id:
            raise ValidationError(_("Please select a Journal."))
        report_action = self.env['ir.actions.report'].search(
            [('report_name', '=', 'daily_customer_invoices.performa_history_report_template')])
        print('report_action',report_action)
        data = {
            "active_model": self._name,
            "active_ids": self.ids,
        }

        return self.env.ref('daily_customer_invoices.action_report_performa_history_html').report_action(None, data=data)
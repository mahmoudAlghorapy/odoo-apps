# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, time


class ReportChequeAccounting(models.AbstractModel):
    _name = 'report.daily_customer_invoices.performa_history_report_template'
    _description = 'Report Performa History'

    @api.model
    def _get_report_values(self, docids, data=None):
        filter_record = self.env[data.get('active_model')].browse(
            data.get('active_ids'))

        date_from = filter_record.date_from
        date_to = filter_record.date_to if filter_record.date_to else fields.Date.today()
        journal_id = filter_record.journal_id

        # Get invoice records
        invoice_records = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('move_type', 'in', ['out_invoice']),
            ('state', '=', 'posted'),
            ('journal_id', '=', journal_id.id)
        ])

        # Get credit note records
        credit_records = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('move_type', 'in', ['out_refund']),
            ('state', '=', 'posted'),
            ('journal_id', '=', journal_id.id)
        ])

        # Calculate totals
        total_invoiced_amount = sum(invoice_records.mapped('amount_total_signed'))
        total_invoiced_residual = sum(invoice_records.mapped('amount_residual'))

        total_credit_amount = sum(credit_records.mapped('amount_total_signed'))
        total_credit_residual = sum(credit_records.mapped('amount_residual'))

        net_amount = total_invoiced_amount - total_credit_amount
        payment_collection = net_amount - (total_invoiced_residual + total_credit_residual)

        report_data = {
            'invoices': [],
            'credits': [],
            'totals': {
                'total_invoiced_amount': round(total_invoiced_amount, 2),
                'total_invoiced_residual': round(total_invoiced_residual, 2),
                'total_credit_amount': round(total_credit_amount, 2),
                'total_credit_residual': round(total_credit_residual, 2),
                'net_amount': round(net_amount, 2),
                'payment_collection': round(payment_collection, 2),
            }
        }

        # Add invoice lines
        for move in invoice_records:
            report_data['invoices'].append({
                'partner_id': move.partner_id.name or 'N/A',
                'invoice_number': move.name,
                'total_amount': round(move.amount_total_signed, 2),
                'amount_residual': round(move.amount_residual, 2),
            })

        # Add credit note lines
        for move in credit_records:
            report_data['credits'].append({
                'partner_id': move.partner_id.name or 'N/A',
                'invoice_number': move.name,
                'total_amount': round(move.amount_total_signed, 2),
                'amount_residual': round(move.amount_residual, 2),
            })

        return {
            'doc_ids': docids,
            'doc_model': data.get('active_model'),
            'docs': filter_record,
            'values': report_data,
            'data': data,
        }
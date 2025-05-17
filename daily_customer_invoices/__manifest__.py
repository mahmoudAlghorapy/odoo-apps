# -*- coding: utf-8 -*-
{
    'name': 'Daily Customer Invoices',
    'version': '18.0.1.0',
    'category': 'Accounting',
    'summary': """
        Daily Sales Reporting with Payment Tracking
        =========================================
        Generate detailed daily reports for customer invoices and credit notes
        with payment collection analysis and financial summaries.
    """,
    'description': """
        Daily Customer Invoices Report
        -----------------------------

        This module enhances Odoo's accounting capabilities by providing:

        * Daily sales invoice tracking with amount due
        * Credit note reconciliation
        * NET amount calculation (Invoices - Credit Notes)
        * Payment collection analysis
        * Journal-specific filtering
        * Printable PDF reports with timestamps

        Features:
        ---------
        - Filter by date range and journal
        - View customer-wise transactions
        - Track total invoiced vs pending amounts
        - Professional report layout with company branding
        - Audit trail with printed-by user tracking

        Ideal for accountants and sales managers needing daily financial visibility.
    """,
    'author': 'Mahmoud Fathi',
    'website': 'https://www.example.com',
    'license': 'OPL-1',
    'price': 60,
    'currency': 'USD',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/performa_report.xml',
        'wizard/performa_history.xml',
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
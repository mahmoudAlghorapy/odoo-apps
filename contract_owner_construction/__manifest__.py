{
    'name': 'Construction Management',
    'version': '16.0',
    'category': 'base',
    'author': ' Mahmoud Fathi',
    'price': 200,
    'summary': """
    Client Extract and Contractor Extract

    """,
'description': """
Construction Contract Management
===============================

This module provides a complete solution for managing construction contracts, subcontractor invoices, and owner invoices with advanced progress tracking.

Key Features:
-------------
- Manage construction contracts with start/end dates and project details
- Track subcontractor invoices with sequence numbers
- Generate owner invoices with progress percentages
- Automatic calculation of work quantities and amounts
- Supervision invoice generation
- Deduction management system
- Insurance percentage calculations
- Comprehensive reporting on contract progress
- Integration with Odoo Accounting and Sales modules

The module is ideal for construction companies, contractors, and project managers who need to efficiently track and manage their construction contracts and related financial transactions.
""",
    'depends': ['account', 'sale','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/construct.xml',
        'views/analytic_account.xml',
        'report/contract.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'images': ['static/description/banner.gif'],

}

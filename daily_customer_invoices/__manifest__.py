# -*- coding: utf-8 -*-
{
    'name': 'Daily Customer Invoices',
    'version': '18.0',
    'category': 'base',
    'author': 'Mahmoud Fathi',
    'price': '60',
    'summary': """
    Accounting Enhancements 
    """,
    'depends': [
        'base', 'account',
    ],
    'data': [

        'security/ir.model.access.csv',
        'report/performa_report.xml',
        'wizard/performa_history.xml',
        # 'data/server_action.xml',

    ],

    'installable': True,
    'auto_install': False,
    'application': False,

}

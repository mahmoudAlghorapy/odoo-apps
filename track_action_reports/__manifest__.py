# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Track Action Reports',
    'version': '17.1',

    'depends': ['base', 'hr','purchase','sale', 'account'],
    'author': 'Mahmoud Fathy ',
    'summary': "This module track the main print in odoo sale account purchase stock ",
    'description': """
This module track the main print in odoo sale account purchase stock.
========================================
    """,
    'category': 'Accounting',

    'data': [
        # 'security/ir.model.access.csv',
        # 'security/calendar_security.xml',
        # 'views/employee.xml',

    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

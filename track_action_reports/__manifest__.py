# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Track Action Reports',
    'version': '18.1',
    'depends': ['base', 'hr','purchase','sale', 'account'],
    'author': 'Mahmoud Fathy ',
    'price': '40',
    'currency': 'USD',
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
    'images': [
        'static/description/banner.gif',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

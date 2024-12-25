# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Track Action Reports',
    'version': '18.1',
    'depends': ['base', 'hr','purchase','sale', 'account'],
    'author': 'Mahmoud Fathy mahmah273@gmail.com ',
    'price': '40',


    'currency': 'USD',
    'website': 'https://www.linkedin.com/in/mahmoud-mohamed-096638110/',

    'summary': "This module track the main prints of odoo sale, account, purchase, stock ",
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
        'static/description/purchase.png',
        # 'security/calendar_security.xml',
        # 'views/employee.xml',

    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

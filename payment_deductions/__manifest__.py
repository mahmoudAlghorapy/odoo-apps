{
    "name": "Account Payment Deduction",
    "version": "18.0",
    "author": "Mahmoud Fathi mahmah273@gmail.com",

    "category": "account",
    'price': '40',
'summary': "This module add many deduction in payment journal entry  ",
    'description': """
This module add many deduction in payment journal entry  when we press action confirm   after we make accounts configration in setting.


    """,
    "depends": [
        "account", "account_accountant",
    ],
    "data": [
        # 'security/ir.model.access.csv',
        # 'security/groups.xml',

        'views/account_setting.xml',
        'views/account_payment.xml',
        # 'data/cron.xml',

    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

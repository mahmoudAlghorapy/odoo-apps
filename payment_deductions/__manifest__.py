{
    "name": "Account Payment Deduction",
    "version": "17.0",
    "author": "Mahmoud Fathi mahmah273@gmail.com",

    "license": "LGPL-3",
    "category": "account",
    'price': '50',
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
    'installable': True,
    'images': ['static/description/banner.gif'],
}

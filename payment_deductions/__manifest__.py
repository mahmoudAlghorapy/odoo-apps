{
    "name": "Account Payment Deduction",
    "version": "18.0",
    "author": "Mahmoud Fathi mahmah273@gmail.com",

    "license": "AGPL-3",
    "category": "account",
    'price': '40',
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
}

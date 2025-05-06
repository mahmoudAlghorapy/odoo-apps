{
    'name': 'Construction Management',
    'version': '16.0',
    'category': 'base',
    'author': ' Mahmoud Fathi',
    'price': 100,
    'summary': """
    Client Extract and Contractor Extract

    """,
    'depends': ['account', 'sale','sale_management','order_line_sequences','bi_sale_purchase_discount_with_tax'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/construct.xml',
        'views/analytic_account.xml',
        'report/contract.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False
}

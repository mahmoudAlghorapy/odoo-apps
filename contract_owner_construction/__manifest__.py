{
    'name': 'Construction Management',
    'version': '16.0',
    'category': 'base',
    'author': ' Mahmoud Fathi',
    'price': 200.00,
    'currency': 'USD',
    'license': 'LGPL-3',  # Required license key
    'summary': 'Comprehensive Construction Contract and Invoice Management System',
    'description': """
        <div class="oe_row">
            <h2>Construction Contract Management</h2>
            <p>Streamline construction projects with advanced contract, invoice, and progress tracking.</p>
            
            <h3>Key Features:</h3>
            <ul class="oe_spaced">
                <li>🏗️ Manage subcontractor and owner invoices</li>
                <li>📅 Track project timelines (date ranges)</li>
                <li>📊 Automatic progress percentage calculations</li>
                <li>💰 Supervision invoice generation</li>
                <li>🧾 Deduction management system</li>
                <li>🛡️ Insurance withholding calculations</li>
                <li>🔢 Sequential invoice numbering</li>
                <li>📈 Integrated with Odoo Sales & Accounting</li>
            </ul>
            
            <div class="oe_demo oe_screenshot">
                <img src="screenshot1.png" alt="Construction Module Screenshot">
            </div>
            
            <h3>Support</h3>
            <p>Contact <a href="mailto:support@example.com">support@example.com</a> for assistance.</p>
        </div>
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

from odoo import models, fields, api


class AccountMoveDeductionLine(models.Model):
    _name = 'account.move.deduction.line'
    _description = 'Deduction Line'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        ondelete='cascade'
    )

    name = fields.Char(
        string='Item Name'  # Translated from "اسم البند"
    )

    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        compute='_compute_account_id',
        store=True,
        readonly=False,
        precompute=True,
        index=True,
        auto_join=True,
        ondelete="cascade",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id), ('is_off_balance', '=', False)]",
        check_company=True,
        tracking=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        default=lambda self: self.env.company
    )

    discount_percent = fields.Float(
        string='Discount Percentage'  # Translated from "نسبة الخصم"
    )

    discount_amount = fields.Monetary(
        string='Amount',
        # compute='_compute_discount_values',
        # inverse='_inverse_discount_amount',
        store=True
    )

    currency_id = fields.Many2one(
        related='move_id.currency_id',
        store=True,
        readonly=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Item Name',
        domain="[('type', '=', 'service')]"
    )

    @api.onchange('discount_percent', 'move_id.amount_total_works')
    def _compute_discount_values(self):
        for line in self:
            if line.move_id.amount_total_works:
                # Only compute if percentage was changed (amount will be handled by inverse)
                line.discount_amount = (line.discount_percent / 100.0) * line.move_id.amount_total_works
            else:
                line.discount_amount = 0.0

    @api.onchange('discount_amount', 'move_id.amount_total_works')
    def _inverse_discount_amount(self):
        for line in self:
            print('line.move_id.amount_total_works',line.move_id.amount_total_works)
            if line.move_id.amount_total_works and line.discount_amount:
                # When amount is manually set, calculate the percentage
                line.discount_percent = (line.discount_amount / line.move_id.amount_total_works) * 100.0

    @api.depends('product_id', 'move_id')
    def _compute_account_id(self):
        for line in self:
            if not line.move_id:
                line.account_id = False
                continue

            account = False

            # If product is set, get account from product
            if line.product_id:
                fiscal_position = line.move_id.fiscal_position_id
                accounts = line.with_company(line.move_id.company_id).product_id \
                    .product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)

                if line.move_id.is_sale_document(include_receipts=True):
                    account = accounts['income']
                elif line.move_id.is_purchase_document(include_receipts=True):
                    account = accounts['expense']

            # If no product or no account found from product, try partner-specific account
            if not account and line.move_id.partner_id:
                account = self.env['account.account']._get_most_frequent_account_for_partner(
                    company_id=line.move_id.company_id.id,
                    partner_id=line.move_id.partner_id.id,
                    move_type=line.move_id.move_type,
                )

            # If still no account, fall back to journal's default account
            if not account:
                account = line.move_id.journal_id.default_account_id

            # Apply fiscal position mapping if needed
            if account and line.move_id.fiscal_position_id:
                account = line.move_id.fiscal_position_id.map_account(account)

            line.account_id = account
# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    const_type = fields.Selection(
        [('normal', 'normal'), ('to_owner', 'To Owner'), ('to_sub_contractor', 'To Sub Contractor')],
        default="normal"
    )
    sale_order_id = fields.Many2one('sale.order', 'Order')
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    project_name = fields.Char(string='Project Name')

    sub_inv_sequence = fields.Integer(string='Sub Invoice Sequence in Contract', compute='_compute_sub_inv_sequence',
                                      store=True)

    owner_inv_sequence = fields.Integer(string='Owner Invoice Sequence in Contract',
                                        compute='_compute_owner_inv_sequence', store=True)

    amount_total_works = fields.Float(string="Total Amount", required=False, compute='compute_amount_total_works')

    insurance_works = fields.Float(string="Withheld Work Insurance", required=False,
                                   compute='compute_amount_total_works')

    insurance_percentage = fields.Float(string="Insurance Percentage", required=False, default=0.0)
    is_supervision = fields.Boolean(string="",default=False  )
    is_converted = fields.Boolean(string="",default=False  )

    deduction_line_ids = fields.One2many(
        'account.move.deduction.line',
        'move_id',
        string='Deduction Items',
        copy=False
    )

    total_deductions = fields.Monetary(
        string='Total Deductions',
        compute='_compute_total_deductions',
        store=True,
        currency_field='currency_id'
    )
    supervision_invoice_id = fields.Many2one(
        comodel_name="account.move",
        copy=False
    )
    total_supervision_amount = fields.Monetary(compute="_compute_total_supervision_amount", store=True,
                                               string="Total Supervision")

    # @api.depends(
    #     'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
    #     'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
    #     'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
    #     'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
    #     'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
    #     'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
    #     'line_ids.balance',
    #     'line_ids.currency_id',
    #     'line_ids.amount_currency',
    #     'line_ids.amount_residual',
    #     'line_ids.amount_residual_currency',
    #     'line_ids.payment_id.state',
    #     'line_ids.full_reconcile_id', 'discount_method', 'discount_amount', 'discount_amount_line')
    # def _compute_amount(self):
    #     for move in self:
    #         total_untaxed, total_untaxed_currency = 0.0, 0.0
    #         total_tax, total_tax_currency = 0.0, 0.0
    #         total_residual, total_residual_currency = 0.0, 0.0
    #         total, total_currency = 0.0, 0.0
    #
    #         for line in move.line_ids:
    #             if move.is_invoice(True):
    #                 # === Invoices ===
    #                 if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
    #                     # Tax amount.
    #                     total_tax += line.balance
    #                     total_tax_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.display_type in ('product', 'rounding'):
    #                     # Untaxed amount.
    #                     total_untaxed += line.balance
    #                     total_untaxed_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.display_type == 'payment_term':
    #                     # Residual amount.
    #                     total_residual += line.amount_residual
    #                     total_residual_currency += line.amount_residual_currency
    #             else:
    #                 # === Miscellaneous journal entry ===
    #                 if line.debit:
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #
    #         sign = move.direction_sign
    #         amount_total_with_supervision = sign * total_currency + move.total_supervision_amount
    #         print('amount_total_with_supervision',amount_total_with_supervision)
    #
    #         move.amount_untaxed = sign * total_untaxed_currency
    #         move.amount_tax = sign * total_tax_currency
    #         move.amount_total = amount_total_with_supervision
    #         print('move.amount_total',move.amount_total)
    #         move.amount_residual = -sign * total_residual_currency
    #         print(' move.amount_residual', move.amount_residual)
    #
    #         move.amount_untaxed_signed = -total_untaxed
    #         move.amount_tax_signed = -total_tax
    #         move.amount_total_signed = abs(
    #             amount_total_with_supervision) if move.move_type == 'entry' else -amount_total_with_supervision
    #         move.amount_residual_signed = total_residual
    #         move.amount_total_in_currency_signed = abs(
    #             amount_total_with_supervision) if move.move_type == 'entry' else -(sign * amount_total_with_supervision)
    #         res = move._calculate_discount()
    #         move.discount_amt = res
    #         move.discount_amt_line = res

    @api.depends('invoice_line_ids','invoice_line_ids.supervision_amount')
    def _compute_total_supervision_amount(self):
        for rec in self:
            if rec.is_supervision:
                rec.total_supervision_amount = sum(rec.invoice_line_ids.mapped('supervision_amount'))
            else:
                rec.total_supervision_amount = 0.0


    def action_convert_to_supervision_invoice(self):
        inv_vals = {
            'partner_id': self.partner_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'project_name': self.project_name,
            'invoice_date': self.invoice_date,
            'sale_order_id': self.sale_order_id.id,
            'journal_id': self.journal_id.id,
            'const_type': 'to_owner',
            'move_type': 'out_invoice',
            'state': 'draft',
            'is_supervision': True,
        }
        invoice_id = self.create(inv_vals)

        inv_lines = []
        for line in self.invoice_line_ids:
            # Try to match with corresponding sale.order.line by product_id
            matching_so_line = self.sale_order_id.order_line.filtered(
                lambda l: l.product_id.id == line.product_id.id
            )[:1]  # Get the first match if multiple

            contract_qty = matching_so_line.product_uom_qty if matching_so_line else 0.0
            contract_amount = matching_so_line.price_subtotal if matching_so_line else 0.0

            inv_lines.append(
                (0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'account_id': line.account_id.id if line.account_id else False,
                    'account_analytic_id': line.account_analytic_id.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'contract_qty': contract_qty,
                    'contract_amount': contract_amount,

                })
            )

        invoice_id.write({
            'invoice_line_ids': inv_lines
        })
        self.supervision_invoice_id = invoice_id.id
        print('self.supervision_invoice_id ',self.supervision_invoice_id )
        self.is_converted = True
    def action_view_supervision_invoice(self):

        action_vals = {}
        if self.supervision_invoice_id:
            action_vals = {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.supervision_invoice_id.id,
                'views': [ (self.env.ref('construction.invoice_construction_view_form').id, 'form')],
            }
        return action_vals

    @api.onchange('date_from')
    def onchange_date_from(self):
        for rec in self:
            if rec.date_from:
                rec.invoice_date = rec.date_from

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)

        for move in moves:
            if move.move_type in ('out_invoice', 'out_refund', 'out_receipt') and move.state == 'draft':
                lines_to_add = []

                for deduction in move.deduction_line_ids:
                    if deduction.account_id and deduction.discount_amount:
                        line_vals = {
                            'account_id': deduction.account_id.id,
                            'name': deduction.product_id.name or 'Deduction',
                            'quantity': 1,
                            'price_unit': -deduction.discount_amount,
                            'exclude_from_invoice_tab': True,
                            'display_type': 'product',
                            'product_id': deduction.product_id.id if deduction.product_id else False,
                        }
                        lines_to_add.append((0, 0, line_vals))

                if lines_to_add:
                    move.with_context(check_move_validity=False).write({
                        'invoice_line_ids': lines_to_add
                    })

        return moves

    @api.depends('deduction_line_ids.discount_amount')
    def _compute_total_deductions(self):
        for move in self:
            move.total_deductions = sum(line.discount_amount for line in move.deduction_line_ids)

    @api.depends('invoice_line_ids', 'invoice_line_ids.total_price', 'insurance_percentage')
    def compute_amount_total_works(self):
        for order in self:
            # print('insurance_percentage',order.insurance_percentage)
            order.amount_total_works = sum(order.invoice_line_ids.mapped('total_price'))
            order.insurance_works = order.insurance_percentage * order.amount_total_works

    @api.depends('sale_order_id', 'sale_order_id.const_invoice_ids')
    def _compute_sub_inv_sequence(self):
        for move in self:
            if move.sale_order_id:
                related_moves = move.sale_order_id.const_invoice_ids.filtered(
                    lambda m: m.move_type in ['in_invoice']).sorted('create_date')
                move.sub_inv_sequence = related_moves.ids.index(move.id) + 1 if move.id in related_moves.ids else 0
            else:
                move.sub_inv_sequence = 0

    @api.depends('sale_order_id', 'sale_order_id.const_invoice_ids')
    def _compute_owner_inv_sequence(self):
        for move in self:
            if move.sale_order_id:
                related_moves = move.sale_order_id.const_invoice_ids.filtered(
                    lambda m: m.move_type in ['out_invoice']).sorted('create_date')
                move.owner_inv_sequence = related_moves.ids.index(move.id) + 1 if move.id in related_moves.ids else 0
            else:
                move.owner_inv_sequence = 0

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(AccountMove, self).default_get(fields_list)
    #     if not self.env.context.get('create_sub_inv'):
    #         res.pop('sale_order_id', None)
    #         res.pop('const_type', None)
    #         res.pop('move_type', None)
    #         res.pop('date_from', None)
    #         res.pop('date_to', None)
    #         res.pop('project_name', None)
    #         res.pop('journal_id', None)
    #     return res

    @api.onchange('sale_order_id')
    def change_order(self):
        if self.sale_order_id:
            order_lines = []
            company = self.company_id

            for line in self.sale_order_id.order_line:
                if line.product_id:
                    taxes = line.product_id.taxes_id.filtered(
                        lambda r: not company or r.company_id == company
                    )
                    if self.fiscal_position_id and taxes:
                        tax_ids = self.fiscal_position_id.map_tax(taxes)._origin.ids
                    else:
                        tax_ids = taxes._origin.ids

                    last_price = 0.0
                    last_qty = 0.0
                    # if self.const_type == 'to_owner':
                    last_price = line.price_unit
                    print('last_price', last_price)

                    # Get the account manually
                    account = line.product_id.property_account_income_id or \
                              line.product_id.categ_id.property_account_income_categ_id

                    if self.fiscal_position_id and account:
                        account = self.fiscal_position_id.map_account(account)

                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_id': line.product_uom.id,
                        'last_qty': last_qty,
                        'last_price': last_price,
                        'contract_qty': line.product_uom_qty,
                        'contract_amount': line.price_subtotal,
                        'price_unit': last_price,
                        'company_id': line.company_id.id,
                        'tax_ids': [(6, 0, tax_ids)],
                        'account_id': account.id if account else False,
                    }))

            self.invoice_line_ids = order_lines


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    last_qty = fields.Float('Last Quantity', compute="_compute_qty_price")
    total_qty = fields.Float('Total Quantity', compute="_compute_total_qty")
    last_price = fields.Float('Last Price', compute="_compute_qty_price")
    current_price = fields.Float('Current Price', compute="_compute_total_price")
    total_price = fields.Float('Total Price', compute="_compute_total_price")
    product_percent = fields.Float("Percent %", compute="_compute_percent", inverse="_inverse_percent", store=True)
    contract_qty = fields.Float(
        string="Contract Quantity",
        required=False
    )

    contract_amount = fields.Float(
        string="Contract Amount",
        required=False
    )

    last_product_percent = fields.Float('Last Percent %', compute="_compute_qty_price")
    total_product_percent = fields.Float('Tota Percent %', compute="_compute_total_product_percent", store=True)
    category = fields.Char('Category')
    sequence_number = fields.Integer(string='#', compute='_compute_sequence_number', help='Line Numbers')
    account_analytic_id = fields.Many2one('account.analytic.account', )
    supervision_amount = fields.Monetary(compute="_compute_supervision_amount")

    @api.depends('account_analytic_id')
    def _compute_supervision_amount(self):
        for line in self:
            supervision_amount = 0.0
            print('line.move_id.move_type',line.move_id.move_type)
            if line.move_id.move_type == "out_invoice":
                supervision_amount = (
                        ((line.account_analytic_id.supervision_percent / 100) * line.price_unit) * line.quantity)
            line.supervision_amount = supervision_amount

    @api.depends('product_percent', 'last_product_percent')
    def _compute_total_product_percent(self):
        for il in self:
            il.total_product_percent = il.product_percent + il.last_product_percent

    @api.depends('move_id.invoice_line_ids')
    def _compute_sequence_number(self):
        """Compute the sequence numbers based on the order of lines in the move."""
        for move in self.mapped('move_id'):
            # Get all lines in the move, sorted by `sequence` (avoid sorting by `id` for NewIds)
            lines = move.invoice_line_ids.sorted(key=lambda l: l.sequence)

            sequence_number = 1
            seq_map = {}

            for line in lines:
                if line.display_type in 'product':
                    seq_map[line.id] = sequence_number
                    # No increment for display lines
                else:
                    seq_map[line.id] = sequence_number
                    sequence_number += 1

            # Apply the sequence numbers to lines in self that belong to this move
            for line in self.filtered(lambda l: l.move_id == move):
                line.sequence_number = seq_map[line.id] = sequence_number
                sequence_number += 1

    @api.depends('product_id', 'move_id.sale_order_id', 'move_id.partner_id', 'move_id.invoice_date', 'quantity',
                 'product_percent')
    def _compute_qty_price(self):
        for il in self:
            last_qty = 0.0
            last_price = 0.0
            last_product_percent = 0.0
            qty = 0.0
            if il.product_id and il.move_id.sale_order_id and il.move_id.partner_id and il.move_id.invoice_date:
                for inv in il.move_id.sale_order_id.const_invoice_ids:
                    if inv.const_type == il.move_id.const_type:
                        if inv.invoice_date and il.move_id.invoice_date and inv.partner_id == il.move_id.partner_id and inv.invoice_date < il.move_id.invoice_date:
                            for invl in inv.invoice_line_ids:
                                if invl.product_id == il.product_id:
                                    last_qty += invl.quantity
                                    last_price += invl.quantity * invl.price_unit
                                    last_product_percent += invl.product_percent
                    # elif il.move_id.const_type == "to_owner":
                    #     if inv.invoice_date and il.move_id.invoice_date and inv.invoice_date < il.move_id.invoice_date:
                    #         for invl in inv.invoice_line_ids:
                    #             if invl.product_id == il.product_id:
                    #                 qty += invl.quantity
                    #     il.quantity = qty
            il.last_qty = last_qty
            il.last_price = last_price
            il.last_product_percent = last_product_percent

    @api.depends('last_qty', 'quantity')
    def _compute_total_qty(self):
        for il in self:
            il.total_qty = il.last_qty + il.quantity

    @api.depends('price_unit', 'quantity', 'last_price')
    def _compute_total_price(self):
        for il in self:
            il.current_price = il.price_unit * il.quantity
            il.total_price = il.current_price + il.last_price

    @api.depends('total_qty', 'product_id', 'move_id')
    def _compute_percent(self):
        for il in self:
            il.product_percent = 0.0  # Default value

            if not il.move_id or not il.move_id.sale_order_id:
                continue

            # Find matching order line
            matching_lines = il.move_id.sale_order_id.order_line.filtered(
                lambda l: l.product_id == il.product_id and l.product_uom_qty > 0
            )

            if matching_lines:
                line = matching_lines[0]
                try:
                    # Get all previous invoice quantities for this product
                    all_invoice_lines = il.move_id.sale_order_id.invoice_ids.mapped('invoice_line_ids').filtered(
                        lambda l: l.product_id == il.product_id
                    )
                    total_invoiced_qty = sum(all_invoice_lines.mapped('quantity')) + il.quantity
                    # print('total_invoiced_qty',total_invoiced_qty)

                    il.product_percent = round((total_invoiced_qty / line.product_uom_qty) * 100, 2)
                except ZeroDivisionError:
                    il.product_percent = 0.0

    @api.constrains('total_product_percent')
    def _check_percent_not_exceed_100(self):
        for il in self:
            if il.total_product_percent > 100:
                raise ValidationError(_(
                    "The total percent for product %s cannot exceed 100%%."
                ) % il.product_id.display_name)

    @api.onchange('product_percent')
    def _inverse_percent(self):
        for il in self:
            if not il.move_id or not il.move_id.sale_order_id:
                continue

            matching_lines = il.move_id.sale_order_id.order_line.filtered(
                lambda l: l.product_id == il.product_id and l.product_uom_qty > 0
            )

            if matching_lines:
                line = matching_lines[0]
                try:
                    # Calculate what the total invoiced quantity should be based on percentage
                    target_total_qty = (il.product_percent / 100) * line.product_uom_qty

                    # Get all previous invoice quantities excluding current line
                    all_invoice_lines = il.move_id.sale_order_id.invoice_ids.mapped('invoice_line_ids').filtered(
                        lambda l: l.product_id == il.product_id and l.id != il.id
                    )
                    previous_qty = sum(all_invoice_lines.mapped('quantity'))

                    # Calculate how much we need to invoice in this line
                    il.quantity = target_total_qty - previous_qty
                except ZeroDivisionError:
                    il.quantity = 0.0


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sub_count = fields.Integer('Sub Count', compute="_compute_inv_count")
    owner_count = fields.Integer('Owner Count', compute="_compute_inv_count")
    const_invoice_ids = fields.One2many("account.move", 'sale_order_id', string='Sub invoices')
    const_type = fields.Selection([('normal', 'normal'), ('const', 'Const')], default="normal")
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    project_name = fields.Char(string='اسم المشروع')
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], default="fix",
                                       string='Discount Method')

    @api.depends('const_invoice_ids')
    def _compute_inv_count(self):
        for ord in self:
            ord.sub_count = len(ord.const_invoice_ids.filtered(lambda x: x.const_type == 'to_sub_contractor'))
            ord.owner_count = len(ord.const_invoice_ids.filtered(lambda x: x.const_type == 'to_owner'))

    def action_view_sub_inv(self):
        self.ensure_one()
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        action = {
            'name': _('Sub Contractor Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('contract_owner_construction.invoice_construction_view_tree').id, 'tree'),
                (self.env.ref('contract_owner_construction.invoice_construction_view_form').id, 'form')
            ],
            'domain': [('sale_order_id', '=', self.id), ('const_type', '=', 'to_sub_contractor')],
            'context': dict(self._context, default_sale_order_id=self.id,
                            default_partner_id=self.partner_id.id,
                            default_const_type='to_sub_contractor',
                            default_move_type='in_invoice',
                            default_date_from=self.date_from,
                            default_date_to=self.date_to,
                            default_project_name=self.project_name,
                            default_journal_id=journal.id if journal else False,
                            create_sub_inv=True),
        }
        return action

    @api.onchange('date_from')
    def onchange_date_from(self):
        for rec in self:
            if rec.date_from:
                rec.date_order = rec.date_from

    def action_view_owner_inv(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return {
            'name': _('Owner Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('contract_owner_construction.invoice_construction_view_tree').id, 'tree'),
                (self.env.ref('contract_owner_construction.invoice_construction_view_form').id, 'form')
            ],
            'context': dict(self._context, default_sale_order_id=self.id,
                            default_partner_id=self.partner_id.id,
                            default_const_type='to_owner',
                            default_move_type='out_invoice',
                            default_date_from=self.date_from,
                            default_date_to=self.date_to,
                            default_project_name=self.project_name,
                            default_journal_id=journal.id if journal else False,
                            create_sub_inv=True),

            'domain': [('partner_id', '=', self.partner_id.id), ('sale_order_id', '=', self.id),
                       ('const_type', '=', 'to_owner')],
        }

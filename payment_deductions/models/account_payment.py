# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError, UserError
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    is_html_empty,
    sql
)
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    discount_amount = fields.Monetary(currency_field='currency_id')
    stamp_amount = fields.Monetary(currency_field='currency_id')
    admin_fees = fields.Monetary(currency_field='currency_id')
    withholding_in_amount = fields.Monetary(currency_field='currency_id', string='Withholding(IN)')
    withholding_out_amount = fields.Monetary(currency_field='currency_id', string='Withholding(OUT -1)')
    withholding_out_amount_3 = fields.Monetary(currency_field='currency_id', string='Withholding(OUT -3)')
    advertising_amount = fields.Monetary(string='Advertising', currency_field='currency_id')

    def action_post(self):
        res = super(AccountPaymentInherit, self).action_post()
        line_updates = []
        if self.payment_type == 'inbound':
            partner_move_lines = self.move_id.line_ids.filtered(lambda line: line.debit > 0)
            debit_round = round(sum(partner_move_lines.mapped('debit')), 2)

            if partner_move_lines:
                if self.company_id.discount_account and self.discount_amount > 0:
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.discount_account.id,
                        'name': 'Discount',
                        'currency_id': self.company_currency_id.id,
                        'credit': 0.0,
                        'debit': self.discount_amount,
                    }))
                if self.company_id.advertising_account and self.advertising_amount > 0:
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.advertising_account.id,
                        'name': 'Advertising',
                        'currency_id': self.company_currency_id.id,
                        'credit': 0.0,
                        'debit': self.advertising_amount,
                    }))
                if self.company_id.stamp_account and self.stamp_amount > 0:
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.stamp_account.id,
                        'name': 'Stamp',
                        'currency_id': self.company_currency_id.id,
                        'credit': 0.0,
                        'debit': self.stamp_amount,
                    }))
                if self.company_id.withholding_in_account and self.withholding_in_amount > 0:
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.withholding_in_account.id,
                        'name': 'Withholding(IN)',
                        'currency_id': self.company_currency_id.id,
                        'credit': 0.0,
                        'debit': self.withholding_in_amount,
                    }))
                if self.company_id.admin_fees and self.admin_fees > 0:
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.admin_fees.id,
                        'name': 'Withholding(IN)',
                        'currency_id': self.company_currency_id.id,
                        'credit': 0.0,
                        'debit': self.admin_fees,
                    }))

                for line in partner_move_lines:
                    new_debit = debit_round
                    for update in line_updates:
                        new_debit -= update[2]['debit']
                    line_updates.append((1, line.id, {'debit': new_debit}))
                # Apply accumulated changes to self.move_id.line_ids
                self.move_id.line_ids = line_updates
        if self.payment_type == 'outbound':
            partner_move_lines = self.move_id.line_ids.filtered(lambda line: line.credit > 0)
            credit_round = round(sum(partner_move_lines.mapped('credit')), 2)
            if partner_move_lines:
                if self.company_id.withholding_out_account and self.withholding_out_amount > 0:
                    # Create a new line for withholding
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.withholding_out_account.id,
                        'name': 'Withholding(OUT)',
                        'currency_id': self.company_currency_id.id,
                        'credit': self.withholding_out_amount,
                        'debit': 0.0,
                    }))
                    # credit_round -= self.withholding_out_amount
                if self.company_id.withholding_out_account_3 and self.withholding_out_amount_3 > 0:
                    # Create a new line for withholding
                    line_updates.append((0, 0, {
                        'account_id': self.company_id.withholding_out_account_3.id,
                        'name': 'Withholding(OUT-3)',
                        'currency_id': self.company_currency_id.id,
                        'credit': self.withholding_out_amount_3,
                        'debit': 0.0,
                    }))
                    for line in partner_move_lines:
                        new_credit = credit_round
                        for update in line_updates:
                            new_credit -= update[2]['credit']
                        line_updates.append((1, line.id, {'credit': new_credit}))
                        # Apply accumulated changes to self.move_id.line_ids
                    self.move_id.line_ids = line_updates
                    # credit_round -= self.withholding_out_amount_3
            #     for line in partner_move_lines:
            #         line_updates.append((1, line.id, {'credit': line.credit - self.withholding_out_amount_3}))
            # self.move_id.write({'line_ids': line_updates})
        return res

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # if len(liquidity_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one outstanding payments/receipts account.",
                #         move.display_name,
                #     ))

                # if len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one receivable/payable account (with an exception of "
                #         "internal transfers).",
                #         move.display_name,
                #     ))

                # if writeoff_lines and len(writeoff_lines.account_id) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, "
                #         "all optional journal items must share the same account.",
                #         move.display_name,
                #     ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                # if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "share the same partner.",
                #         move.display_name,
                #     ))

                if counterpart_lines.account_id.account_type == 'asset_receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            print('payment_vals_to_write', payment_vals_to_write)
            print('move_vals_to_write', move_vals_to_write)
            _logger.warn('Skip payment_vals_to_writethreshold ' + str(payment_vals_to_write))
            _logger.warn('Skip move_vals_to_write the threshold ' + str(move_vals_to_write))
            _logger.info('payment_vals_to_write %s', payment_vals_to_write)
            _logger.info('move_vals_to_write %s', move_vals_to_write)
            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))


# def create_check_button(self):
#     if self.amount > 0:
#         for pay in self.with_context(skip_account_move_synchronization=True):
#             liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
#             if liquidity_lines and counterpart_lines and writeoff_lines:
#                 counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
#                 writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))
#
#                 if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
#                     sign = -1
#                 else:
#                     sign = 1
#                 writeoff_amount = abs(writeoff_amount) * sign
#
#                 write_off_line_vals = {
#                     'name': writeoff_lines[0].name,
#                     'amount': writeoff_amount,
#                     'account_id': writeoff_lines[0].account_id.id,
#                 }
#             else:
#                 write_off_line_vals = {}
#
#             line_vals_list = pay._prepare_move_line_default_vals_new(write_off_line_vals=write_off_line_vals)
#
#             line_ids_commands = [
#                 Command.update(liquidity_lines.id, line_vals_list[0]) if liquidity_lines else Command.create(
#                     line_vals_list[0]),
#                 Command.update(counterpart_lines.id, line_vals_list[1]) if counterpart_lines else Command.create(
#                     line_vals_list[1])
#             ]
#
#             for line in writeoff_lines:
#                 line_ids_commands.append((2, line.id))
#
#             for extra_line_vals in line_vals_list[2:]:
#                 line_ids_commands.append((0, 0, extra_line_vals))
#
#             # Update the existing journal items.
#             # If dealing with multiple write-off lines, they are dropped and a new one is generated.
#
#             pay.move_id.write({
#                 'partner_id': pay.partner_id.id,
#                 'currency_id': pay.currency_id.id,
#                 'partner_bank_id': pay.partner_bank_id.id,
#                 # 'line_ids': line_ids_commands,
#             })
#     else:
#         raise ValidationError(_("Please define an Amount."))


def _prepare_check_values(self, values):
    print('values', values)

    max_debit_value = 0.0
    max_credit_value = 0.0

    if self.payment_type == 'outbound' and self.payment_method_code == 'issue_check':
        for line in values:
            current_credit = line.get('credit', 0)
            if current_credit > max_credit_value:
                max_credit_value = current_credit
                max_credit_line = line

        if max_credit_line:
            print('max_credit_line', max_credit_line)
            self.do_checks_operations(max_credit_line)

    if self.payment_type == 'inbound' and self.payment_method_code == 'received_third_check':
        for line in values:
            current_debit = line.get('debit', 0)
            if current_debit > max_debit_value:
                max_debit_value = current_debit
                max_debit_line = line

        if max_debit_line:
            print('max_credit_line', max_debit_line)
            self.do_checks_operations(max_debit_line)

    return values

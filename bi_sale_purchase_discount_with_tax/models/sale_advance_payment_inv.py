from odoo import api, fields, models, _


class SaleAdvancePaymentInvInherit(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoice(self, order, so_line, amount):
        invoice = super(SaleAdvancePaymentInvInherit, self)._create_invoice(order, so_line, amount)
        # Ensure tax calculation uses discounted amount
        # invoice._recompute_dynamic_lines()
        invoice._compute_tax_totals()
        return invoice

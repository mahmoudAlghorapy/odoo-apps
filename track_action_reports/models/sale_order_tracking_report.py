from odoo import api, models


class ReportSaleOrder(models.AbstractModel):
    _name = 'report.sale.report_saleorder'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        sale_orders = self.env['sale.order'].browse(docids)

        if self._validate_sale_orders(sale_orders):
            # Add a message to the sale order indicating the report print
            for order in sale_orders:
                order.message_post(
                    body=f"Report printed by {user.name}",
                    subject="Report Printed"
                )
            return {
                'doc_ids': docids,
                'doc_model': 'sale.order',
                'docs': sale_orders,
                'data': data,
                'user': user,
            }
        else:
            return {}

    def _validate_sale_orders(self, sale_orders):
        for order in sale_orders:
            if not order.partner_id:
                return False
        return True


class ReportAccountMove(models.AbstractModel):
    _name = 'report.account.report_invoice_with_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['account.move'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': account_moves,
            'data': data,
            'user': user,
        }
class ReportAccountMoveWithOutPayment(models.AbstractModel):
    _name = 'report.account.report_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['account.move'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': account_moves,
            'data': data,
            'user': user,
        }

class ReportAccountPayment(models.AbstractModel):
    _name = 'report.account.report_payment_receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['account.payment'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': account_moves,
            'data': data,
            'user': user,
        }
class ReportAccountPaymentDocument(models.AbstractModel):
    _name = 'report.account.report_payment_receipt_document'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['account.payment'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': account_moves,
            'data': data,
            'user': user,
        }
class ReportStockPicking(models.AbstractModel):
    _name = 'report.stock.report_picking'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['stock.picking'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': account_moves,
            'data': data,
            'user': user,
        }


class ReportProductTemplate(models.AbstractModel):
    _name = 'report.mrp_account_enterprise.product_template_cost_structure'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['product.product'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'docs': account_moves,
            'data': data,
            'user': user,
        }


class ReportPurchaseOrder(models.AbstractModel):
    _name = 'report.purchase.report_purchaseorder'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user

        account_moves = self.env['purchase.order'].browse(docids)
        print('account_moves',account_moves)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name} purchase name {move.name}",
                subject="Report Printed"
            )
        print('data',data)
        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs': account_moves,
            'data': data,
            'user': user,
        }


class ReportRFQ(models.AbstractModel):
    _name = 'report.purchase.report_purchasequotation'

    @api.model
    def _get_report_values(self, docids, data=None):
        user = self.env.user
        account_moves = self.env['purchase.order'].browse(docids)

        # if self._validate_account_moves(account_moves):
        # Add a message to the account move indicating the report print
        for move in account_moves:
            move.message_post(
                body=f"Report printed by {user.name}",
                subject="Report Printed"
            )
        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs': account_moves,
            'data': data,
            'user': user,
        }

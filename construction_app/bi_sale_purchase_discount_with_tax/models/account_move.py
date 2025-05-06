# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang


class account_move(models.Model):
	_inherit = 'account.move'

	invoice_line_ids = fields.One2many(  # /!\ invoice_line_ids is just a subset of line_ids.
		'account.move.line',
		'move_id',
		string='Invoice lines',
		copy=False,
		readonly=True,
		domain=[('display_type', 'in', ('product', 'line_section', 'line_note')),('exclude_from_invoice_tab', '=', False)],
		states={'draft': [('readonly', False)]},
	)
	is_line = fields.Boolean('Is a line')
	total_amount_before_discount_amt = fields.Monetary(compute='_compute_total_amount_before_discount_amt',
													   string='Amount Before Discount', store=True, readonly=True)
	total_quantity = fields.Float(string="Total Quantity", required=False, compute="compute_total_quantity")
	total_partner_invoiced = fields.Monetary(
		string="Total Partner Invoiced",
		compute='_compute_total_partner_invoiced',
		currency_field='company_currency_id',
		store=False
	)
	is_insta = fields.Boolean(string="Is INSTA", default=lambda self: self.env.company.is_insta)

	@api.depends('partner_id', 'invoice_date', 'state')
	def _compute_total_partner_invoiced(self):
		for move in self:
			if not move.partner_id:
				move.total_partner_invoiced = 0.0
				continue

			date_to = move.invoice_date or fields.Date.context_today(move)

			# Search without internal_type condition
			domain = [
				('partner_id', '=', move.partner_id.id),
				('date', '<=', date_to),
				('parent_state', '=', 'posted'),
			]

			lines = self.env['account.move.line'].search(domain)

			# Now filter lines by internal_type in Python
			filtered_lines = lines.filtered(
				lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')

			)

			move.total_partner_invoiced = sum(filtered_lines.mapped('balance'))

	@api.depends('invoice_line_ids.quantity')
	def compute_total_quantity(self):
		for rec in self:
			rec.total_quantity = sum(rec.invoice_line_ids.mapped('quantity'))


	@api.depends('discount_amt')
	def _compute_total_amount_before_discount_amt(self):
		for rec in self:
			rec.total_amount_before_discount_amt = sum(rec.invoice_line_ids.mapped('price_subtotal'))



	@api.depends('discount_amount','discount_method','discount_type','config_inv_tax')
	def _calculate_discount(self):
		res_config= self.env.company
		cur_obj = self.env['res.currency']
		res=0.0
		discount = 0.0
		for move in self:
			applied_discount = line_discount = sums = move_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
			if self._context.get('default_move_type') in ['out_invoice', 'out_receipt', 'out_refund']:
				if res_config.tax_discount_policy:
					if res_config.tax_discount_policy == 'tax':
						if move.discount_method == 'fix':
							discount = move.discount_amount
							res = discount
						elif move.discount_method == 'per':
							total = 0.0
							tax = 0.0
							for line in self.invoice_line_ids:
								if line.exclude_from_invoice_tab == False:
									tax += line.com_tax()
									total += line.price_unit
								res = (total ) * (move.discount_amount/ 100)
						else:
							res = discount


						for line in move.invoice_line_ids:
							amount_untaxed += line.price_subtotal
							applied_discount += line.discount_amt

							if line.discount_method == 'fix':
								line_discount += line.discount_amount
								res = line_discount
							elif line.discount_method == 'per':
								tax = line.com_tax()
								line_discount += (line.price_subtotal )  * (line.discount_amount/ 100)
								res = line_discount

					else:

						for line in move.invoice_line_ids:
							amount_untaxed += line.price_subtotal
							applied_discount += line.discount_amt
							res = applied_discount

							if line.discount_method == 'fix':
								line_discount += line.discount_amount
								res = line_discount
							elif line.discount_method == 'per':
								# tax = line.com_tax()
								line_discount += line.price_subtotal * (line.discount_amount/ 100)
								res = line_discount

						if move.discount_type == 'global':
							if move.discount_method == 'fix':
								move_discount = move.discount_amount
								res = move_discount
								if move.invoice_line_ids:
									for line in move.invoice_line_ids:
										if line.tax_ids:
											final_discount = 0.0
											try:
												final_discount = ((move.discount_amount*line.price_subtotal)/amount_untaxed)
											except ZeroDivisionError:
												pass
											discount = line.price_subtotal
											taxes = line.tax_ids.compute_all(discount, \
																move.currency_id,1.0, product=line.product_id, \
																partner=move.partner_id)
											sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
								move.update({
									'config_inv_tax': sums,
								})
							else:
								move.discount_amt_line = 0.00
								move_discount = amount_untaxed * (move.discount_amount / 100)

								res = move_discount
								if move.invoice_line_ids:
									for line in move.invoice_line_ids:
										if line.tax_ids:
											final_discount = 0.0
											try:
												final_discount = ((move.discount_amount*line.price_subtotal)/100.0)
											except ZeroDivisionError:
												pass
											discount = line.price_subtotal
											taxes = line.tax_ids.compute_all(discount, \
																move.currency_id,1.0, product=line.product_id, \
																partner=move.partner_id)
											sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

								move.update({
									'config_inv_tax': sums,
								})
						else:

							if move.invoice_line_ids:
								for line in self.invoice_line_ids:
									if line.tax_ids:
										final_discount = 0.0
										try:
											test = move.invoice_line_ids.mapped('discount_method')
											if test == 'fix':
												final_discount = ((move.invoice_line_ids.discount_amount*line.price_subtotal)/amount_untaxed)
										except ZeroDivisionError:
											pass
										discount = line.price_subtotal

										taxes = line.tax_ids.compute_all(discount, \
															move.currency_id,1.0, product=line.product_id, \
															partner=move.partner_id)
										sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
			else:

				if res_config.tax_discount_policy == 'tax':
					if move.discount_method == 'fix':
						discount = move.discount_amount
						res = discount
					elif move.discount_method == 'per':
						total = 0.0
						tax = 0.0
						for line in self.invoice_line_ids:
							if line.exclude_from_invoice_tab == False:
								tax += line.com_tax()
								total += line.price_unit

							res = (total + tax) * (move.discount_amount/ 100)

					else:
						res = discount


					for line in move.invoice_line_ids:
						amount_untaxed += line.price_subtotal
						applied_discount += line.discount_amt

						if line.discount_method == 'fix':
							line_discount += line.discount_amount
							res = line_discount
						elif line.discount_method == 'per':
							# tax = line.com_tax()
							line_discount += line.price_subtotal  * (line.discount_amount/ 100)
							res = line_discount

				else:

					for line in move.invoice_line_ids:
						amount_untaxed += line.price_subtotal
						applied_discount += line.discount_amt
						res = applied_discount

						if line.discount_method == 'fix':
							line_discount += line.discount_amount
							res = line_discount
						elif line.discount_method == 'per':
							tax = line.com_tax()
							line_discount += (line.price_subtotal ) * (line.discount_amount/ 100)
							res = line_discount

					if move.discount_type == 'global':
						if move.discount_method == 'fix':
							move_discount = move.discount_amount
							res = move_discount
							if move.invoice_line_ids:
								for line in move.invoice_line_ids:
									if line.tax_ids:
										final_discount = 0.0
										try:
											final_discount = ((move.discount_amount*line.price_subtotal)/amount_untaxed)
										except ZeroDivisionError:
											pass
										discount = line.price_subtotal
										taxes = line.tax_ids.compute_all(discount, \
															move.currency_id,1.0, product=line.product_id, \
															partner=move.partner_id)
										sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
							move.update({
								'config_inv_tax': sums,
							})
						else:
							move.discount_amt_line = 0.00
							move_discount = amount_untaxed * (move.discount_amount / 100)

							res = move_discount
							if move.invoice_line_ids:
								for line in move.invoice_line_ids:
									if line.tax_ids:
										final_discount = 0.0
										try:
											final_discount = ((move.discount_amount*line.price_subtotal)/100.0)
										except ZeroDivisionError:
											pass
										discount = line.price_subtotal
										taxes = line.tax_ids.compute_all(discount, \
															move.currency_id,1.0, product=line.product_id, \
															partner=move.partner_id)
										sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

							move.update({
								'config_inv_tax': sums,
							})
					else:

						if move.invoice_line_ids:
							for line in self.invoice_line_ids:
								if line.tax_ids:
									final_discount = 0.0
									try:
										test = move.invoice_line_ids.mapped('discount_method')
										if test == 'fix':
											final_discount = ((move.invoice_line_ids.discount_amount*line.price_subtotal)/amount_untaxed)
									except ZeroDivisionError:
										pass
									discount = line.price_subtotal

									taxes = line.tax_ids.compute_all(discount, \
														move.currency_id,1.0, product=line.product_id, \
														partner=move.partner_id)
									sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

		return res



	@api.depends(
		'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
		'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
		'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
		'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
		'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
		'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
		'line_ids.balance',
		'line_ids.currency_id',
		'line_ids.amount_currency',
		'line_ids.amount_residual',
		'line_ids.amount_residual_currency',
		'line_ids.payment_id.state',
		'line_ids.full_reconcile_id','discount_method','discount_amount','discount_amount_line')
	def _compute_amount(self):
		for move in self:
			total_untaxed, total_untaxed_currency = 0.0, 0.0
			total_tax, total_tax_currency = 0.0, 0.0
			total_residual, total_residual_currency = 0.0, 0.0
			total, total_currency = 0.0, 0.0

			for line in move.line_ids:
				if move.is_invoice(True):
					# === Invoices ===
					if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
						# Tax amount.
						total_tax += line.balance
						total_tax_currency += line.amount_currency
						total += line.balance
						total_currency += line.amount_currency
					elif line.display_type in ('product', 'rounding'):
						# Untaxed amount.
						total_untaxed += line.balance
						total_untaxed_currency += line.amount_currency
						total += line.balance
						total_currency += line.amount_currency
					elif line.display_type == 'payment_term':
						# Residual amount.
						total_residual += line.amount_residual
						total_residual_currency += line.amount_residual_currency
				else:
					# === Miscellaneous journal entry ===
					if line.debit:
						total += line.balance
						total_currency += line.amount_currency

			sign = move.direction_sign
			move.amount_untaxed = sign * total_untaxed_currency
			print('move.amount_untaxed',move.amount_untaxed)
			move.amount_tax = sign * total_tax_currency
			move.amount_total = sign * total_currency
			move.amount_residual = -sign * total_residual_currency
			print('total_untaxed',total_untaxed)
			move.amount_untaxed_signed = -total_untaxed
			move.amount_tax_signed = -total_tax
			move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
			move.amount_residual_signed = total_residual
			move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total)
			res = move._calculate_discount()
			move.discount_amt = res
			move.discount_amt_line = res


	def _compute_amount_account(self):
		for record in self:
			for line in record.invoice_line_ids:
				if line.product_id:
					record.discount_account_id = line.account_id.id


	@api.depends('discount_type')
	def _calculate_count_total(self):
		res_config= self.env.company
		final_count_total = 00
		for move in self :
			if self._context.get('default_move_type') in ['out_invoice', 'out_receipt', 'out_refund']:
				if move.discount_type == 'global':
					res = self._calculate_discount()
					if  move.config_inv_tax:
						move.update({
						   'count_total' : move.amount_untaxed + move.config_inv_tax,
						   'untax_test_amount' :  move.amount_untaxed,
						   'final_count_total' : move.amount_untaxed + move.config_inv_tax
						})
					else:
						test_amount =(move.amount_untaxed)
						move.update({
						   'count_total' : test_amount+ move.amount_tax,
						   'untax_test_amount' :  test_amount,
						   'final_count_total' : test_amount+ move.amount_tax,
						})

				else:
					res = self._calculate_discount()
					if  move.config_inv_tax:
						move.update({
						   'count_total' : move.amount_untaxed + move.config_inv_tax
						})
					else:
						test_amount =(move.amount_untaxed - res)
						move.update({
						   'count_total' : test_amount+ move.amount_tax,
						   'final_count_total': test_amount+ move.amount_tax,
						   'untax_test_amount' :  test_amount
						})
			else:
				res = self._calculate_discount()
				if move.discount_type == 'global':
					if  move.config_inv_tax:
						move.update({
						   'count_total' : move.amount_untaxed + move.config_inv_tax,
						   'untax_test_amount' :  move.amount_untaxed
						})
					else:
						# test_amount =(move.amount_untaxed - res)
						move.update({
						   'count_total' : move.amount_untaxed + move.amount_tax,
						   'untax_test_amount' :  move.amount_untaxed
						})
				else:
					if  move.config_inv_tax:
						move.update({
						   'count_total' : move.amount_untaxed + move.config_inv_tax
						})
					else:
						test_amount =(move.amount_untaxed - res)
						move.update({
						   'count_total' : test_amount+ move.amount_tax,
						   'untax_test_amount' :  test_amount
						})


	discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')],'Discount Method')
	discount_amount = fields.Float('Discount Amount')
	discount_amt = fields.Monetary(string='Discount', readonly=True, compute='_compute_amount')
	amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, tracking=True,
		compute='_compute_amount')
	amount_tax = fields.Monetary(string='Tax', store=True, readonly=True,
		compute='_compute_amount')
	amount_total = fields.Monetary(string='Total', store=True, readonly=True,
		compute='_compute_amount',
		inverse='_inverse_amount_total')
	discount_type = fields.Selection([('line', 'Move Line'), ('global', 'Global')], 'Discount Applies to',default='global')
	discount_account_id = fields.Many2one('account.account', 'Discount Account',compute='_compute_amount_account',store=True)
	discount_amt_line = fields.Monetary(compute='_compute_amount', string='Line Discount', digits='Discount', store=True, readonly=True)
	discount_amount_line = fields.Monetary(string="Discount Line")
	config_inv_tax = fields.Monetary(string="total disc tax",compute="_calculate_discount",store=True)
	count_total = fields.Monetary(string="tax total",compute="_calculate_count_total",readonly=True)
	untax_test_amount = fields.Monetary(string="total untax amount for line",compute="_calculate_discount",store=True)
	final_count_total = fields.Monetary(string="total amount",compute="_calculate_discount",store=True)

	@api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_unit', 'amount_total', 'amount_untaxed',
				 'discount_type', 'discount_amount', 'discount_amount_line')
	def _compute_tax_totals(self):
		res_config = self.env.company
		for move in self:
			if not move.is_invoice(include_receipts=True):
				continue

			base_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
			base_line_values_list = []
			discount_amount = move._calculate_discount()

			# Apply the same discount policy logic as in sale orders
			if res_config.tax_discount_policy == 'tax' and move.discount_type == 'global' and move.discount_method == 'per':
				# Special case for tax-inclusive discounts
				total_amount = sum(base_lines.mapped('price_subtotal'))
				total_tax = sum(line.price_total - line.price_subtotal for line in base_lines)
				full_amount = total_amount + total_tax
				discount_value = full_amount * (move.discount_amount / 100)

				new_total_amount = total_amount - (
							discount_value * (total_amount / full_amount)) if full_amount else total_amount
				new_total_tax = total_tax - (discount_value * (total_tax / full_amount)) if full_amount else total_tax

				for line in base_lines:
					line_ratio = line.price_subtotal / total_amount if total_amount else 0
					discounted_subtotal = new_total_amount * line_ratio

					base_dict = line._convert_to_tax_base_line_dict()
					base_dict['price_unit'] = discounted_subtotal / line.quantity if line.quantity else 0
					base_dict['price_subtotal'] = discounted_subtotal
					base_line_values_list.append(base_dict)
			else:
				# Regular discount application
				discount_share = discount_amount / sum(base_lines.mapped('price_subtotal')) if base_lines and sum(
					base_lines.mapped('price_subtotal')) else 0

				for line in base_lines:
					base_dict = line._convert_to_tax_base_line_dict()

					if move.is_insta:
						total_qty = line.total_metres * line.quantity
						base_dict['quantity'] = total_qty
						base_dict['price_subtotal'] = total_qty * line.price_unit

						if discount_amount > 0:
							line_discount = base_dict['price_subtotal'] * discount_share
							base_dict['price_unit'] -= line_discount / total_qty if total_qty else 0
							base_dict['price_subtotal'] -= line_discount
					else:
						if discount_amount > 0:
							line_discount = line.price_subtotal * discount_share
							base_dict['price_unit'] -= line_discount / line.quantity if line.quantity else 0
							base_dict['price_subtotal'] -= line_discount

					base_line_values_list.append(base_dict)

			# Compute taxes with the adjusted amounts
			tax_totals = self.env['account.tax']._prepare_tax_totals(
				base_line_values_list,
				move.currency_id,
			)

			move.tax_totals = tax_totals

	@api.model_create_multi
	def create(self, vals_list):
		result = super(account_move,self).create(vals_list)
		if self._context.get('default_move_type') in ('out_invoice','out_refund','out_receipt'):
			for res in result:
				if res.discount_method and res.discount_amount:
					if res.state in 'draft':
						account = False
						for line in res.invoice_line_ids:
							if line.product_id:
								account = line.account_id.id

						l = res.line_ids.filtered(lambda s: s.name == "Discount")

						if len(l or []) == 0 and account:
							discount_vals = {
								'account_id': account,
								'quantity': 1,
								'price_unit': -res.discount_amt,
								'name': "Discount",
								'tax_ids' :None,
								'exclude_from_invoice_tab': True,
								'display_type':'product',


							}
							res.with_context(check_move_validity=False).write({
									'invoice_line_ids' : [(0,0,discount_vals)]
								})
				else:
					if res.state in 'draft':
						account = False
						for line in res.invoice_line_ids:
							if line.product_id:
								account = line.account_id.id

						l = res.line_ids.filtered(lambda s: s.name == "Discount")

						if len(l or []) == 0 and account:
							discount_vals = {
								'account_id': account,
								'quantity': 1,
								'price_unit': -res.discount_amount_line,
								'name': "Discount",
								'tax_ids' :None,
								'exclude_from_invoice_tab': True,
								'display_type':'product',
								'discount_amount': - res.discount_amount_line


							}
							res.with_context(check_move_validity=False).write({
									'invoice_line_ids' : [(0,0,discount_vals)]
								})
		else:
			for res in result:
				if res.invoice_line_ids:
					if res.invoice_line_ids[0].product_id:
						if "Down payment" in res.invoice_line_ids[0].product_id.name:
							res.write({'discount_method':'',
								'discount_amount':0})

				if res.discount_method and res.discount_amount:
					if res.state in 'draft':
						account = False
						for line in res.invoice_line_ids:
							if line.product_id:
								account = line.account_id.id

						l = res.line_ids.filtered(lambda s: s.name == "Discount")

						if len(l or []) == 0 and account:
							discount_vals = {
								'account_id': account,
								'quantity': 1,
								'price_unit': -res.discount_amt,
								'name': "Discount",
								'tax_ids' :None,
								'exclude_from_invoice_tab': True,
								'display_type':'product',


							}
							res.with_context(check_move_validity=False).write({
									'invoice_line_ids' : [(0,0,discount_vals)]
								})
				else:
					if res.state in 'draft':
						account = False
						for line in res.invoice_line_ids:
							if line.product_id:
								account = line.account_id.id

						l = res.line_ids.filtered(lambda s: s.name == "Discount")

						if len(l or []) == 0 and account:
							discount_vals = {
								'account_id': account,
								'quantity': 1,
								'price_unit': -res.discount_amount_line,
								'name': "Discount",
								'tax_ids' :None,
								'exclude_from_invoice_tab': True,
								'display_type':'product',
								'discount_amount': - res.discount_amount_line


							}
							res.with_context(check_move_validity=False).write({
									'invoice_line_ids' : [(0,0,discount_vals)]
								})

		return result




class account_move_line(models.Model):
	_inherit = 'account.move.line'

	discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
	discount_type = fields.Selection(related='move_id.discount_type', string="Discount Applies to")
	discount_amount = fields.Float('Discount Amount')
	discount_amt = fields.Float('Discount Final Amount')
	flag = fields.Boolean("Flag")
	is_global_disc = fields.Boolean(string = "Global Discount")
	exclude_from_invoice_tab = fields.Boolean(help="Technical field used to exclude some lines from the invoice_line_ids tab in the form view.")
	width = fields.Float(string="Width")
	length = fields.Float(string="Length")
	total_metres = fields.Float(string="NUM Metres", required=False,compute='compute_total_metres' )
	is_insta = fields.Boolean(string="Is INSTA", related='move_id.is_insta')

	# quantity = fields.Float(string='Quantity', store=True, digits=dp.get_precision('Product Unit of Measure'),
	# 						required=True, default=1)

	@api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'total_metres', 'is_insta')
	def _compute_totals(self):
		for line in self:
			if line.display_type != 'product':
				line.price_total = line.price_subtotal = False
				continue

			# Compute 'price_subtotal'.
			if line.is_insta:
				# Special calculation for INSTA
				subtotal = line.total_metres * line.quantity * line.price_unit
			else:
				# Default calculation
				line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
				subtotal = line.quantity * line_discount_price_unit

			# Compute 'price_total'.
			if line.tax_ids:
				# For tax calculation, we still use the discounted price unit if not INSTA
				if line.is_insta:
					price_for_tax = line.price_unit
				else:
					price_for_tax = line_discount_price_unit

				taxes_res = line.tax_ids.compute_all(
					price_for_tax,
					quantity=line.quantity if not line.is_insta else line.total_metres * line.quantity,
					currency=line.currency_id,
					product=line.product_id,
					partner=line.partner_id,
					is_refund=line.is_refund,
				)
				line.price_subtotal = taxes_res['total_excluded']
				line.price_total = taxes_res['total_included']
			else:
				line.price_total = line.price_subtotal = subtotal
	@api.depends('length', 'width')
	def compute_total_metres(self):
		for rec in self:
			rec.total_metres =   rec.width * rec.length

	@api.depends('quantity','price','tax_ids','discount_amount')
	def com_tax(self):
		tax_total = 0.0
		tax = 0.0
		for line in self:
			for tax in line.tax_ids:
				tax_total += (tax.amount/100)*line.price_subtotal
			tax = tax_total
			return tax





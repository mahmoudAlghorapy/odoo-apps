# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    supervision_percent = fields.Float()

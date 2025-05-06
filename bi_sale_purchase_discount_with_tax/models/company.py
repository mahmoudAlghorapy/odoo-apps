from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.company'

    is_insta = fields.Boolean(string="Is INSTA",  )
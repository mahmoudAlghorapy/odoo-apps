from odoo import models, api, fields


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    test = fields.Char(string="Test", required=False, )
    res_users = fields.Many2one('res.users', 'Users', ondelete='cascade')

from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    appointment_id = fields.Many2one(
        "hospital.appointment",
        string="Appointment"
    )
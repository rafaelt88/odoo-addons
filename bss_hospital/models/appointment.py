from odoo import models, fields, api


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _inherit = ['mail.thread']
    _rec_name = 'patient_id'
    _rec_names_search = ['reference', 'patient_id']

    reference = fields.Char(string='Reference', default='New')
    patient_id = fields.Many2one('hospital.patient', string='Patient', ondelete='restrict', required=True)
    date = fields.Date(string='Appointment Date')
    note = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    appointment_line_ids = fields.One2many('hospital.appointment.line', 'appointment_id', string='Appointment Lines')
    total_quantity = fields.Float(
        string='Total Quantity', 
        compute='_compute_total_quantity',
        store=True
    )
    date_of_birth = fields.Date(
        string='Date of Birth', 
        related='patient_id.date_of_birth',
        groups="bss_hospital.group_hospital_doctors"
    )

    @api.model_create_multi
    def create(self, val_list):
        for vals in val_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.appointment')
        return super().create(val_list)

    @api.depends('appointment_line_ids.quantity')
    def _compute_total_quantity(self):
        for record in self:
            total = sum(line.quantity for line in record.appointment_line_ids)
            record.total_quantity = total

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.reference}] {record.patient_id.name}"

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
    
    def action_ongoing(self):
        for record in self:
            record.state = 'ongoing'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'


class HospitalAppointLine(models.Model):
    _name = 'hospital.appointment.line'
    _description = 'Hospital Appointment Line'

    appointment_id = fields.Many2one('hospital.appointment', string='Appointment')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)

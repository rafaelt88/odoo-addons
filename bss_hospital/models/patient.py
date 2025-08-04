from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Hospital Patient'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    date_of_birth = fields.Date(string='Date of Birth', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', tracking=True)
    tag_ids = fields.Many2many(
        'patient.tag', 
        'patient_tag_rel', 
        'patient_id',
        'tag_id',
        string='Tags', tracking=True)
    is_minor = fields.Boolean(string='Minor')
    guardian = fields.Char(string='Guardian')
    weight = fields.Float(string='Weight (kg)')


    # def unlink(self):
    #     for record in self:
    #         domain = [('patient_id', '=', record.id)]
    #         appointments = self.env['hospital.appointment'].search(domain)
    #         if appointments:
    #             raise ValidationError(_("Cannot delete patient '%s' with already existing associated appointments." % record.name))
    #     return super().unlink()
    
    @api.ondelete(at_uninstall=False)
    def _check_patient_appointments(self):
        for record in self:
            domain = [('patient_id', '=', record.id)]
            appointments = self.env['hospital.appointment'].search(domain)
            if appointments:
                raise ValidationError(_("You cannot delete patient '%s' because they have existing appointments." % record.name))
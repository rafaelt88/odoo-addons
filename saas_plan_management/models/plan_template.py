# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class PlanTemplate(models.Model):
    _name = 'saas.plan.template'
    _description = 'SaaS Plan Template'
    _order = 'sequence, name'

    name = fields.Char(
        string='Template Name',
        required=True,
        help='Tên template gói dịch vụ'
    )
    
    code = fields.Char(
        string='Template Code',
        required=True,
        help='Mã template duy nhất'
    )
    
    description = fields.Text(
        string='Description',
        help='Mô tả về template'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    category = fields.Selection([
        ('business', 'Business'),
        ('technical', 'Technical'),
        ('mixed', 'Mixed')
    ], string='Category', default='mixed', required=True)
    
    plan_type = fields.Selection([
        ('free', 'Free'),
        ('trial', 'Trial'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom')
    ], string='Plan Type', required=True, default='basic')
    
    # Template configuration as JSON
    template_config = fields.Text(
        string='Template Configuration',
        help='JSON configuration cho template',
        default='{}'
    )
    
    # Default values cho plan
    default_monthly_price = fields.Float(
        string='Default Monthly Price',
        default=0.0
    )
    
    default_yearly_price = fields.Float(
        string='Default Yearly Price',
        default=0.0
    )
    
    default_max_users = fields.Integer(
        string='Default Max Users',
        default=1
    )
    
    default_storage_gb = fields.Float(
        string='Default Storage (GB)',
        default=1.0
    )
    
    default_api_calls = fields.Integer(
        string='Default API Calls',
        default=1000
    )
    
    # Module template
    default_module_ids = fields.Many2many(
        'saas.odoo.module',
        'plan_template_module_rel',
        'template_id',
        'module_id',
        string='Default Modules',
        help='Các module mặc định cho template này'
    )
    
    # Plans created from this template
    plan_ids = fields.One2many(
        'saas.plan',
        'template_id',  # Sẽ thêm field này vào saas.plan
        string='Created Plans',
        help='Các plan đã tạo từ template này'
    )
    
    # Computed fields
    plan_count = fields.Integer(
        string='Plan Count',
        compute='_compute_plan_count',
        store=True
    )
    
    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 
         'Template code must be unique!')
    ]
    
    @api.depends('plan_ids')
    def _compute_plan_count(self):
        for template in self:
            template.plan_count = len(template.plan_ids)
    
    @api.constrains('template_config')
    def _check_template_config(self):
        for template in self:
            if template.template_config:
                try:
                    json.loads(template.template_config)
                except ValueError:
                    raise ValidationError("Template configuration must be valid JSON!")
    
    def name_get(self):
        """Custom name display"""
        result = []
        for template in self:
            name = template.name
            if template.plan_type:
                name += f" ({template.plan_type.title()})"
            result.append((template.id, name))
        return result
    
    def create_plan_from_template(self):
        """Tạo plan mới từ template"""
        self.ensure_one()
        
        # Parse template configuration
        config = {}
        if self.template_config:
            try:
                config = json.loads(self.template_config)
            except ValueError:
                config = {}
        
        # Create plan values
        plan_vals = {
            'name': f"{self.name} Plan",
            'code': f"{self.code}_PLAN",
            'description': self.description,
            'plan_type': self.plan_type,
            'monthly_price': self.default_monthly_price,
            'yearly_price': self.default_yearly_price,
            'max_users': self.default_max_users,
            'storage_limit_gb': self.default_storage_gb,
            'api_calls_limit_daily': self.default_api_calls,
            'included_module_ids': [(6, 0, self.default_module_ids.ids)],
            'template_id': self.id,
        }
        
        # Apply configuration overrides
        if config:
            for key, value in config.items():
                if hasattr(self.env['saas.plan'], key):
                    plan_vals[key] = value
        
        # Ensure unique code
        base_code = plan_vals['code']
        counter = 1
        while self.env['saas.plan'].search([('code', '=', plan_vals['code'])]):
            plan_vals['code'] = f"{base_code}_{counter}"
            counter += 1
        
        # Create the plan
        plan = self.env['saas.plan'].create(plan_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Created Plan'),
            'res_model': 'saas.plan',
            'res_id': plan.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_plans(self):
        """View plans created from this template"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plans from Template'),
            'res_model': 'saas.plan',
            'view_mode': 'tree,form',
            'domain': [('template_id', '=', self.id)]
        }
    
    def duplicate_template(self):
        """Duplicate template"""
        new_code = f"{self.code}_COPY"
        counter = 1
        while self.search([('code', '=', new_code)]):
            new_code = f"{self.code}_COPY_{counter}"
            counter += 1
        
        return self.copy({
            'name': f"{self.name} (Copy)",
            'code': new_code,
            'active': False
        })
    
    def get_template_config(self):
        """Get parsed template configuration"""
        if self.template_config:
            try:
                return json.loads(self.template_config)
            except ValueError:
                return {}
        return {}

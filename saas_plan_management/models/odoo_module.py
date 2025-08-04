# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaasOdooModule(models.Model):
    _name = 'saas.odoo.module'
    _description = 'Odoo Module for SaaS Plans'
    _order = 'category, name'

    name = fields.Char(
        string='Module Name',
        required=True,
        help='Tên module Odoo'
    )
    
    technical_name = fields.Char(
        string='Technical Name',
        required=True,
        help='Tên kỹ thuật của module (VD: sale, purchase, stock)'
    )
    
    description = fields.Text(
        string='Description',
        help='Mô tả chức năng của module'
    )
    
    category = fields.Selection([
        ('accounting', 'Accounting & Finance'),
        ('sales', 'Sales'),
        ('purchase', 'Purchase'),
        ('inventory', 'Inventory & MRP'),
        ('hr', 'Human Resources'),
        ('marketing', 'Marketing'),
        ('project', 'Project Management'),
        ('website', 'Website & E-commerce'),
        ('productivity', 'Productivity'),
        ('administration', 'Administration'),
        ('localization', 'Localization'),
        ('industry', 'Industry Specific'),
        ('integration', 'Integration'),
        ('other', 'Other')
    ], string='Category', required=True, default='other')
    
    version = fields.Char(
        string='Version',
        default='17.0',
        help='Phiên bản Odoo tương thích'
    )
    
    license = fields.Selection([
        ('LGPL-3', 'LGPL-3'),
        ('OPL-1', 'Odoo Proprietary License'),
        ('GPL-3', 'GPL-3'),
        ('MIT', 'MIT'),
        ('Other', 'Other')
    ], string='License', default='LGPL-3')
    
    is_core_module = fields.Boolean(
        string='Core Module',
        default=False,
        help='Module cốt lõi của Odoo'
    )
    
    is_popular = fields.Boolean(
        string='Popular Module',
        default=False,
        help='Module phổ biến được sử dụng nhiều'
    )
    
    is_required = fields.Boolean(
        string='Required',
        default=False,
        help='Module bắt buộc phải có'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Thông tin bổ sung
    author = fields.Char(
        string='Author',
        help='Tác giả của module'
    )
    
    website = fields.Char(
        string='Website',
        help='Website của module'
    )
    
    depends = fields.Text(
        string='Dependencies',
        help='Các module phụ thuộc (cách nhau bởi dấu phẩy)'
    )
    
    # Quan hệ với plans
    plan_ids = fields.Many2many(
        'saas.plan',
        'saas_plan_module_rel',
        'module_id',
        'plan_id',
        string='Used in Plans',
        help='Các gói dịch vụ sử dụng module này'
    )
    
    # Computed fields
    plan_count = fields.Integer(
        string='Plan Count',
        compute='_compute_plan_count',
        store=True
    )
    
    @api.depends('plan_ids')
    def _compute_plan_count(self):
        for module in self:
            module.plan_count = len(module.plan_ids)
    
    _sql_constraints = [
        ('unique_technical_name', 'UNIQUE(technical_name)', 
         'Technical name must be unique!')
    ]
    
    def name_get(self):
        """Custom name display"""
        result = []
        for module in self:
            name = module.name
            if module.technical_name:
                name += f" ({module.technical_name})"
            if module.is_core_module:
                name += " [Core]"
            if module.is_popular:
                name += " ⭐"
            result.append((module.id, name))
        return result
    
    def action_view_plans(self):
        """Action to view plans using this module"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Plans Using This Module',
            'res_model': 'saas.plan',
            'view_mode': 'tree,form',
            'domain': [('included_module_ids', 'in', self.id)]
        }
    
    @api.model
    def create_default_modules(self):
        """Create default Odoo modules"""
        default_modules = [
            # Core modules
            {'name': 'Base', 'technical_name': 'base', 'category': 'administration', 'is_core_module': True, 'is_required': True},
            {'name': 'Web', 'technical_name': 'web', 'category': 'administration', 'is_core_module': True, 'is_required': True},
            {'name': 'Mail', 'technical_name': 'mail', 'category': 'productivity', 'is_core_module': True, 'is_popular': True},
            
            # Sales & CRM
            {'name': 'CRM', 'technical_name': 'crm', 'category': 'sales', 'is_popular': True},
            {'name': 'Sales Management', 'technical_name': 'sale', 'category': 'sales', 'is_popular': True},
            {'name': 'Sales Teams', 'technical_name': 'sales_team', 'category': 'sales'},
            
            # Accounting
            {'name': 'Invoicing', 'technical_name': 'account', 'category': 'accounting', 'is_popular': True},
            {'name': 'Accounting Reports', 'technical_name': 'account_reports', 'category': 'accounting'},
            
            # Purchase
            {'name': 'Purchase Management', 'technical_name': 'purchase', 'category': 'purchase', 'is_popular': True},
            
            # Inventory
            {'name': 'Inventory Management', 'technical_name': 'stock', 'category': 'inventory', 'is_popular': True},
            {'name': 'Manufacturing', 'technical_name': 'mrp', 'category': 'inventory'},
            
            # HR
            {'name': 'Employees', 'technical_name': 'hr', 'category': 'hr', 'is_popular': True},
            {'name': 'Time Off', 'technical_name': 'hr_holidays', 'category': 'hr'},
            {'name': 'Payroll', 'technical_name': 'hr_payroll', 'category': 'hr'},
            
            # Project
            {'name': 'Project Management', 'technical_name': 'project', 'category': 'project', 'is_popular': True},
            {'name': 'Timesheets', 'technical_name': 'hr_timesheet', 'category': 'project'},
            
            # Website & E-commerce
            {'name': 'Website Builder', 'technical_name': 'website', 'category': 'website', 'is_popular': True},
            {'name': 'E-commerce', 'technical_name': 'website_sale', 'category': 'website'},
            
            # Marketing
            {'name': 'Email Marketing', 'technical_name': 'mass_mailing', 'category': 'marketing'},
            {'name': 'Events', 'technical_name': 'event', 'category': 'marketing'},
            
            # Productivity
            {'name': 'Calendar', 'technical_name': 'calendar', 'category': 'productivity', 'is_popular': True},
            {'name': 'Contacts', 'technical_name': 'contacts', 'category': 'productivity', 'is_popular': True},
            {'name': 'Documents', 'technical_name': 'documents', 'category': 'productivity'},
        ]
        
        for module_data in default_modules:
            if not self.search([('technical_name', '=', module_data['technical_name'])]):
                self.create(module_data)

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaasPlanAddon(models.Model):
    _name = 'saas.plan.addon'
    _description = 'SaaS Plan Add-on'
    _order = 'sequence, name'

    name = fields.Char(
        string='Add-on Name',
        required=True,
        help='Tên của add-on'
    )
    
    code = fields.Char(
        string='Add-on Code',
        required=True,
        help='Mã add-on duy nhất'
    )
    
    description = fields.Text(
        string='Description',
        help='Mô tả chi tiết về add-on'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    plan_id = fields.Many2one(
        'saas.plan',
        string='Plan',
        required=True,
        ondelete='cascade',
        help='Gói dịch vụ mà add-on này thuộc về'
    )
    
    addon_type = fields.Selection([
        ('feature', 'Feature Enhancement'),
        ('limit', 'Limit Increase'),
        ('module', 'Additional Module'),
        ('service', 'Additional Service'),
        ('integration', 'Third-party Integration'),
        ('customization', 'Customization'),
        ('support', 'Support Package')
    ], string='Add-on Type', required=True, default='feature')
    
    category = fields.Selection([
        ('storage', 'Storage'),
        ('users', 'Users'),
        ('integration', 'Integration'),
        ('support', 'Support'),
        ('customization', 'Customization'),
        ('features', 'Features'),
        ('other', 'Other')
    ], string='Category', required=True, default='other')
    
    # Pricing
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    monthly_price = fields.Monetary(
        string='Monthly Price',
        currency_field='currency_id',
        help='Giá hàng tháng của add-on'
    )
    
    yearly_price = fields.Monetary(
        string='Yearly Price',
        currency_field='currency_id',
        help='Giá hàng năm của add-on'
    )
    
    setup_fee = fields.Monetary(
        string='Setup Fee',
        currency_field='currency_id',
        help='Phí thiết lập ban đầu'
    )
    
    # Configuration
    is_required = fields.Boolean(
        string='Required',
        default=False,
        help='Add-on bắt buộc phải có'
    )
    
    max_quantity = fields.Integer(
        string='Max Quantity',
        default=1,
        help='Số lượng tối đa có thể mua'
    )
    
    unlimited_quantity = fields.Boolean(
        string='Unlimited Quantity',
        default=False
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Specification cho từng loại add-on
    additional_users = fields.Integer(
        string='Additional Users',
        default=0,
        help='Số người dùng bổ sung (cho addon type = limit)'
    )
    
    additional_storage_gb = fields.Float(
        string='Additional Storage (GB)',
        default=0.0,
        help='Dung lượng lưu trữ bổ sung'
    )
    
    additional_api_calls = fields.Integer(
        string='Additional API Calls',
        default=0,
        help='Số lượng API calls bổ sung mỗi ngày'
    )
    
    additional_emails = fields.Integer(
        string='Additional Emails',
        default=0,
        help='Số email bổ sung mỗi tháng'
    )
    
    included_modules = fields.Text(
        string='Included Modules',
        help='Các module bổ sung (cách nhau bởi dấu phẩy)'
    )
    
    # Support specifications
    support_level = fields.Selection([
        ('basic', 'Basic'),
        ('priority', 'Priority'),
        ('premium', 'Premium'),
        ('dedicated', 'Dedicated')
    ], string='Support Level', default='basic')
    
    response_time_hours = fields.Float(
        string='Response Time (Hours)',
        default=24.0,
        help='Thời gian phản hồi cam kết'
    )
    
    # Dependencies
    depends_on_addon_ids = fields.Many2many(
        'saas.plan.addon',
        'saas_addon_dependency_rel',
        'addon_id',
        'depends_on_id',
        string='Depends on Add-ons',
        help='Add-on này phụ thuộc vào các add-on khác'
    )
    
    conflicts_with_addon_ids = fields.Many2many(
        'saas.plan.addon',
        'saas_addon_conflict_rel',
        'addon_id',
        'conflicts_with_id',
        string='Conflicts with Add-ons',
        help='Add-on này xung đột với các add-on khác'
    )
    
    # Computed fields
    effective_monthly_price = fields.Monetary(
        string='Effective Monthly Price',
        compute='_compute_effective_prices',
        currency_field='currency_id',
        store=True
    )
    
    effective_yearly_price = fields.Monetary(
        string='Effective Yearly Price',
        compute='_compute_effective_prices',
        currency_field='currency_id',
        store=True
    )
    
    _sql_constraints = [
        ('positive_prices', 'CHECK(monthly_price >= 0 AND yearly_price >= 0)', 
         'Prices must be positive!'),
        ('positive_quantities', 'CHECK(max_quantity > 0)', 
         'Max quantity must be positive!'),
        ('unique_code_per_plan', 'UNIQUE(plan_id, code)', 
         'Add-on code must be unique per plan!')
    ]
    
    @api.depends('monthly_price', 'yearly_price')
    def _compute_effective_prices(self):
        for addon in self:
            addon.effective_monthly_price = addon.monthly_price
            if addon.yearly_price > 0:
                addon.effective_yearly_price = addon.yearly_price
            else:
                addon.effective_yearly_price = addon.monthly_price * 12
    
    @api.constrains('depends_on_addon_ids')
    def _check_addon_dependencies(self):
        for addon in self:
            if addon in addon.depends_on_addon_ids:
                raise ValidationError("Add-on cannot depend on itself!")
    
    @api.constrains('conflicts_with_addon_ids')
    def _check_addon_conflicts(self):
        for addon in self:
            if addon in addon.conflicts_with_addon_ids:
                raise ValidationError("Add-on cannot conflict with itself!")
    
    def name_get(self):
        """Custom name display"""
        result = []
        for addon in self:
            name = addon.name
            if addon.addon_type:
                name += f" ({addon.addon_type.replace('_', ' ').title()})"
            if addon.is_required:
                name += " [Required]"
            result.append((addon.id, name))
        return result

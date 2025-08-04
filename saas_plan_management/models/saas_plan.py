# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json

class SaasPlan(models.Model):
    _name = 'saas.plan'
    _description = 'SaaS Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    
    def name_get(self):
        """Custom name display"""
        result = []
        for plan in self:
            name = plan.name
            if plan.plan_type:
                name += f" ({plan.plan_type.title()})"
            if not plan.active:
                name += " [Inactive]"
            result.append((plan.id, name))
        return result

    # Thông tin cơ bản
    name = fields.Char(
        string='Plan Name',
        required=True,
        tracking=True,
        help='Tên gói dịch vụ (VD: Basic, Standard, Premium)'
    )
    
    code = fields.Char(
        string='Plan Code',
        required=True,
        help='Mã gói dịch vụ (VD: BASIC, STD, PREM)'
    )
    
    description = fields.Text(
        string='Description',
        help='Mô tả chi tiết về gói dịch vụ'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Thứ tự hiển thị'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    # Template relationship
    template_id = fields.Many2one(
        'saas.plan.template',
        string='Created from Template',
        help='Template sử dụng để tạo plan này',
        ondelete='set null'
    )
    
    # Phân loại gói
    plan_type = fields.Selection([
        ('free', 'Free Trial'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom')
    ], string='Plan Type', required=True, default='basic', tracking=True)
    
    # Thông tin giá
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    monthly_price = fields.Monetary(
        string='Monthly Price',
        currency_field='currency_id',
        tracking=True,
        help='Giá hàng tháng'
    )
    
    quarterly_price = fields.Monetary(
        string='Quarterly Price',
        currency_field='currency_id',
        help='Giá hàng quý (3 tháng)'
    )
    
    yearly_price = fields.Monetary(
        string='Yearly Price',
        currency_field='currency_id',
        tracking=True,
        help='Giá hàng năm'
    )
    
    setup_fee = fields.Monetary(
        string='Setup Fee',
        currency_field='currency_id',
        help='Phí thiết lập ban đầu'
    )
    
    # Chu kỳ thanh toán
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom')
    ], string='Default Billing Cycle', default='monthly', required=True)
    
    # Giới hạn người dùng
    max_users = fields.Integer(
        string='Max Users',
        default=1,
        help='Số lượng người dùng tối đa'
    )
    
    unlimited_users = fields.Boolean(
        string='Unlimited Users',
        default=False,
        help='Không giới hạn số lượng người dùng'
    )
    
    # Giới hạn dữ liệu
    storage_limit_gb = fields.Float(
        string='Storage Limit (GB)',
        default=1.0,
        help='Giới hạn dung lượng lưu trữ (GB)'
    )
    
    unlimited_storage = fields.Boolean(
        string='Unlimited Storage',
        default=False
    )
    
    # Giới hạn giao dịch
    transaction_limit_monthly = fields.Integer(
        string='Monthly Transaction Limit',
        default=100,
        help='Giới hạn số giao dịch mỗi tháng'
    )
    
    unlimited_transactions = fields.Boolean(
        string='Unlimited Transactions',
        default=False
    )
    
    # Giới hạn API
    api_calls_limit_daily = fields.Integer(
        string='Daily API Calls Limit',
        default=1000,
        help='Giới hạn số lượng API calls mỗi ngày'
    )
    
    unlimited_api_calls = fields.Boolean(
        string='Unlimited API Calls',
        default=False
    )
    
    # Giới hạn email
    email_limit_monthly = fields.Integer(
        string='Monthly Email Limit',
        default=100,
        help='Giới hạn số email gửi mỗi tháng'
    )
    
    unlimited_emails = fields.Boolean(
        string='Unlimited Emails',
        default=False
    )
    
    # Quan hệ với module Odoo
    included_module_ids = fields.Many2many(
        'saas.odoo.module',
        'saas_plan_module_rel',
        'plan_id',
        'module_id',
        string='Included Modules',
        help='Các module Odoo được bao gồm trong gói'
    )
    
    # Quan hệ với add-ons
    addon_ids = fields.One2many(
        'saas.plan.addon',
        'plan_id',
        string='Available Add-ons',
        help='Các add-on có thể mua thêm cho gói này'
    )    
    
    # Quan hệ với customers (thông qua instances)    # Note: instance_ids removed to avoid circular dependency
    # Use instance_count computed field instead
    
    # Features
    multi_company_support = fields.Boolean(
        string='Multi-Company Support',
        default=False
    )
    
    custom_domain_support = fields.Boolean(
        string='Custom Domain Support',
        default=False
    )
    
    api_access_enabled = fields.Boolean(
        string='API Access',
        default=True
    )
    
    priority_support = fields.Boolean(
        string='Priority Support',
        default=False
    )
    
    white_label_option = fields.Boolean(
        string='White Label Option',
        default=False
    )
    
    backup_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('none', 'No Backup')
    ], string='Backup Frequency', default='weekly')
    
    # Computed fields
    module_count = fields.Integer(
        string='Module Count',
        compute='_compute_module_count',
        store=True
    )
    
    addon_count = fields.Integer(
        string='Add-on Count',
        compute='_compute_addon_count',
        store=True    )
    
    # Computed fields for statistics
    # instance_count = fields.Integer(
    #     string='Instance Count',
    #     compute='_compute_instance_count',
    #     help='Số lượng instances sử dụng plan này'
    # )
    
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
    
    # Constraints
    _sql_constraints = [
        ('positive_prices', 'CHECK(monthly_price >= 0 AND yearly_price >= 0)', 
         'Prices must be positive!'),
        ('positive_limits', 'CHECK(max_users > 0 AND storage_limit_gb > 0)', 
         'Limits must be positive!'),
        ('unique_code', 'UNIQUE(code)', 
         'Plan code must be unique!')
    ]
    
    @api.depends('included_module_ids')
    def _compute_module_count(self):
        for plan in self:
            plan.module_count = len(plan.included_module_ids)
    
    @api.depends('addon_ids')
    def _compute_addon_count(self):
        for plan in self:
            plan.addon_count = len(plan.addon_ids)
    
    # def _compute_instance_count(self):
    #     """Compute number of instances using this plan"""
    #     for plan in self:
    #         # Use lazy loading to avoid dependency issues
    #         if 'saas.instance' in self.env:
    #             plan.instance_count = self.env['saas.instance'].search_count([('plan_id', '=', plan.id)])
    #         else:
    #             plan.instance_count = 0
    
    @api.depends('monthly_price', 'yearly_price', 'quarterly_price')
    def _compute_effective_prices(self):
        for plan in self:
            plan.effective_monthly_price = plan.monthly_price
            if plan.yearly_price > 0:
                plan.effective_yearly_price = plan.yearly_price
            else:
                plan.effective_yearly_price = plan.monthly_price * 12
    
    @api.constrains('max_users')
    def _check_max_users(self):
        for plan in self:
            if not plan.unlimited_users and plan.max_users <= 0:
                raise ValidationError(_('Max users must be greater than 0 when not unlimited.'))
    
    @api.constrains('storage_limit_gb')
    def _check_storage_limit(self):
        for plan in self:
            if not plan.unlimited_storage and plan.storage_limit_gb <= 0:
                raise ValidationError(_('Storage limit must be greater than 0 when not unlimited.'))
    
    def name_get(self):
        """Custom name display"""
        result = []
        for plan in self:
            name = plan.name
            if plan.plan_type:
                name += f" ({plan.plan_type.title()})"
            if not plan.active:
                name += " [Inactive]"
            result.append((plan.id, name))
        return result
    
    # def action_view_instances(self):
    #     """Action to view instances using this plan"""
    #     # Check if saas.instance model exists
    #     if 'saas.instance' not in self.env:
    #         raise UserError(_('SaaS Instance model is not available. Please install SaaS Customer Management module.'))
        
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': f'Instances using {self.name}',
    #         'res_model': 'saas.instance',
    #         'view_mode': 'tree,form',
    #         'domain': [('plan_id', '=', self.id)],
    #         'context': {'default_plan_id': self.id},
    #         'target': 'current',
    #     }
    
    def action_view_modules(self):
        """Action to view included modules"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Included Modules'),
            'res_model': 'saas.odoo.module',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.included_module_ids.ids)]
        }
    
    def action_view_addons(self):
        """Action to view available add-ons"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Available Add-ons'),
            'res_model': 'saas.plan.addon',
            'view_mode': 'tree,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id}
        }
    
    def get_price_for_billing_cycle(self, billing_cycle):
        """Get price for specific billing cycle"""
        if billing_cycle == 'monthly':
            return self.monthly_price
        elif billing_cycle == 'quarterly':
            return self.quarterly_price or (self.monthly_price * 3)
        elif billing_cycle == 'yearly':
            return self.yearly_price or (self.monthly_price * 12)
        return 0.0
    
    def can_upgrade_to(self, target_plan):
        """Check if can upgrade from this plan to target plan"""
        if not target_plan:
            return False
        
        # Logic to determine if upgrade is possible
        plan_hierarchy = {
            'free': 0,
            'basic': 1,
            'standard': 2,
            'premium': 3,
            'enterprise': 4,
            'custom': 5
        }
        
        current_level = plan_hierarchy.get(self.plan_type, 0)
        target_level = plan_hierarchy.get(target_plan.plan_type, 0)
        
        return target_level > current_level
    
    def duplicate_plan(self):
        """Duplicate plan with new code"""
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

from odoo import models, fields, api
from datetime import datetime, timedelta

class SaasInstance(models.Model):
    _name = 'saas.instance'
    _description = 'SaaS Instance'
    _rec_name = 'instance_name'
    _order = 'date_created desc'

    instance_name = fields.Char(string='Instance Name', required=True)
    subdomain = fields.Char(string='Subdomain', required=True)
    full_url = fields.Char(string='Full URL', compute='_compute_full_url', store=True)
    
    # Thông tin kỹ thuật
    database_id = fields.Char(string='Database ID')
    odoo_version = fields.Selection([
        ('15.0', 'Odoo 15.0'),
        ('16.0', 'Odoo 16.0'),
        ('17.0', 'Odoo 17.0'),
        ('18.0', 'Odoo 18.0')
    ], string='Odoo Version', default='17.0', required=True)
    
    server_location = fields.Selection([
        ('us-east', 'US East'),
        ('eu-west', 'EU West'),
        ('asia-pacific', 'Asia Pacific')
    ], string='Server Location', default='us-east')
    
    # Quan hệ
    customer_id = fields.Many2one('saas.customer', string='Customer', required=True, ondelete='cascade')
    service_package_id = fields.Many2one('saas.service.package', string='Service Package', required=True)
    # plan_id = fields.Many2one('saas.plan', string='Plan')
    
    # Plan related fields
    # plan_name = fields.Char(string='Plan Name', related='plan_id.name', readonly=True)
    # plan_type = fields.Selection(related='plan_id.plan_type', string='Plan Type', readonly=True)
    # plan_currency_id = fields.Many2one(related='plan_id.currency_id', readonly=True)
    # plan_monthly_price = fields.Monetary(related='plan_id.monthly_price', string='Monthly Price', currency_field='plan_currency_id', readonly=True)
    # plan_quarterly_price = fields.Monetary(related='plan_id.quarterly_price', string='Quarterly Price', currency_field='plan_currency_id', readonly=True)
    # plan_yearly_price = fields.Monetary(related='plan_id.yearly_price', string='Yearly Price', currency_field='plan_currency_id', readonly=True)
    # plan_storage_limit_gb = fields.Float(related='plan_id.storage_limit_gb', string='Storage Limit (GB)', readonly=True)
    # plan_max_users = fields.Integer(related='plan_id.max_users', string='Max Users', readonly=True)
    
    # Computed price based on billing cycle
    # current_price = fields.Monetary(
    #     string='Current Price',
    #     compute='_compute_current_price',
    #     currency_field='plan_currency_id',
    #     help='Price based on selected billing cycle'
    # )
    
    # Trạng thái và thời gian
    status = fields.Selection([
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated')
    ], string='Status', default='trial', required=True)

    date_created = fields.Datetime(string='Created Date', default=fields.Datetime.now, readonly=True)
    date_activated = fields.Datetime(string='Activated Date', readonly=True)
    trial_end_date = fields.Datetime(string='Trial End Date', compute='_compute_trial_end_date', store=True)
    subscription_end_date = fields.Date(string='Subscription End Date')
    
    # Thông tin subscription
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Billing Cycle', default='monthly')
    
    # Sử dụng tài nguyên
    current_users = fields.Integer(string='Current Users', default=1)
    storage_used_gb = fields.Float(string='Storage Used (GB)', default=0.0)    
    
    # Computed fields
    days_until_expiry = fields.Integer(string='Days Until Expiry', compute='_compute_days_until_expiry', store=True)
    storage_percentage = fields.Float(string='Storage Usage %', compute='_compute_storage_percentage')
    
    @api.depends('subdomain')
    def _compute_full_url(self):
        for instance in self:
            if instance.subdomain:
                instance.full_url = f"https://{instance.subdomain}.odoo.com"
            else:
                instance.full_url = ""
    
    @api.depends('date_created')
    def _compute_trial_end_date(self):
        for instance in self:
            if instance.date_created:
                # Thêm 7 ngày từ ngày tạo để tính ngày kết thúc trial
                instance.trial_end_date = instance.date_created + timedelta(days=7)
            else:
                instance.trial_end_date = False
    
    @api.depends('subscription_end_date')
    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for instance in self:
            if instance.subscription_end_date:
                delta = instance.subscription_end_date - today
                instance.days_until_expiry = delta.days
            else:
                instance.days_until_expiry = 0
    
    @api.depends('storage_used_gb', 'service_package_id.storage_gb')
    def _compute_storage_percentage(self):
        for instance in self:
            if instance.service_package_id.storage_gb > 0:
                instance.storage_percentage = (instance.storage_used_gb / instance.service_package_id.storage_gb) * 100
            else:
                instance.storage_percentage = 0.0

    # @api.depends('storage_used_gb', 'plan_id.storage_limit_gb')
    # def _compute_storage_percentage(self):
    #     for instance in self:
    #         if instance.plan_id and instance.plan_id.storage_limit_gb > 0:
    #             instance.storage_percentage = (instance.storage_used_gb / instance.plan_id.storage_limit_gb) * 100
    #         else:
    #             instance.storage_percentage = 0.0
    
    # @api.depends('plan_id', 'billing_cycle')
    # def _compute_current_price(self):
    #     """Compute current price based on billing cycle"""
    #     for instance in self:
    #         if instance.plan_id:
    #             if instance.billing_cycle == 'monthly':
    #                 instance.current_price = instance.plan_id.monthly_price
    #             elif instance.billing_cycle == 'quarterly':
    #                 instance.current_price = instance.plan_id.quarterly_price
    #             elif instance.billing_cycle == 'yearly':
    #                 instance.current_price = instance.plan_id.yearly_price
    #             else:
    #                 instance.current_price = 0.0
    #         else:
    #             instance.current_price = 0.0
    
    # @api.onchange('plan_id')
    # def _onchange_plan_id(self):
    #     """Auto update billing cycle based on plan's default billing cycle"""
    #     if self.plan_id and self.plan_id.billing_cycle:
    #         self.billing_cycle = self.plan_id.billing_cycle
    
    def action_activate(self):
        self.write({
            'status': 'active',
            'date_activated': fields.Datetime.now()
        })
        return True
    
    def action_suspend(self):
        self.write({'status': 'suspended'})
        return True
    
    def action_terminate(self):
        self.write({'status': 'terminated'})
        return True
    
    def action_extend_trial(self):
        if self.trial_end_date:
            self.trial_end_date = self.trial_end_date + timedelta(days=7)
        else:
            self.trial_end_date = fields.Date.today() + timedelta(days=7)
        return True
    
    def action_view_payment_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment History',
            'res_model': 'saas.payment.history',
            'view_mode': 'tree,form',
            'domain': [('instance_id', '=', self.id)],
            'context': {'default_instance_id': self.id, 'default_customer_id': self.customer_id.id}
        }

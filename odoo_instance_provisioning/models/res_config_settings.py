# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Provisioning Settings
    saas_base_domain = fields.Char(
        'Base Domain',
        config_parameter='saas.base_domain',
        default='odoo.saas.com',
        help='Base domain for instance subdomains (e.g., customer.yourdomain.com)'
    )
    
    saas_docker_image = fields.Char(
        'Docker Image',
        config_parameter='saas.docker_image', 
        default='odoo:17.0',
        help='Docker image to use for new instances'
    )
    
    saas_backup_path = fields.Char(
        'Backup Path',
        config_parameter='saas.backup_path',
        default='/opt/odoo/backups',
        help='Directory path for storing instance backups'
    )
    
    saas_max_instances_per_plan = fields.Integer(
        'Max Instances per Plan',
        config_parameter='saas.max_instances_per_plan',
        default=100,
        help='Maximum number of instances allowed per service plan'
    )
    
    saas_default_cpu_limit = fields.Float(
        'Default CPU Limit',
        config_parameter='saas.default_cpu_limit',
        default=1.0,
        help='Default CPU limit in cores for new instances'
    )
    
    saas_default_memory_limit = fields.Integer(
        'Default Memory Limit',
        config_parameter='saas.default_memory_limit', 
        default=1024,
        help='Default memory limit in MB for new instances'
    )
    
    saas_default_storage_limit = fields.Integer(
        'Default Storage Limit',
        config_parameter='saas.default_storage_limit',
        default=10,
        help='Default storage limit in GB for new instances'
    )
    
    # Monitoring Settings
    saas_enable_monitoring = fields.Boolean(
        'Enable Resource Monitoring',
        config_parameter='saas.enable_monitoring',
        default=True,
        help='Enable automatic resource usage monitoring'
    )
    
    saas_monitoring_interval = fields.Integer(
        'Monitoring Interval',
        config_parameter='saas.monitoring_interval',
        default=15,
        help='Resource monitoring interval in minutes'
    )
    
    # Backup Settings
    saas_enable_auto_backup = fields.Boolean(
        'Enable Auto Backup',
        config_parameter='saas.enable_auto_backup',
        default=True,
        help='Enable automatic backup for all instances'
    )
    
    saas_backup_retention_days = fields.Integer(
        'Backup Retention Days',
        config_parameter='saas.backup_retention_days',
        default=30,
        help='Number of days to keep backup files'
    )
    
    # API Settings
    saas_api_rate_limit = fields.Integer(
        'API Rate Limit',
        config_parameter='saas.api_rate_limit',
        default=100,
        help='API requests per hour limit per IP'
    )
    
    saas_enable_api_auth = fields.Boolean(
        'Enable API Authentication',
        config_parameter='saas.enable_api_auth',
        default=False,
        help='Require authentication for API endpoints'
    )
    
    # Notification Settings
    saas_admin_email = fields.Char(
        'Admin Email',
        config_parameter='saas.admin_email',
        help='Email address for admin notifications'
    )
    
    saas_enable_notifications = fields.Boolean(
        'Enable Email Notifications',
        config_parameter='saas.enable_notifications',
        default=True,
        help='Send email notifications for important events'
    )
    
    @api.model
    def get_values(self):
        res = super().get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        res.update(
            saas_base_domain=ICPSudo.get_param('saas.base_domain', 'odoo.saas.com'),
            saas_docker_image=ICPSudo.get_param('saas.docker_image', 'odoo:17.0'),
            saas_backup_path=ICPSudo.get_param('saas.backup_path', '/opt/odoo/backups'),
            saas_max_instances_per_plan=int(ICPSudo.get_param('saas.max_instances_per_plan', 100)),
            saas_default_cpu_limit=float(ICPSudo.get_param('saas.default_cpu_limit', 1.0)),
            saas_default_memory_limit=int(ICPSudo.get_param('saas.default_memory_limit', 1024)),
            saas_default_storage_limit=int(ICPSudo.get_param('saas.default_storage_limit', 10)),
            saas_enable_monitoring=ICPSudo.get_param('saas.enable_monitoring', 'True').lower() == 'true',
            saas_monitoring_interval=int(ICPSudo.get_param('saas.monitoring_interval', 15)),
            saas_enable_auto_backup=ICPSudo.get_param('saas.enable_auto_backup', 'True').lower() == 'true',
            saas_backup_retention_days=int(ICPSudo.get_param('saas.backup_retention_days', 30)),
            saas_api_rate_limit=int(ICPSudo.get_param('saas.api_rate_limit', 100)),
            saas_enable_api_auth=ICPSudo.get_param('saas.enable_api_auth', 'False').lower() == 'true',
            saas_admin_email=ICPSudo.get_param('saas.admin_email', ''),
            saas_enable_notifications=ICPSudo.get_param('saas.enable_notifications', 'True').lower() == 'true',
        )
        return res
    
    def set_values(self):
        super().set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        ICPSudo.set_param('saas.base_domain', self.saas_base_domain or 'odoo.saas.com')
        ICPSudo.set_param('saas.docker_image', self.saas_docker_image or 'odoo:17.0')
        ICPSudo.set_param('saas.backup_path', self.saas_backup_path or '/opt/odoo/backups')
        ICPSudo.set_param('saas.max_instances_per_plan', self.saas_max_instances_per_plan)
        ICPSudo.set_param('saas.default_cpu_limit', self.saas_default_cpu_limit)
        ICPSudo.set_param('saas.default_memory_limit', self.saas_default_memory_limit)
        ICPSudo.set_param('saas.default_storage_limit', self.saas_default_storage_limit)
        ICPSudo.set_param('saas.enable_monitoring', self.saas_enable_monitoring)
        ICPSudo.set_param('saas.monitoring_interval', self.saas_monitoring_interval)
        ICPSudo.set_param('saas.enable_auto_backup', self.saas_enable_auto_backup)
        ICPSudo.set_param('saas.backup_retention_days', self.saas_backup_retention_days)
        ICPSudo.set_param('saas.api_rate_limit', self.saas_api_rate_limit)
        ICPSudo.set_param('saas.enable_api_auth', self.saas_enable_api_auth)
        ICPSudo.set_param('saas.admin_email', self.saas_admin_email or '')
        ICPSudo.set_param('saas.enable_notifications', self.saas_enable_notifications)

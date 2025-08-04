# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaasInstanceRequest(models.Model):
    _name = 'saas.instance.request'
    _description = 'SaaS Instance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'request_id'

    # Request Information
    request_id = fields.Char('Request ID', required=True, default=lambda self: self._generate_request_id())
    source = fields.Selection([
        ('portal', 'Registration Portal'),
        ('manual', 'Manual'),
        ('api', 'API'),
    ], string='Source', default='portal', required=True)
    
    # Customer Information
    customer_email = fields.Char('Customer Email', required=True)
    customer_name = fields.Char('Customer Name', required=True)
    customer_phone = fields.Char('Customer Phone')
    company_name = fields.Char('Company Name', required=True)
    
    # Instance Configuration
    plan_id = fields.Many2one('saas.plan', 'Service Plan', required=True)
    database_name = fields.Char('Database Name', required=True)
    subdomain = fields.Char('Sub-domain', required=True)
    admin_email = fields.Char('Admin Email', required=True)
    admin_password = fields.Char('Admin Password')
    
    # Request Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('validated', 'Validated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Processing Information
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='normal')
    
    # Relationships
    instance_id = fields.Many2one('saas.instance.provisioning', 'Created Instance', readonly=True)
    customer_id = fields.Many2one('saas.customer', 'Customer')
    
    # Additional Data
    raw_data = fields.Text('Raw Request Data', help='Original JSON data from the request')
    validation_errors = fields.Text('Validation Errors')
    processing_notes = fields.Text('Processing Notes')
    
    # Dates
    submitted_date = fields.Datetime('Submitted Date')
    validated_date = fields.Datetime('Validated Date')
    processing_start_date = fields.Datetime('Processing Start Date')
    completed_date = fields.Datetime('Completed Date')
    
    # Estimated times
    estimated_processing_time = fields.Integer('Estimated Processing Time (minutes)', default=30)
    actual_processing_time = fields.Integer('Actual Processing Time (minutes)', compute='_compute_actual_processing_time')
    
    @api.model
    def _generate_request_id(self):
        """Generate unique request ID"""
        return f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    @api.depends('processing_start_date', 'completed_date')
    def _compute_actual_processing_time(self):
        """Compute actual processing time"""
        for record in self:
            if record.processing_start_date and record.completed_date:
                delta = record.completed_date - record.processing_start_date
                record.actual_processing_time = int(delta.total_seconds() / 60)
            else:
                record.actual_processing_time = 0
    
    @api.constrains('subdomain')
    def _check_subdomain_format(self):
        """Validate subdomain format"""
        import re
        for record in self:
            if record.subdomain:
                if not re.match(r'^[a-z0-9-]+$', record.subdomain):
                    raise ValidationError(_('Subdomain can only contain lowercase letters, numbers, and hyphens.'))
                if len(record.subdomain) < 3 or len(record.subdomain) > 63:
                    raise ValidationError(_('Subdomain must be between 3 and 63 characters long.'))
                if record.subdomain.startswith('-') or record.subdomain.endswith('-'):
                    raise ValidationError(_('Subdomain cannot start or end with a hyphen.'))
    
    @api.constrains('database_name')
    def _check_database_name_format(self):
        """Validate database name format"""
        import re
        for record in self:
            if record.database_name:
                if not re.match(r'^[a-z0-9_]+$', record.database_name):
                    raise ValidationError(_('Database name can only contain lowercase letters, numbers, and underscores.'))
                if len(record.database_name) < 3 or len(record.database_name) > 63:
                    raise ValidationError(_('Database name must be between 3 and 63 characters long.'))
    
    @api.model
    def create(self, vals):
        """Override create to set default values and validate"""
        # Generate admin password if not provided
        if not vals.get('admin_password'):
            vals['admin_password'] = self._generate_password()
        
        # Set database name based on subdomain if not provided
        if not vals.get('database_name') and vals.get('subdomain'):
            vals['database_name'] = vals['subdomain'].replace('-', '_')
        
        # Set admin email same as customer email if not provided
        if not vals.get('admin_email') and vals.get('customer_email'):
            vals['admin_email'] = vals['customer_email']
        
        return super().create(vals)
    
    def _generate_password(self):
        """Generate secure password"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for i in range(12))
    
    @api.model
    def create_from_portal_data(self, data):
        """Create instance request from portal registration data"""
        try:
            # Validate required fields
            required_fields = ['customer_email', 'customer_name', 'company_name', 
                             'plan_id', 'subdomain']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                raise ValidationError(_('Missing required fields: %s') % ', '.join(missing_fields))
            
            # Create request
            vals = {
                'source': 'portal',
                'customer_email': data['customer_email'],
                'customer_name': data['customer_name'],
                'customer_phone': data.get('customer_phone', ''),
                'company_name': data['company_name'],
                'plan_id': data['plan_id'],
                'subdomain': data['subdomain'],
                'admin_email': data.get('admin_email', data['customer_email']),
                'admin_password': data.get('admin_password'),
                'raw_data': json.dumps(data),
                'state': 'submitted',
                'submitted_date': fields.Datetime.now(),
            }
            
            request = self.create(vals)
            
            # Auto-validate if all data is correct
            request.action_validate()
            
            return request
            
        except Exception as e:
            _logger.error(f"Failed to create instance request from portal data: {str(e)}")
            raise UserError(_('Failed to create instance request: %s') % str(e))
    
    def action_submit(self):
        """Submit the request for validation"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            
            record.state = 'submitted'
            record.submitted_date = fields.Datetime.now()
            
            # Auto-validate if possible
            try:
                record.action_validate()
            except:
                pass  # Validation will be done manually
    
    def action_validate(self):
        """Validate the request"""
        for record in self:
            if record.state not in ['submitted', 'validated']:
                raise UserError(_('Only submitted requests can be validated.'))
            
            errors = []
            
            # Check if subdomain is available
            existing_instance = self.env['saas.instance.provisioning'].search([
                ('subdomain', '=', record.subdomain),
                ('state', '!=', 'terminated')
            ])
            if existing_instance:
                errors.append(f'Subdomain "{record.subdomain}" is already in use')
            
            # Check if database name is available
            existing_instance = self.env['saas.instance.provisioning'].search([
                ('database_name', '=', record.database_name),
                ('state', '!=', 'terminated')
            ])
            if existing_instance:
                errors.append(f'Database name "{record.database_name}" is already in use')
            
            # Check if plan exists and is active
            if not record.plan_id or not record.plan_id.active:
                errors.append('Selected service plan is not available')
            
            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, record.customer_email):
                errors.append('Invalid customer email format')
            if not re.match(email_pattern, record.admin_email):
                errors.append('Invalid admin email format')
            
            if errors:
                record.validation_errors = '\n'.join(errors)
                record.state = 'failed'
                raise UserError(_('Validation failed:\n%s') % '\n'.join(errors))
            else:
                record.validation_errors = False
                record.state = 'validated'
                record.validated_date = fields.Datetime.now()
                
                # Auto-start processing
                record.action_process()
    
    def action_process(self):
        """Start processing the request"""
        for record in self:
            if record.state != 'validated':
                raise UserError(_('Only validated requests can be processed.'))
            
            record.state = 'processing'
            record.processing_start_date = fields.Datetime.now()
            
            try:
                # Find or create customer
                customer = record._find_or_create_customer()
                record.customer_id = customer.id
                
                # Create instance
                instance_vals = {
                    'name': f'{record.company_name} - {record.plan_id.name}',
                    'subdomain': record.subdomain,
                    'database_name': record.database_name,
                    'plan_id': record.plan_id.id,
                    'admin_email': record.admin_email,
                    'admin_password': record.admin_password,
                    'company_name': record.company_name,
                    'customer_id': customer.id,
                    'instance_request_id': record.id,
                    'state': 'draft',
                }
                
                instance = self.env['saas.instance.provisioning'].create(instance_vals)
                record.instance_id = instance.id
                
                # Start provisioning
                instance.action_provision()
                
                record.state = 'completed'
                record.completed_date = fields.Datetime.now()
                record.processing_notes = 'Instance created and provisioning started successfully'
                
            except Exception as e:
                record.state = 'failed'
                record.processing_notes = f'Processing failed: {str(e)}'
                _logger.error(f"Failed to process instance request {record.id}: {str(e)}")
                raise UserError(_('Processing failed: %s') % str(e))
    
    def _find_or_create_customer(self):
        """Find existing customer or create new one"""
        Customer = self.env['saas.customer']
        
        # Try to find existing customer by email
        customer = Customer.search([('contact_email', '=', self.customer_email)], limit=1)
        
        if not customer:
            # Create new customer
            customer_vals = {
                'contact_name': self.customer_name,
                'contact_email': self.customer_email,
                'contact_phone': self.customer_phone,
                'company_name': self.company_name,
                'email': self.customer_email,  # Company email
                'phone': self.customer_phone,  # Company phone
                'state': 'active',
            }
            customer = Customer.create(customer_vals)
        
        return customer
    
    def action_cancel(self):
        """Cancel the request"""
        for record in self:
            if record.state in ['completed', 'cancelled']:
                raise UserError(_('Completed or already cancelled requests cannot be cancelled.'))
            
            record.state = 'cancelled'
            
            # If instance was created, we might want to handle it
            if record.instance_id and record.instance_id.state == 'draft':
                record.instance_id.unlink()
    
    def action_retry(self):
        """Retry failed request"""
        for record in self:
            if record.state != 'failed':
                raise UserError(_('Only failed requests can be retried.'))
            
            # Reset to validated state and try again
            record.state = 'validated'
            record.validation_errors = False
            record.processing_notes = False
            record.action_process()
    
    @api.model
    def cron_process_pending_requests(self):
        """Cron job to process pending requests"""
        # Process submitted requests
        submitted_requests = self.search([('state', '=', 'submitted')])
        for request in submitted_requests:
            try:
                request.action_validate()
            except Exception as e:
                _logger.error(f"Failed to validate request {request.id}: {str(e)}")
        
        # Process validated requests
        validated_requests = self.search([('state', '=', 'validated')])
        for request in validated_requests:
            try:
                request.action_process()
            except Exception as e:
                _logger.error(f"Failed to process request {request.id}: {str(e)}")
    
    @api.model
    def cleanup_old_requests(self):
        """Clean up old completed/failed requests"""
        cutoff_date = fields.Datetime.now() - timedelta(days=30)
        old_requests = self.search([
            ('state', 'in', ['completed', 'failed', 'cancelled']),
            ('create_date', '<', cutoff_date)
        ])
        
        for request in old_requests:
            # Archive instead of delete to maintain history
            request.active = False
    
    def action_view_instance(self):
        """Open the created instance record"""
        self.ensure_one()
        if not self.instance_id:
            raise UserError(_('No instance has been created for this request yet.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Instance'),
            'res_model': 'saas.instance.provisioning',
            'res_id': self.instance_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def get_request_summary(self):
        """Get summary information for the request"""
        self.ensure_one()
        return {
            'request_id': self.request_id,
            'state': self.state,
            'customer_name': self.customer_name,
            'company_name': self.company_name,
            'subdomain': self.subdomain,
            'plan_name': self.plan_id.name,
            'submitted_date': self.submitted_date,
            'estimated_time': self.estimated_processing_time,
            'actual_time': self.actual_processing_time,
            'instance_url': self.instance_id.url if self.instance_id else None,
        }

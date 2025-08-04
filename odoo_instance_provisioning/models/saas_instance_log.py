# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaasInstanceProvisioningLog(models.Model):
    _name = 'saas.instance.provisioning.log'
    _description = 'SaaS Instance Provisioning Log'
    _order = 'timestamp desc'
    _rec_name = 'message'

    # Basic Information
    instance_id = fields.Many2one('saas.instance.provisioning', 'Instance', required=True, ondelete='cascade')
    timestamp = fields.Datetime('Timestamp', required=True, default=fields.Datetime.now)
    
    # Log Details
    level = fields.Selection([
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], string='Level', required=True, default='info')
    
    message = fields.Text('Message', required=True)
    details = fields.Text('Details')
    
    # Context Information
    operation = fields.Char('Operation', help='Operation being performed when log was created')
    component = fields.Char('Component', help='System component that generated the log')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    
    # Technical Details
    exception_type = fields.Char('Exception Type')
    stack_trace = fields.Text('Stack Trace')
    request_id = fields.Char('Request ID', help='Related request ID if applicable')
    
    # Computed Fields
    level_color = fields.Integer('Level Color', compute='_compute_level_color')
    formatted_timestamp = fields.Char('Formatted Timestamp', compute='_compute_formatted_timestamp')
    
    @api.depends('level')
    def _compute_level_color(self):
        """Compute color based on log level for UI display"""
        color_map = {
            'debug': 1,    # Gray
            'info': 10,    # Blue
            'warning': 3,  # Yellow
            'error': 9,    # Red
            'critical': 2, # Orange
        }
        for record in self:
            record.level_color = color_map.get(record.level, 0)
    
    @api.depends('timestamp')
    def _compute_formatted_timestamp(self):
        """Format timestamp for display"""
        for record in self:
            if record.timestamp:
                record.formatted_timestamp = record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                record.formatted_timestamp = ''
    
    @api.model
    def create_log(self, instance_id, level, message, **kwargs):
        """Helper method to create log entries"""
        vals = {
            'instance_id': instance_id,
            'level': level,
            'message': message,
            'timestamp': fields.Datetime.now(),
        }
        
        # Add optional fields
        for field in ['details', 'operation', 'component', 'exception_type', 
                     'stack_trace', 'request_id']:
            if field in kwargs:
                vals[field] = kwargs[field]
        
        return self.create(vals)
    
    @api.model
    def log_info(self, instance_id, message, **kwargs):
        """Create info log entry"""
        return self.create_log(instance_id, 'info', message, **kwargs)
    
    @api.model
    def log_warning(self, instance_id, message, **kwargs):
        """Create warning log entry"""
        return self.create_log(instance_id, 'warning', message, **kwargs)
    
    @api.model
    def log_error(self, instance_id, message, **kwargs):
        """Create error log entry"""
        return self.create_log(instance_id, 'error', message, **kwargs)
    
    @api.model
    def log_critical(self, instance_id, message, **kwargs):
        """Create critical log entry"""
        return self.create_log(instance_id, 'critical', message, **kwargs)
    
    @api.model
    def log_debug(self, instance_id, message, **kwargs):
        """Create debug log entry"""
        return self.create_log(instance_id, 'debug', message, **kwargs)
    
    @api.model
    def log_exception(self, instance_id, exception, operation=None):
        """Create log entry from exception"""
        import traceback
        
        vals = {
            'instance_id': instance_id,
            'level': 'error',
            'message': str(exception),
            'exception_type': type(exception).__name__,
            'stack_trace': traceback.format_exc(),
            'operation': operation,
            'timestamp': fields.Datetime.now(),
        }
        
        return self.create(vals)
    
    def action_view_instance(self):
        """Navigate to the related instance"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Instance'),
            'res_model': 'saas.instance',
            'res_id': self.instance_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def cleanup_old_logs(self, days=30):
        """Clean up old log entries"""
        from datetime import timedelta
        
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([
            ('timestamp', '<', cutoff_date),
            ('level', 'in', ['debug', 'info'])  # Keep warnings and errors longer
        ])
        
        count = len(old_logs)
        old_logs.unlink()
        
        _logger.info(f"Cleaned up {count} old log entries")
        return count
    
    @api.model
    def get_instance_logs_summary(self, instance_id, hours=24):
        """Get log summary for an instance in the last N hours"""
        from datetime import timedelta
        
        since = fields.Datetime.now() - timedelta(hours=hours)
        
        logs = self.search([
            ('instance_id', '=', instance_id),
            ('timestamp', '>=', since)
        ])
        
        summary = {
            'total': len(logs),
            'by_level': {},
            'recent_errors': [],
            'last_activity': None,
        }
        
        # Count by level
        for level in ['debug', 'info', 'warning', 'error', 'critical']:
            summary['by_level'][level] = len(logs.filtered(lambda l: l.level == level))
        
        # Get recent errors
        error_logs = logs.filtered(lambda l: l.level in ['error', 'critical'])
        summary['recent_errors'] = [{
            'timestamp': log.timestamp,
            'level': log.level,
            'message': log.message,
            'operation': log.operation,
        } for log in error_logs.sorted('timestamp', reverse=True)[:5]]
        
        # Last activity
        if logs:
            summary['last_activity'] = max(logs.mapped('timestamp'))
        
        return summary
    
    @api.model
    def export_logs(self, instance_id, start_date=None, end_date=None, levels=None):
        """Export logs for an instance"""
        domain = [('instance_id', '=', instance_id)]
        
        if start_date:
            domain.append(('timestamp', '>=', start_date))
        if end_date:
            domain.append(('timestamp', '<=', end_date))
        if levels:
            domain.append(('level', 'in', levels))
        
        logs = self.search(domain, order='timestamp asc')
        
        # Format for export
        export_data = []
        for log in logs:
            export_data.append({
                'timestamp': log.timestamp.isoformat() if log.timestamp else '',
                'level': log.level,
                'message': log.message,
                'details': log.details or '',
                'operation': log.operation or '',
                'component': log.component or '',
                'user': log.user_id.name if log.user_id else '',
                'exception_type': log.exception_type or '',
            })
        
        return export_data
    
    @api.model
    def search_logs(self, instance_id, search_term, levels=None, limit=100):
        """Search logs by message content"""
        domain = [
            ('instance_id', '=', instance_id),
            '|',
            ('message', 'ilike', search_term),
            ('details', 'ilike', search_term)
        ]
        
        if levels:
            domain.append(('level', 'in', levels))
        
        return self.search(domain, limit=limit, order='timestamp desc')
    
    def get_context_logs(self, minutes_before=5, minutes_after=5):
        """Get logs around this log entry for context"""
        from datetime import timedelta
        
        self.ensure_one()
        
        start_time = self.timestamp - timedelta(minutes=minutes_before)
        end_time = self.timestamp + timedelta(minutes=minutes_after)
        
        return self.search([
            ('instance_id', '=', self.instance_id.id),
            ('timestamp', '>=', start_time),
            ('timestamp', '<=', end_time),
        ], order='timestamp asc')
    
    @api.model
    def get_error_patterns(self, instance_id=None, days=7):
        """Analyze error patterns"""
        from datetime import timedelta
        from collections import Counter
        
        domain = [
            ('level', 'in', ['error', 'critical']),
            ('timestamp', '>=', fields.Datetime.now() - timedelta(days=days))
        ]
        
        if instance_id:
            domain.append(('instance_id', '=', instance_id))
        
        error_logs = self.search(domain)
        
        # Analyze patterns
        patterns = {
            'most_common_errors': Counter(),
            'errors_by_operation': Counter(),
            'errors_by_component': Counter(),
            'errors_by_hour': Counter(),
        }
        
        for log in error_logs:
            # Extract error type from message
            error_type = log.exception_type or log.message.split(':')[0] if ':' in log.message else log.message[:50]
            patterns['most_common_errors'][error_type] += 1
            
            if log.operation:
                patterns['errors_by_operation'][log.operation] += 1
            
            if log.component:
                patterns['errors_by_component'][log.component] += 1
            
            # Hour of day
            hour = log.timestamp.hour
            patterns['errors_by_hour'][hour] += 1
        
        # Convert to lists for easier handling
        result = {}
        for key, counter in patterns.items():
            result[key] = counter.most_common(10)
        
        return result

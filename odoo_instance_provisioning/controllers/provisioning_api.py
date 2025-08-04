# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

# Optional imports
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

_logger = logging.getLogger(__name__)


class ProvisioningAPIController(http.Controller):
    """API Controller for Instance Provisioning"""
    
    @http.route('/api/provisioning/create_instance', type='json', auth='public', 
                methods=['POST'], csrf=False, cors='*')
    def create_instance(self, **kwargs):
        """
        API endpoint to create a new instance
        Expected payload:
        {
            "customer_email": "admin@company.com",
            "customer_name": "John Doe",
            "customer_phone": "0123456789",
            "company_name": "My Company",
            "plan_id": 1,
            "subdomain": "mycompany",
            "admin_email": "admin@company.com",
            "admin_password": "secure_password" (optional),
            "priority": "normal" (optional)
        }
        """
        try:
            # Validate required fields
            required_fields = ['customer_email', 'customer_name', 'company_name', 
                             'plan_id', 'subdomain']
            missing_fields = [field for field in required_fields if not kwargs.get(field)]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'error_code': 'MISSING_FIELDS'
                }
            
            # Create instance request
            InstanceRequest = request.env['saas.instance.request'].sudo()
            instance_request = InstanceRequest.create_from_portal_data(kwargs)
            
            return {
                'success': True,
                'request_id': instance_request.request_id,
                'message': 'Instance request created successfully',
                'data': {
                    'request_id': instance_request.request_id,
                    'state': instance_request.state,
                    'subdomain': instance_request.subdomain,
                    'estimated_time': instance_request.estimated_processing_time,
                }
            }
            
        except ValidationError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
        except Exception as e:
            _logger.error(f"API Error in create_instance: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/request_status/<string:request_id>', 
                type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_request_status(self, request_id, **kwargs):
        """Get status of an instance request"""
        try:
            InstanceRequest = request.env['saas.instance.request'].sudo()
            instance_request = InstanceRequest.search([('request_id', '=', request_id)], limit=1)
            
            if not instance_request:
                return {
                    'success': False,
                    'error': 'Request not found',
                    'error_code': 'REQUEST_NOT_FOUND'
                }
            
            response_data = instance_request.get_request_summary()
            
            return {
                'success': True,
                'data': response_data
            }
            
        except Exception as e:
            _logger.error(f"API Error in get_request_status: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/instance_info/<string:subdomain>', 
                type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_instance_info(self, subdomain, **kwargs):
        """Get information about an instance by subdomain"""
        try:
            Instance = request.env['saas.instance.provisioning'].sudo()
            instance = Instance.search([('subdomain', '=', subdomain)], limit=1)
            
            if not instance:
                return {
                    'success': False,
                    'error': 'Instance not found',
                    'error_code': 'INSTANCE_NOT_FOUND'
                }
            
            return {
                'success': True,
                'data': {
                    'name': instance.name,
                    'subdomain': instance.subdomain,
                    'url': instance.url,
                    'state': instance.state,
                    'plan_name': instance.plan_id.name,
                    'company_name': instance.company_name,
                    'provisioned_date': instance.provisioned_date.isoformat() if instance.provisioned_date else None,
                    'last_activity': instance.last_activity.isoformat() if instance.last_activity else None,
                    'cpu_usage': instance.cpu_usage,
                    'memory_usage': instance.memory_usage,
                    'storage_usage': instance.storage_usage,
                }
            }
            
        except Exception as e:
            _logger.error(f"API Error in get_instance_info: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/instance_logs/<string:subdomain>', 
                type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_instance_logs(self, subdomain, **kwargs):
        """Get logs for an instance"""
        try:
            Instance = request.env['saas.instance.provisioning'].sudo()
            instance = Instance.search([('subdomain', '=', subdomain)], limit=1)
            
            if not instance:
                return {
                    'success': False,
                    'error': 'Instance not found',
                    'error_code': 'INSTANCE_NOT_FOUND'
                }
            
            # Get query parameters
            hours = int(kwargs.get('hours', 24))
            levels = kwargs.get('levels', '').split(',') if kwargs.get('levels') else None
            limit = int(kwargs.get('limit', 50))
            
            # Get logs
            InstanceLog = request.env['saas.instance.provisioning.log'].sudo()
            from datetime import timedelta
            from odoo import fields
            
            domain = [
                ('instance_id', '=', instance.id),
                ('timestamp', '>=', fields.Datetime.now() - timedelta(hours=hours))
            ]
            
            if levels:
                domain.append(('level', 'in', levels))
            
            logs = InstanceLog.search(domain, limit=limit, order='timestamp desc')
            
            log_data = []
            for log in logs:
                log_data.append({
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'level': log.level,
                    'message': log.message,
                    'operation': log.operation,
                    'component': log.component,
                })
            
            return {
                'success': True,
                'data': {
                    'logs': log_data,
                    'total_count': len(logs),
                    'summary': InstanceLog.get_instance_logs_summary(instance.id, hours)
                }
            }
            
        except Exception as e:
            _logger.error(f"API Error in get_instance_logs: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/manage_instance/<string:subdomain>', 
                type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def manage_instance(self, subdomain, **kwargs):
        """Manage instance (start, stop, restart, backup)"""
        try:
            Instance = request.env['saas.instance.provisioning'].sudo()
            instance = Instance.search([('subdomain', '=', subdomain)], limit=1)
            
            if not instance:
                return {
                    'success': False,
                    'error': 'Instance not found',
                    'error_code': 'INSTANCE_NOT_FOUND'
                }
            
            action = kwargs.get('action')
            if not action:
                return {
                    'success': False,
                    'error': 'Action is required',
                    'error_code': 'MISSING_ACTION'
                }
            
            # Perform action
            if action == 'start':
                instance.action_start()
                message = 'Instance started successfully'
            elif action == 'stop':
                instance.action_stop()
                message = 'Instance stopped successfully'
            elif action == 'restart':
                instance.action_stop()
                instance.action_start()
                message = 'Instance restarted successfully'
            elif action == 'backup':
                instance.action_backup()
                message = 'Backup created successfully'
            elif action == 'terminate':
                instance.action_terminate()
                message = 'Instance terminated successfully'
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'error_code': 'UNKNOWN_ACTION'
                }
            
            return {
                'success': True,
                'message': message,
                'data': {
                    'subdomain': instance.subdomain,
                    'state': instance.state,
                }
            }
            
        except UserError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'USER_ERROR'
            }
        except Exception as e:
            _logger.error(f"API Error in manage_instance: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/validate_subdomain', 
                type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def validate_subdomain(self, **kwargs):
        """Validate if subdomain is available"""
        try:
            subdomain = kwargs.get('subdomain')
            if not subdomain:
                return {
                    'success': False,
                    'error': 'Subdomain is required',
                    'error_code': 'MISSING_SUBDOMAIN'
                }
            
            # Check format
            import re
            if not re.match(r'^[a-z0-9-]+$', subdomain):
                return {
                    'success': False,
                    'available': False,
                    'error': 'Subdomain can only contain lowercase letters, numbers, and hyphens',
                    'error_code': 'INVALID_FORMAT'
                }
            
            # Check length
            if len(subdomain) < 3 or len(subdomain) > 63:
                return {
                    'success': False,
                    'available': False,
                    'error': 'Subdomain must be between 3 and 63 characters long',
                    'error_code': 'INVALID_LENGTH'
                }
            
            # Check availability
            Instance = request.env['saas.instance'].sudo()
            existing = Instance.search([
                ('subdomain', '=', subdomain),
                ('state', '!=', 'terminated')
            ], limit=1)
            
            available = not bool(existing)
            
            return {
                'success': True,
                'available': available,
                'subdomain': subdomain,
                'message': 'Subdomain is available' if available else 'Subdomain is already taken'
            }
            
        except Exception as e:
            _logger.error(f"API Error in validate_subdomain: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/plans', 
                type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_available_plans(self, **kwargs):
        """Get list of available service plans"""
        try:
            Plan = request.env['saas.plan'].sudo()
            plans = Plan.search([('active', '=', True)])
            
            plan_data = []
            for plan in plans:
                plan_data.append({
                    'id': plan.id,
                    'name': plan.name,
                    'description': plan.description,
                    'price': float(plan.price) if hasattr(plan, 'price') else 0.0,
                    'currency': plan.currency.name if hasattr(plan, 'currency') and plan.currency else 'USD',
                    'max_users': plan.max_users if hasattr(plan, 'max_users') else 0,
                    'storage_limit': plan.storage_limit if hasattr(plan, 'storage_limit') else 0,
                    'features': [module.name for module in plan.included_module_ids] if plan.included_module_ids else [],
                })
            
            return {
                'success': True,
                'data': plan_data
            }
            
        except Exception as e:
            _logger.error(f"API Error in get_available_plans: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @http.route('/api/provisioning/health', 
                type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def health_check(self, **kwargs):
        """Health check endpoint"""
        try:
            return {
                'success': True,
                'status': 'healthy',
                'timestamp': fields.Datetime.now().isoformat(),
                'version': '17.0.1.0.0'
            }
        except Exception as e:
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }

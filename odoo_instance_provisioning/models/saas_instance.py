# -*- coding: utf-8 -*-

import logging
import subprocess
import os
import xmlrpc.client
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import psycopg2
import time
import requests

# Optional imports
try:
    import docker
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False
    docker = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

_logger = logging.getLogger(__name__)


class SaasInstanceProvisioning(models.Model):
    _name = 'saas.instance.provisioning'
    _description = 'SaaS Instance Provisioning'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'subdomain'

    # Basic Information
    name = fields.Char('Instance Name', required=True)
    subdomain = fields.Char('Sub-domain', required=True, 
                           help='Sub-domain for accessing the instance (e.g., companya)')
    database_name = fields.Char('Database Name', required=True)
    plan_id = fields.Many2one('saas.plan', 'Service Plan', required=True)
    
    # Instance Configuration
    url = fields.Char('Instance URL', compute='_compute_url', store=True)
    odoo_version = fields.Char('Odoo Version', default='17.0')
    admin_email = fields.Char('Admin Email', required=True)
    admin_password = fields.Char('Admin Password')
    company_name = fields.Char('Company Name', required=True)
    
    # Status and Lifecycle
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)
    
    # Technical Details
    container_id = fields.Char('Container ID')
    port = fields.Integer('Port')
    ip_address = fields.Char('IP Address')
    ssl_enabled = fields.Boolean('SSL Enabled', default=True)
    
    # Resource Limits
    cpu_limit = fields.Float('CPU Limit (cores)', default=1.0)
    memory_limit = fields.Integer('Memory Limit (MB)', default=1024)
    storage_limit = fields.Integer('Storage Limit (GB)', default=10)
    
    # Usage Statistics
    cpu_usage = fields.Float('CPU Usage (%)')
    memory_usage = fields.Float('Memory Usage (%)')
    storage_usage = fields.Float('Storage Usage (%)')
    last_activity = fields.Datetime('Last Activity')
    
    # Backup and Maintenance
    backup_enabled = fields.Boolean('Backup Enabled', default=True)
    backup_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Backup Frequency', default='daily')
    last_backup = fields.Datetime('Last Backup')
    next_backup = fields.Datetime('Next Backup', compute='_compute_next_backup')
    
    # Relationships
    customer_id = fields.Many2one('saas.customer', 'Customer')
    instance_request_id = fields.Many2one('saas.instance.request', 'Instance Request')
    log_ids = fields.One2many('saas.instance.provisioning.log', 'instance_id', 'Logs')
    
    # Dates
    provisioned_date = fields.Datetime('Provisioned Date')
    expiry_date = fields.Datetime('Expiry Date')
    
    @api.depends('subdomain')
    def _compute_url(self):
        """Compute the full URL for the instance"""
        base_domain = self.env['ir.config_parameter'].sudo().get_param(
            'saas.base_domain', 'odoo.saas.com')
        for record in self:
            if record.subdomain:
                protocol = 'https' if record.ssl_enabled else 'http'
                record.url = f"{protocol}://{record.subdomain}.{base_domain}"
            else:
                record.url = False
    
    @api.depends('backup_frequency', 'last_backup')
    def _compute_next_backup(self):
        """Compute next backup date based on frequency"""
        for record in self:
            if record.last_backup and record.backup_frequency:
                if record.backup_frequency == 'daily':
                    record.next_backup = record.last_backup + timedelta(days=1)
                elif record.backup_frequency == 'weekly':
                    record.next_backup = record.last_backup + timedelta(weeks=1)
                elif record.backup_frequency == 'monthly':
                    record.next_backup = record.last_backup + timedelta(days=30)
            else:
                record.next_backup = False
    
    @api.constrains('subdomain')
    def _check_subdomain_unique(self):
        """Ensure subdomain is unique"""
        for record in self:
            if record.subdomain:
                existing = self.search([
                    ('subdomain', '=', record.subdomain),
                    ('id', '!=', record.id),
                    ('state', '!=', 'terminated')
                ])
                if existing:
                    raise ValidationError(_('Subdomain "%s" is already in use.') % record.subdomain)
    
    @api.constrains('database_name')
    def _check_database_name_unique(self):
        """Ensure database name is unique"""
        for record in self:
            if record.database_name:
                existing = self.search([
                    ('database_name', '=', record.database_name),
                    ('id', '!=', record.id),
                    ('state', '!=', 'terminated')
                ])
                if existing:
                    raise ValidationError(_('Database name "%s" is already in use.') % record.database_name)
    
    @api.model
    def create(self, vals):
        """Override create to set default values"""
        if not vals.get('database_name') and vals.get('subdomain'):
            vals['database_name'] = vals['subdomain'].replace('-', '_').replace('.', '_')
        
        # Set port if not provided
        if not vals.get('port'):
            vals['port'] = self._get_available_port()
        
        return super().create(vals)
    
    def _get_available_port(self):
        """Get next available port for instance"""
        # Simple implementation - in production, use better port management
        last_instance = self.search([], order='port desc', limit=1)
        if last_instance and last_instance.port:
            return last_instance.port + 1
        else:
            return 8070  # Start from 8070
        # return 8069 
    
    def action_provision(self):
        """Start the provisioning process"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft instances can be provisioned.'))
            
            record.state = 'provisioning'
            record._create_log('info', 'Starting provisioning process')
            
            try:
                # Start provisioning in background
                self.env.ref('odoo_instance_provisioning.ir_cron_provision_instances').sudo().method_direct_trigger()
                record._create_log('info', 'Provisioning job queued successfully')
            except Exception as e:
                record.state = 'error'
                record._create_log('error', f'Failed to queue provisioning job: {str(e)}')
                raise UserError(_('Failed to start provisioning: %s') % str(e))
    
    def action_start(self):
        """Start the instance"""
        for record in self:
            if record.state not in ['suspended', 'active']:
                raise UserError(_('Only suspended or active instances can be started.'))
            
            try:
                record._start_container()
                record.state = 'active'
                record._create_log('info', 'Instance started successfully')
            except Exception as e:
                record._create_log('error', f'Failed to start instance: {str(e)}')
                raise UserError(_('Failed to start instance: %s') % str(e))
    
    def action_stop(self):
        """Stop the instance"""
        for record in self:
            if record.state != 'active':
                raise UserError(_('Only active instances can be stopped.'))
            
            try:
                record._stop_container()
                record.state = 'suspended'
                record._create_log('info', 'Instance stopped successfully')
            except Exception as e:
                record._create_log('error', f'Failed to stop instance: {str(e)}')
                raise UserError(_('Failed to stop instance: %s') % str(e))
    
    def action_terminate(self):
        """Terminate the instance"""
        for record in self:
            if record.state == 'terminated':
                raise UserError(_('Instance is already terminated.'))
            
            try:
                record._terminate_instance()
                record.state = 'terminated'
                record._create_log('info', 'Instance terminated successfully')
            except Exception as e:
                record._create_log('error', f'Failed to terminate instance: {str(e)}')
                raise UserError(_('Failed to terminate instance: %s') % str(e))
    
    def action_backup(self):
        """Create backup of the instance"""
        for record in self:
            if record.state != 'active':
                raise UserError(_('Only active instances can be backed up.'))
            
            try:
                record._create_backup()
                record.last_backup = fields.Datetime.now()
                record._create_log('info', 'Backup created successfully')
            except Exception as e:
                record._create_log('error', f'Failed to create backup: {str(e)}')
                raise UserError(_('Failed to create backup: %s') % str(e))
    
    def _provision_instance(self):
        """Main provisioning logic"""
        try:
            self._create_log('info', 'Checking PostgreSQL connection')
            self._check_postgres_connection()
            
            self._create_log('info', 'Starting database creation')
            self._create_database()
            
            self._create_log('info', 'Starting container deployment')
            self._deploy_container()
            
            self._create_log('info', 'Installing modules')
            self._install_modules()
            
            self._create_log('info', 'Setting up admin user')
            self._setup_admin_user()
            
            self._create_log('info', 'Configuring company')
            self._setup_company()
            
            self._create_log('info', 'Configuring subdomain')
            self._setup_subdomain()
            
            # self._create_log('info', 'Setting up localization')
            # self._setup_localization()
            
            self.state = 'active'
            self.provisioned_date = fields.Datetime.now()
            self._create_log('info', 'Provisioning completed successfully')
            
            # Notify customer management module
            self._notify_customer_management()
            
        except Exception as e:
            self.state = 'error'
            self._create_log('error', f'Provisioning failed: {str(e)}')
            _logger.error(f"Provisioning failed for instance {self.id}: {str(e)}")
            raise
    
    def _create_database(self):
        """Create PostgreSQL database for the instance"""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'scripts', 'create_instance.sh'
        )
        
        # Check if script exists
        if not os.path.exists(script_path):
            raise Exception(f"Script not found: {script_path}")
        
        # Get database configuration from Odoo
        from odoo import tools
        db_host = tools.config.get('db_host', 'localhost')
        db_port = tools.config.get('db_port', 5432)
        db_user = tools.config.get('db_user', 'odoo')
        db_password = tools.config.get('db_password', '')
        
        # Prepare environment with Odoo's database configuration
        env = os.environ.copy()
        env.update({
            'PGHOST': str(db_host),
            'PGPORT': str(db_port),
            'PGUSER': str(db_user),
        })
        
        if db_password:
            env['PGPASSWORD'] = str(db_password)
        
        cmd = [
            'bash', script_path,
            self.database_name,
            self.admin_email,
            self.admin_password,
            self.company_name
        ]
        
        self._create_log('info', f'Creating database {self.database_name} on {db_host}:{db_port}')
        self._create_log('info', f'Executing: {" ".join(cmd)}')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
            
            # Combine stdout and stderr for better error analysis
            full_output = (result.stdout or '') + (result.stderr or '')
            
            # First check if the output indicates database already exists (regardless of return code)
            if ("Database already exists" in full_output or 
                "already exists" in full_output or
                "using existing database" in full_output):
                # This is acceptable - database already exists, we can use it
                self._create_log('warning', f'Database {self.database_name} already exists, using existing database')
                if result.stdout:
                    self._create_log('info', f'Script output: {result.stdout}')
                # Don't raise exception, continue with existing database
                return
            
            # Check for actual errors if return code is not 0
            if result.returncode != 0:
                error_msg = full_output or "Unknown error occurred"
                
                # Check for specific error patterns and provide helpful messages
                if "connection to server" in error_msg and "Connection refused" in error_msg:
                    detailed_error = (f"PostgreSQL server is not accessible at {db_host}:{db_port}. "
                                    f"Please ensure PostgreSQL container is running and accessible. "
                                    f"Error details: {error_msg}")
                    self._create_log('error', detailed_error)
                    raise Exception(detailed_error)
                elif "command not found" in error_msg:
                    detailed_error = ("Required command not found. Please ensure PostgreSQL client tools are installed. "
                                    f"Error details: {error_msg}")
                    self._create_log('error', detailed_error)
                    raise Exception(detailed_error)
                elif "permission denied" in error_msg.lower():
                    detailed_error = ("Permission denied. Please check database user privileges. "
                                    f"Error details: {error_msg}")
                    self._create_log('error', detailed_error)
                    raise Exception(detailed_error)
                else:
                    detailed_error = f"Database creation failed: {error_msg}"
                    self._create_log('error', detailed_error)
                    raise Exception(detailed_error)
            else:
                # Log successful output
                if result.stdout:
                    self._create_log('info', f'Script output: {result.stdout}')
                
        except subprocess.TimeoutExpired:
            error_msg = "Database creation script timed out after 5 minutes"
            self._create_log('error', error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to execute database creation script: {str(e)}"
            self._create_log('error', error_msg)
            raise Exception(error_msg)
        
        self._create_log('info', f'Database {self.database_name} created successfully')

    def _deploy_container(self):
        """Deploy Docker container for the instance"""
        if not HAS_DOCKER:
            raise Exception("Docker library not available. Please install: pip install docker")

        try:
            # 🔎 Bước 1: Kiểm tra kết nối PostgreSQL trước
            conn = psycopg2.connect(
                dbname=self.database_name,
                user='odoo',                  # hoặc self.db_user nếu có
                password='odoo',              # hoặc self.db_password
                host='db',             # đổi từ localhost thành tên service container postgres
                port=5432
            )
            conn.close()
            self._create_log('info', f"✅ Database {self.database_name} is accessible")

            # 🐳 Bước 2: Khởi tạo Docker container
            client = docker.from_env()

            volume_name = f'odoo_data_{self.database_name}'
            try:
                # Tạo volume Docker (nếu chưa có)
                client.volumes.get(volume_name)
            except docker.errors.NotFound:
                client.volumes.create(name=volume_name)
            
            container_config = {
                'image': f'odoo:{self.odoo_version}',
                'name': f'odoo_{self.database_name}',
                'ports': {'8069/tcp': self.port},
                'environment': {
                    'HOST': 'db',               # Đây là tên host DB trong mạng Docker
                    'USER': 'odoo',
                    'PASSWORD': 'odoo',
                    'DATABASE': self.database_name,  # thêm biến để Odoo biết tên DB
                },
                'volumes': {
                    volume_name: {
                        'bind': '/var/lib/odoo',
                        'mode': 'rw'
                    }
                },
                'network': 'odoo17-tutorial_default',
                'detach': True,
                'restart_policy': {"Name": "unless-stopped"},
                'command': f"--db-filter=^{self.database_name}$",
            }

            container = client.containers.run(**container_config)
            self.container_id = container.id
            self._create_log('info', f'✅ Container {container.id} deployed successfully')

        except psycopg2.OperationalError as db_err:
            self._create_log('error', f'❌ Cannot connect to database {self.database_name}: {str(db_err)}')
            raise Exception(f"Database connection failed: {str(db_err)}")

        except docker.errors.APIError as docker_err:
            self._create_log('error', f'❌ Docker error: {str(docker_err)}')
            raise Exception(f"Container deployment failed: {str(docker_err)}")

        except Exception as e:
            self._create_log('error', f'❌ Unexpected error: {str(e)}')
            raise Exception(f"Container deployment failed: {str(e)}")

    def _wait_for_odoo(self, timeout=90):
        """Wait until Odoo is up and responding on HTTP"""
        container_host = f"odoo_{self.database_name}"  # tên container bạn đặt khi tạo
        url = f"http://{container_host}:8069"
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    self._create_log('info', f"Odoo instance is up at {url}")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(3)

        raise Exception(f"Timed out waiting for Odoo at {url}")
    
    def _install_modules(self):
        """Install modules based on service plan"""
        if not self.plan_id.included_module_ids:
            return

        try:
            # Wait for Odoo to start
            self._wait_for_odoo(timeout=240)

            # RPC connection
            # url = f'http://localhost:{self.port}'
            container_host = f"odoo_{self.database_name}"  # tên container bạn đặt khi tạo
            url = f"http://{container_host}:8069"
            db = self.database_name
            username = 'admin'
            password = 'admin'

            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, username, password, {})

            if not uid:
                raise Exception("Authentication failed to instance")

            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

            # Build list of module names
            module_names = [
                module.technical_name.strip()
                for module in self.plan_id.included_module_ids
                if module.technical_name and module.technical_name.strip()
            ]

            if not module_names:
                self._create_log('warning', 'No valid module names to install')
                return

            # Search modules using 'in' operator — SAFELY
            module_ids = models.execute_kw(
                db, uid, password,
                'ir.module.module', 'search',
                [[('name', 'in', module_names)]]
            )

            if not module_ids:
                self._create_log('warning', f"No matching modules found in instance for: {module_names}")
                return

            # Install all at once
            models.execute_kw(
                db, uid, password,
                'ir.module.module', 'button_immediate_install',
                [module_ids]
            )
            self._create_log('info', f"Installed modules: {module_names}")

        except xmlrpc.client.Fault as fault:
            raise Exception(f"XML-RPC Fault: {fault.faultString}")
        except Exception as e:
            raise Exception(f"Module installation failed: {str(e)}")
    
    def _setup_admin_user(self):
        """Setup admin user for the instance"""
        try:
            container_host = f"odoo_{self.database_name}"  # tên container bạn đặt khi tạo
            url = f"http://{container_host}:8069"
            db = self.database_name
            username = 'admin'
            password = 'admin'
            
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, username, password, {})
            
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            
            # Update admin user
            models.execute_kw(
                db, uid, password,
                'res.users', 'write',
                [uid, {
                    'login': self.admin_email,
                    'email': self.admin_email,
                    'password': self.admin_password,
                }]
            )
            
            self._create_log('info', 'Admin user configured successfully')
            
        except Exception as e:
            raise Exception(f"Admin user setup failed: {str(e)}")
    
    def _setup_company(self):
        """Setup company information"""
        try:
            container_host = f"odoo_{self.database_name}"  # tên container bạn đặt khi tạo
            url = f"http://{container_host}:8069"
            db = self.database_name
            username = self.admin_email
            password = self.admin_password
            
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, username, password, {})
            
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            
            # Get company
            company_ids = models.execute_kw(
                db, uid, password,
                'res.company', 'search', [[]]
            )
            
            if company_ids:
                models.execute_kw(
                    db, uid, password,
                    'res.company', 'write',
                    [company_ids[0], {'name': self.company_name}]
                )
            
            self._create_log('info', 'Company information configured')
            
        except Exception as e:
            raise Exception(f"Company setup failed: {str(e)}")
    
    def _setup_subdomain(self):
        """Setup subdomain routing"""
        # This would typically involve:
        # 1. Updating Nginx/Apache configuration
        # 2. Updating DNS records
        # 3. Setting up SSL certificates
        
        # For now, just log the action
        self._create_log('info', f'Subdomain {self.subdomain} configured')
    
    def _setup_localization(self):
        """Setup localization modules"""
        # Install Vietnamese localization as default
        try:
            url = f'http://localhost:{self.port}'
            db = self.database_name
            username = self.admin_email
            password = self.admin_password
            
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, username, password, {})
            
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            
            # Install l10n_vn
            module_ids = models.execute_kw(
                db, uid, password,
                'ir.module.module', 'search',
                [['name', '=', 'l10n_vn']]
            )
            
            if module_ids:
                models.execute_kw(
                    db, uid, password,
                    'ir.module.module', 'button_immediate_install',
                    [module_ids]
                )
                self._create_log('info', 'Vietnamese localization installed')
            
        except Exception as e:
            self._create_log('warning', f'Localization setup failed: {str(e)}')
    
    def _notify_customer_management(self):
        """Notify customer management module about instance creation"""
        try:
            if self.customer_id:
                # Update customer instance status
                self.customer_id.write({
                    'instance_count': self.customer_id.instance_count + 1
                })
            
            self._create_log('info', 'Customer management notified')
            
        except Exception as e:
            self._create_log('warning', f'Customer notification failed: {str(e)}')
    
    def _start_container(self):
        """Start Docker container"""
        if not HAS_DOCKER:
            raise Exception("Docker library not available. Please install: pip install docker")
        
        try:
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            container.start()
        except Exception as e:
            raise Exception(f"Failed to start container: {str(e)}")
    
    def _stop_container(self):
        """Stop Docker container"""
        if not HAS_DOCKER:
            raise Exception("Docker library not available. Please install: pip install docker")
        
        try:
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            container.stop()
        except Exception as e:
            raise Exception(f"Failed to stop container: {str(e)}")
    
    def _terminate_instance(self):
        """Terminate instance completely"""
        if not HAS_DOCKER:
            raise Exception("Docker library not available. Please install: pip install docker")
        
        try:
            # Stop and remove container
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            container.stop()
            container.remove()
            
            # Drop database
            script_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'scripts', 'drop_database.sh'
            )
            
            cmd = ['bash', script_path, self.database_name]
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            raise Exception(f"Failed to terminate instance: {str(e)}")
    
    def _create_backup(self):
        """Create backup of instance"""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'scripts', 'backup_instance.sh'
        )
        
        cmd = ['bash', script_path, self.database_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Backup failed: {result.stderr}")
    
    def _create_log(self, level, message):
        """Create log entry for the instance"""
        self.env['saas.instance.provisioning.log'].create({
            'instance_id': self.id,
            'level': level,
            'message': message,
            'timestamp': fields.Datetime.now(),
        })
    
    @api.model
    def cron_provision_instances(self):
        """Cron job to provision pending instances"""
        instances = self.search([('state', '=', 'provisioning')])
        for instance in instances:
            try:
                instance._provision_instance()
            except Exception as e:
                _logger.error(f"Failed to provision instance {instance.id}: {str(e)}")
    
    @api.model
    def cron_backup_instances(self):
        """Cron job to backup instances"""
        instances = self.search([
            ('state', '=', 'active'),
            ('backup_enabled', '=', True),
            ('next_backup', '<=', fields.Datetime.now())
        ])
        
        for instance in instances:
            try:
                instance.action_backup()
            except Exception as e:
                _logger.error(f"Failed to backup instance {instance.id}: {str(e)}")
    
    @api.model
    def cron_monitor_instances(self):
        """Cron job to monitor instance health"""
        instances = self.search([('state', '=', 'active')])
        for instance in instances:
            try:
                instance._update_resource_usage()
            except Exception as e:
                _logger.error(f"Failed to monitor instance {instance.id}: {str(e)}")
    
    def _update_resource_usage(self):
        """Update resource usage statistics"""
        if not HAS_DOCKER:
            self._create_log('warning', 'Docker library not available for resource monitoring')
            return
        
        try:
            client = docker.from_env()
            container = client.containers.get(self.container_id)
            
            # Get container stats
            stats = container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0:
                self.cpu_usage = (cpu_delta / system_delta) * 100.0
            
            # Calculate memory usage
            if 'usage' in stats['memory_stats']:
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                self.memory_usage = (memory_usage / memory_limit) * 100.0
            
            self.last_activity = fields.Datetime.now()
            
        except Exception as e:
            self._create_log('error', f'Failed to update resource usage: {str(e)}')
    
    def action_view_logs(self):
        """Action to view logs for this instance"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Logs for {self.name}',
            'res_model': 'saas.instance.provisioning.log',
            'view_mode': 'tree,form',
            'domain': [('instance_id', '=', self.id)],
            'context': {'default_instance_id': self.id},
            'target': 'current',
        }
    
    def _check_postgres_connection(self):
        """Check PostgreSQL connection before provisioning"""
        try:
            # Get database configuration from Odoo's config
            from odoo import tools
            db_host = tools.config.get('db_host', 'localhost')
            db_port = tools.config.get('db_port', 5432)
            db_user = tools.config.get('db_user', 'odoo')
            db_password = tools.config.get('db_password', False)
            
            self._create_log('info', f'Checking PostgreSQL connection to {db_host}:{db_port}')
            
            # Try to connect using psycopg2 directly
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    user=db_user,
                    password=db_password or '',
                    database='postgres'  # Connect to default database
                )
                conn.close()
                self._create_log('info', 'PostgreSQL connection successful')
                return True
                
            except ImportError:
                # Fallback to using script with proper environment variables
                self._create_log('info', 'Using script method for PostgreSQL check')
                return self._check_postgres_with_script(db_host, db_port, db_user, db_password)
            except Exception as e:
                self._create_log('error', f'PostgreSQL connection failed: {str(e)}')
                raise Exception(f"Cannot connect to PostgreSQL at {db_host}:{db_port}. Error: {str(e)}")
                
        except Exception as e:
            error_msg = f"Failed to run PostgreSQL connection check: {str(e)}"
            self._create_log('error', error_msg)
            raise Exception(error_msg)
    
    def _check_postgres_with_script(self, db_host, db_port, db_user, db_password):
        """Fallback method using script with proper environment"""
        check_script_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'scripts', 'check_postgres.sh'
        )
        
        if not os.path.exists(check_script_path):
            self._create_log('warning', 'PostgreSQL check script not found, skipping connection check')
            return True
        
        # Prepare environment with Odoo's database configuration
        env = os.environ.copy()
        env.update({
            'PGHOST': str(db_host),
            'PGPORT': str(db_port),
            'PGUSER': str(db_user),
        })
        
        if db_password:
            env['PGPASSWORD'] = str(db_password)
        
        cmd = ['bash', check_script_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "PostgreSQL connection check failed"
                self._create_log('error', f'PostgreSQL check failed: {error_msg}')
                return False
            
            self._create_log('info', 'PostgreSQL connection check passed')
            return True
            
        except subprocess.TimeoutExpired:
            error_msg = "PostgreSQL connection check timed out"
            self._create_log('error', error_msg)
            return False
        except Exception as e:
            error_msg = f"Failed to run PostgreSQL connection check: {str(e)}"
            self._create_log('error', error_msg)
            return False

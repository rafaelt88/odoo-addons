# -*- coding: utf-8 -*-
{
    'name': 'Odoo Instance Provisioning',
    'version': '17.0.1.0.0',
    'category': 'SaaS',
    'summary': 'Module tự động hóa việc tạo và quản lý các instance Odoo độc lập cho từng khách hàng',
    'description': '''
    Module tự động hóa phức tạp để:
    - Nhận yêu cầu từ module "Cổng Đăng ký"
    - Tự động khởi tạo database Odoo mới
    - Cài đặt module theo gói dịch vụ
    - Thiết lập người dùng quản trị và thông tin công ty
    - Cấu hình sub-domain
    - Thiết lập bản địa hóa và tùy chỉnh mặc định
    - Sao lưu và giám sát sức khỏe instance
    ''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'web',
        'mail',
        'saas_plan_management',
        'saas_customer_management',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/cron_data.xml',
        
        # Views
        'views/saas_instance_log_views.xml',
        'views/saas_instance_request_views.xml',
        'views/saas_instance_views.xml',
        'views/provisioning_settings_views.xml',
        'views/provisioning_menus.xml',
    ],
    'external_dependencies': {
        'python': [
            'requests',
            'psycopg2',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

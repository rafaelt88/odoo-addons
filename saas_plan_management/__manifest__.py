{
    'name': 'SaaS Plan Management',
    'version': '17.0.1.0.0',
    'category': 'SaaS/Management',
    'summary': 'Quản lý Gói dịch vụ SaaS - Định nghĩa các gói dịch vụ, module Odoo, giới hạn và pricing',
    'description': """
SaaS Plan Management Module
===========================

Module quản lý các gói dịch vụ SaaS bao gồm:

**Tính năng chính:**
* Định nghĩa các gói dịch vụ (Basic, Standard, Premium)
* Quản lý module Odoo được bao gồm trong mỗi gói
* Thiết lập giới hạn người dùng, dung lượng, giao dịch
* Cấu hình chu kỳ thanh toán (tháng, quý, năm)
* Quản lý Add-on và tùy chỉnh riêng lẻ
* Hệ thống pricing linh hoạt

**Chức năng:**
* Tạo/Chỉnh sửa/Xóa gói dịch vụ
* Gán module Odoo cho từng gói
* Cập nhật giá và giới hạn
* Template gói dịch vụ mẫu
* Báo cáo và phân tích gói dịch vụ

**Tích hợp:**
* Liên kết với SaaS Customer Management
* Hỗ trợ multi-currency
* API endpoints cho external integration
    """,
    'author': 'SaaS Development Team',
    'website': 'https://saas-platform.com',
    'license': 'LGPL-3',    
    'depends': [
        'base',
        'web',
        'mail',
        'portal',
        'saas_customer_management',
    ],
    'data': [
        # Security
        'security/saas_plan_groups.xml',
        'security/ir.model.access.csv',
        # Data
        'data/odoo_module_data.xml',
        'data/plan_template_data.xml',
        # Views
        'views/saas_plan_views.xml',
        'views/odoo_module_views.xml',
        'views/plan_addon_views.xml',
        'views/plan_template_views.xml',
        'views/saas_plan_menus.xml',  # Load menus last after all actions
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 101,
}

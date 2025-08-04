{
    "name": "SaaS Website Plans",
    "version": "17.0.1.0.0",
    "category": "Website/SaaS",
    "summary": "Website interface để hiển thị các gói SaaS Plans cho khách hàng đăng ký",
    "description": """
SaaS Website Plans
==================

Module website hiển thị các gói SaaS Plans cho khách hàng:

**Tính năng chính:**
* Trang website hiển thị tất cả gói SaaS Plans
* Giao diện responsive, hiện đại cho mobile/desktop
* So sánh chi tiết các tính năng của từng gói
* Hỗ trợ nhiều chu kỳ thanh toán (tháng/quý/năm)
* Form đăng ký dịch vụ và tạo lead
* Tích hợp với CRM để quản lý khách hàng tiềm năng

**Tích hợp:**
* Lấy dữ liệu từ module saas_plan_management
* Tạo leads trong CRM khi khách hàng đăng ký
* Menu website "SaaS Plans" tự động
* SEO-friendly với meta tags
    """,
    "author": "SaaS Development Team",
    "website": "https://saas-platform.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "website",
        "portal",
        "crm",
        "saas_plan_management",  # Dependency chính để lấy dữ liệu plans
        "saas_customer_management",  # Dependency để tạo customer records
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/website_menu_data.xml",
        "views/saas_plans_templates.xml",
        "views/checkout_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "saas_website_plans/static/src/css/saas_plans.css",
            "saas_website_plans/static/src/js/saas_plans.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "auto_install": False,
    "application": False,
    "sequence": 102,
}

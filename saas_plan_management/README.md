# SaaS Plan Management Module

## Mô tả

Module **SaaS Plan Management** (Quản lý Gói dịch vụ SaaS) được thiết kế để quản lý toàn diện các gói dịch vụ SaaS mà doanh nghiệp cung cấp. Module này tích hợp chặt chẽ với module `saas_customer_management` để tạo ra một hệ thống quản lý SaaS hoàn chỉnh.

## Tính năng chính

### 1. Quản lý Gói dịch vụ (SaaS Plans)

- **Định nghĩa các gói dịch vụ**: Basic, Standard, Premium, Enterprise
- **Cấu hình giá cả**: Theo tháng, quý, năm với flexibility pricing
- **Thiết lập giới hạn**: Người dùng, dung lượng, giao dịch, API calls
- **Tích hợp đa tiền tệ**: Hỗ trợ multi-currency
- **Chu kỳ thanh toán**: Monthly, Quarterly, Yearly, Custom

### 2. Quản lý Module Odoo

- **Catalog các module**: Danh mục đầy đủ các module Odoo
- **Phân loại module**: Core, Standard, Community, Enterprise
- **Gán module cho plan**: Linh hoạt assign modules cho từng plan
- **Dependency management**: Quản lý dependencies giữa các modules

### 3. Quản lý Add-ons

- **Add-on pricing**: Giá cả riêng biệt cho từng add-on
- **Dependencies**: Quản lý dependencies và conflicts
- **Bulk assignment**: Gán hàng loạt add-ons cho plans

### 4. Plan Templates

- **Template system**: Tạo templates cho các loại plans phổ biến
- **Quick setup**: Nhanh chóng tạo plans từ templates
- **Customization**: Dễ dàng customize templates theo nhu cầu

## Cấu trúc Module

```
saas_plan_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── saas_plan.py           # Model chính cho SaaS plans
│   ├── odoo_module.py         # Catalog các module Odoo
│   ├── plan_addon.py          # Quản lý add-ons
│   └── plan_template.py       # Templates cho plans
├── views/
│   ├── saas_plan_views.xml
│   ├── odoo_module_views.xml
│   ├── plan_addon_views.xml
│   ├── plan_template_views.xml
│   └── saas_plan_menus.xml
├── security/
│   ├── saas_plan_groups.xml   # User groups
│   └── ir.model.access.csv    # Access rights
├── data/
│   ├── odoo_module_data.xml   # Default Odoo modules
│   ├── plan_template_data.xml # Plan templates
│   └── demo_data.xml          # Demo plans và add-ons
└── static/
    ├── description/
    │   └── banner.png
    └── src/css/
        └── saas_plan.css
```

## Models

### 1. saas.plan

Model chính quản lý các gói dịch vụ SaaS.

**Key Fields:**

- `name`: Tên gói dịch vụ
- `code`: Mã gói dịch vụ
- `plan_type`: Loại gói (free, basic, standard, premium, enterprise)
- `monthly_price`, `quarterly_price`, `yearly_price`: Giá theo chu kỳ
- `max_users`: Giới hạn người dùng
- `storage_limit_gb`: Giới hạn dung lượng
- `transaction_limit_monthly`: Giới hạn giao dịch
- `included_module_ids`: Các module được bao gồm
- `addon_ids`: Các add-ons khả dụng

### 2. saas.odoo.module

Catalog các module Odoo khả dụng.

**Key Fields:**

- `name`: Tên module
- `technical_name`: Tên kỹ thuật
- `category`: Phân loại module
- `description`: Mô tả chi tiết
- `is_core`: Module core hay không
- `dependency_ids`: Dependencies

### 3. saas.plan.addon

Quản lý các add-ons cho plans.

**Key Fields:**

- `name`: Tên add-on
- `addon_type`: Loại add-on
- `monthly_price`: Giá hàng tháng
- `description`: Mô tả
- `dependency_ids`, `conflict_ids`: Dependencies và conflicts

### 4. saas.plan.template

Templates để tạo nhanh các plans.

**Key Fields:**

- `name`: Tên template
- `plan_type`: Loại plan
- `default_modules`: Modules mặc định
- `default_limits`: Giới hạn mặc định

## Tích hợp với SaaS Customer Management

Module này tích hợp chặt chẽ với `saas_customer_management`:

1. **saas.instance** được thêm field `plan_id` để link với plan
2. **saas.customer** có computed fields để hiển thị plan information
3. **Views** được cập nhật để hiển thị plan information
4. **Backward compatibility** với `service_package_id` cũ

## Installation & Setup

### 1. Dependencies

```python
'depends': [
    'base',
    'web',
    'mail',
    'portal',
    'saas_customer_management',
]
```

### 2. Installation Steps

1. Copy module vào addons directory
2. Update apps list trong Odoo
3. Install module `saas_plan_management`
4. Module sẽ tự động load demo data và templates

### 3. Configuration

1. Truy cập **SaaS Management > SaaS Plans > Configuration**
2. Review và cập nhật **Odoo Modules** catalog
3. Tạo **Plans** theo nhu cầu doanh nghiệp
4. Setup **Add-ons** nếu cần thiết

## Usage

### Tạo Plan mới

1. Truy cập **SaaS Management > SaaS Plans > SaaS Plans**
2. Click **Create**
3. Điền thông tin cơ bản: Name, Code, Plan Type
4. Cấu hình pricing và limits
5. Assign Odoo modules
6. Thêm add-ons nếu cần
7. Save

### Sử dụng Template

1. Truy cập **SaaS Management > SaaS Plans > Plan Templates**
2. Chọn template phù hợp
3. Click **Create Plan from Template**
4. Customize theo nhu cầu

### Assign Plan cho Customer

1. Truy cập **SaaS Management > Customers**
2. Chọn customer
3. Tạo instance mới
4. Chọn plan trong form instance

## Customization

### Thêm Plan Type mới

```python
plan_type = fields.Selection([
    ('free', 'Free Trial'),
    ('basic', 'Basic'),
    ('standard', 'Standard'),
    ('premium', 'Premium'),
    ('enterprise', 'Enterprise'),
    ('custom', 'Custom'),
    ('your_new_type', 'Your New Type'),  # Thêm type mới
], ...)
```

### Thêm Limits mới

```python
# Trong model saas.plan
your_new_limit = fields.Integer(
    string='Your New Limit',
    default=100,
    help='Description of your new limit'
)
```

### Custom Pricing Logic

```python
@api.depends('plan_type', 'monthly_price', 'custom_factor')
def _compute_dynamic_price(self):
    for plan in self:
        # Your custom pricing logic here
        pass
```

## Troubleshooting

### Common Issues

1. **Module không load được**

   - Kiểm tra dependencies
   - Restart Odoo service
   - Update module list

2. **Data không hiển thị**

   - Kiểm tra access rights
   - Verify data files
   - Check domain filters

3. **Integration issues**
   - Verify `saas_customer_management` đã install
   - Check field mappings
   - Review computed fields

## Support & Development

Module được phát triển bởi SaaS Development Team với mục tiêu tạo ra một platform quản lý SaaS hoàn chỉnh và dễ sử dụng.

Để báo cáo bugs hoặc request features, vui lòng liên hệ development team.

## License

Module được phát hành dưới license LGPL-3, tương thích với Odoo Community Edition.

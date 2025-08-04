# Website Product Promotions Module

## Mô tả

Module `website_product_promotions` cung cấp các tính năng khuyến mãi toàn diện cho hệ thống eCommerce Odoo 17:

### Tính năng chính:

1. **Product Combos (Combo Sản phẩm)**
   - Tạo combo từ nhiều sản phẩm với giá ưu đãi
   - Tự động áp dụng chiết khấu khi khách hàng mua combo
   - Hiển thị combo trên website với giao diện đẹp

2. **Upsell & Cross-sell**
   - Gợi ý sản phẩm nâng cấp (Upsell)
   - Gợi ý sản phẩm đi kèm (Cross-sell)
   - Hiển thị trên trang chi tiết sản phẩm

3. **Tự động nhận diện combo trong giỏ hàng**
   - Khi khách hàng thêm từng sản phẩm lẻ mà trùng với combo
   - Hệ thống tự động áp dụng giảm giá combo

## Cấu trúc Module

```
website_product_promotions/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── product_combo.py       # Model chính cho combo
│   ├── product_template.py    # Extend sản phẩm
│   └── sale_order.py         # Logic giỏ hàng
├── controllers/
│   ├── __init__.py
│   └── combo_controller.py   # Controller xử lý combo
├── views/
│   ├── menu_views.xml        # Menu quản trị
│   ├── product_combo_views.xml
│   ├── product_template_views.xml
│   └── website_templates.xml # Template website
├── static/
│   └── src/
│       ├── js/
│       │   └── combo_add_to_cart.js
│       └── css/
│           └── promotions.css
└── security/
    └── ir.model.access.csv
```

## Cách sử dụng

### 1. Tạo Combo

1. Vào **Sales > Product Promotions > Product Combos**
2. Click **Create**
3. Nhập tên combo và giá combo
4. Thêm sản phẩm vào tab "Combo Products"
5. Save và publish trên website

### 2. Cấu hình Upsell/Cross-sell

1. Vào sản phẩm muốn cấu hình
2. Tab "Upsell / Cross-sell"
3. Chọn sản phẩm upsell và cross-sell
4. Save

### 3. Khách hàng sử dụng

- Xem combo tại `/shop/combos`
- Mua combo hoặc từng sản phẩm lẻ
- Hệ thống tự động áp dụng giảm giá

## Tính năng nâng cao

### Logic tự động nhận diện combo:
- Sau mỗi lần cập nhật giỏ hàng
- Hệ thống kiểm tra tất cả combo active
- Nếu giỏ hàng chứa đúng sản phẩm của combo → áp dụng chiết khấu

### Quản lý xung đột:
- Ưu tiên combo có nhiều sản phẩm trùng nhất
- Khi xóa sản phẩm khỏi combo → xóa chiết khấu tương ứng

## Cài đặt

1. Copy module vào thư mục addons
2. Update Apps List
3. Search "Website Product Promotions"
4. Install

## Dependencies

- website_sale
- sale_management  
- product

## Tác giả

- **Beemart**
- Website: https://beemart.vn

## License

LGPL-3

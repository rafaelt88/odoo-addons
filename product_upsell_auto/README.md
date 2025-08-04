# Product Upsell Auto

## Mô tả

Module `product_upsell_auto` tự động tạo các gợi ý sản phẩm upsell thông minh dựa trên dữ liệu hiện có trong Odoo eCommerce.

## Tính năng chính

### 🤖 Tự động hóa
- Tự động phân tích dữ liệu sản phẩm để tạo gợi ý upsell
- Cron job chạy hàng ngày để cập nhật recommendations
- Thuật toán thông minh dựa trên category và price

### 📊 Thuật toán gợi ý
- Tìm sản phẩm cùng category với giá cao hơn
- Ưu tiên sản phẩm có giá 1.2x - 3x sản phẩm gốc
- Tính điểm ưu tiên dựa trên tỷ lệ giá và rating
- Hiển thị top 5 recommendations tốt nhất

### 🎨 Giao diện đẹp
- Section "You might also like" trên product page
- Sidebar widget hiển thị compact recommendations
- Responsive design cho mobile
- Animation và hover effects

### ⚙️ Quản lý Backend
- Xem và chỉnh sửa recommendations trong product form
- Bulk generation cho tất cả sản phẩm
- Dashboard để quản lý recommendations
- Manual override cho specific products

## Cài đặt

1. **Copy module** vào thư mục addons
2. **Update Apps List:** Settings > Apps > Update Apps List
3. **Install module:** Search "Product Upsell Auto" > Install
4. **Generate recommendations:** Products > Generate All Upsell Recommendations

## Sử dụng

### Tự động (Khuyến nghị)
- Module sẽ tự động chạy cron job mỗi ngày lúc 2:00 AM
- Không cần can thiệp thủ công

### Thủ công
1. **Single Product:** Vào product form > Tab "Auto Recommendations" > Click "Generate Upsell"
2. **Bulk Generation:** Products > Action > Generate All Upsell Recommendations

### Xem kết quả
1. **Frontend:** Vào trang chi tiết sản phẩm bất kỳ
2. **Backend:** Product form > Tab "Auto Recommendations"

## Cấu hình

### Cron Job
- **Frequency:** Hàng ngày lúc 2:00 AM
- **Location:** Settings > Technical > Automation > Scheduled Actions
- **Name:** "Generate Product Upsell Recommendations"

### Thuật toán tuning
Có thể điều chỉnh trong `models/product_template.py`:
- `price_ratio` range (hiện tại: 1.2x - 3x)
- Number of recommendations (hiện tại: top 5)
- Scoring algorithm weights

## API

### Methods
```python
# Generate upsell for single product
product.action_generate_upsell()

# Generate upsell for all products
self.env['product.template'].action_generate_all_upsell()

# Get recommendations for frontend
product.get_upsell_recommendations(limit=3)
```

### JSON Endpoint
```
GET /shop/product/upsell/<int:product_id>
Parameters: limit (default: 4)
Returns: {'success': True, 'products': [...], 'count': 3}
```

## Cấu trúc Database

### Model: product.recommendation
- `source_product_id`: Sản phẩm gốc
- `recommended_product_id`: Sản phẩm được gợi ý
- `type`: 'upsell' hoặc 'crosssell'
- `score`: Điểm ưu tiên (cao = tốt hơn)
- `price_difference`: Chênh lệch giá
- `created_by_system`: True nếu tạo tự động

## Troubleshooting

### Không hiển thị recommendations
1. Check sản phẩm có `sale_ok = True`
2. Check `website_published = True`
3. Chạy manual generation: Product > Generate Upsell

### Cron job không chạy
1. Check Scheduled Actions đã active
2. Check user permissions
3. Check server logs

### Performance issues
1. Giảm frequency của cron job
2. Giảm số lượng recommendations per product
3. Add database indexes nếu cần

## Changelog

### v17.0.1.0.0
- Initial release
- Auto upsell generation based on category + price
- Frontend display templates
- Backend management interface
- Daily cron job
- JSON API endpoints

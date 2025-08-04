# -*- coding: utf-8 -*-
{
    "name": "Website Sale Product Promotions",
    "version": "17.0.1.0.0",
    "category": "Website/eCommerce",
    "summary": "Product Combos, Upsell & Cross-sell, Auto Recommendations for eCommerce",
    "description": """
        Hợp nhất tính năng của hai module:
        - website_product_promotions: Combo sản phẩm, upsell, cross-sell, khuyến mãi website
        - product_upsell_auto: Gợi ý upsell/cross-sell tự động, combo thông minh, recommendation
        
        Tính năng:
        - Tạo combo sản phẩm với giá ưu đãi, tự động áp dụng khi khách mua đủ combo
        - Gợi ý upsell/cross-sell thủ công và tự động dựa trên dữ liệu
        - Giao diện đẹp cho website, backend quản lý dễ dàng
        - Cron tự động cập nhật recommendation
        - Tăng giá trị đơn hàng trung bình, trải nghiệm khách hàng tốt hơn
    """,
    "author": "BeeSmartSolutions",
    "website": "https://beetech.one/",
    "depends": [
        "website_sale",
        "sale_management",
        "product"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_combo_views.xml",
        "views/product_template_views.xml",
        "views/website_templates.xml",
        "views/menu_views.xml",
        "views/product_views.xml",
        "views/recommendation_views.xml",
        "views/fbt_rule_views.xml",
        "views/website_fbt_templates.xml",
        "data/ir_cron.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "website_sale_product_promotions/static/src/css/combo_style.css",
            "website_sale_product_promotions/static/src/css/promotions.css",
            "website_sale_product_promotions/static/src/css/upsell_styles.css",
            "website_sale_product_promotions/static/src/css/upsell.css",
            "website_sale_product_promotions/static/src/css/fbt_styles.css",
            "website_sale_product_promotions/static/src/js/combo_cart.js",
            "website_sale_product_promotions/static/src/js/combo_add_to_cart.js",
            "website_sale_product_promotions/static/src/js/upsell_carousel.js",
            "website_sale_product_promotions/static/src/js/fbt_carousel.js",
        ]
    },
    'images': ['static/description/banner.png'],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}

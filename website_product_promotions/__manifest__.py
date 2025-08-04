# -*- coding: utf-8 -*-
{
    "name": "Website Product Promotions",
    "version": "17.0.1.0.1",
    "category": "Website/eCommerce",
    "summary": "Product Combos, Upsell & Cross-sell for eCommerce",
    "description": """
        This module provides comprehensive product promotion features for Odoo eCommerce:
        
        Features:
        - Product Combos with special pricing
        - Upsell and Cross-sell suggestions
        - Automatic combo detection in cart
        - Beautiful website display
        - Easy backend management
        
        Key Benefits:
        - Increase average order value
        - Better customer experience
        - Flexible combo pricing
        - Automatic discount application
        
        Bug Fixes (v17.0.1.0.1):
        - Fixed "Order Reference (order_id) field is mandatory" error
        - Improved error handling for combo cart operations
        - Enhanced stability for multiple combo scenarios
    """,
    "author": "Beemart",
    "website": "https://beemart.vn",
    "depends": [
        "website_sale",
        "sale_management",
        "product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_combo_views.xml",
        # 'views/product_template_views.xml',
        "views/website_templates.xml",
        "views/menu_views.xml",
        "data/combo_demo_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_product_promotions/static/src/js/combo_add_to_cart.js",
            "website_product_promotions/static/src/css/promotions.css",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}

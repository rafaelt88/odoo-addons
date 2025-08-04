{
    'name': 'Website Frequently Bought Together',
    'version': '17.0.1.0.0',
    'summary': 'Gợi ý sản phẩm thường mua cùng trên website',
    'description': 'Gợi ý sản phẩm Frequently Bought Together (FBT) dựa trên lịch sử đơn hàng và cho phép chỉnh sửa thủ công.',
    'category': 'Website',
    'author': 'Your Company',
    'depends': ['website_sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/fbt_rule_views.xml',
        'views/website_fbt_templates.xml',
        'data/fbt_cron.xml',
    ],
    'assets': {
        'web.assets_frontend': [ 
            'website_frequently_bought_together/static/src/css/fbt_styles.css',
            'website_frequently_bought_together/static/src/js/fbt_carousel.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

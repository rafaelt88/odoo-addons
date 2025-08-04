from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_fbt_products(self):
        self.ensure_one()
        rule = self.env['website.fbt.rule'].with_context(prefetch_fields=False).search([
            ('product_id', '=', self.id),
            ('active', '=', True)
        ], limit=1)
        product_ids = set(rule.fbt_product_ids.ids)
        # Chỉ lấy sản phẩm đang publish trên website
        products = self.env['product.template'].browse(list(product_ids))
        products = products.filtered(lambda p: p.website_published)
        return products

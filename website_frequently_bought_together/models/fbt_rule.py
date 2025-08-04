from odoo import models, fields, api

class FrequentlyBoughtTogetherRule(models.Model):
    _name = 'website.fbt.rule'
    _description = 'Frequently Bought Together Rule'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.template', string='Main Product', required=True, ondelete='cascade')
    fbt_product_ids = fields.Many2many('product.template', 'website_fbt_rel', 'rule_id', 'product_id', string='FBT Products')
    is_manual = fields.Boolean('Manual', default=False, help='Đánh dấu nếu là gợi ý thủ công')
    active = fields.Boolean('Active', default=True)
    confidence = fields.Float('Confidence', help='Độ tin cậy của gợi ý (AI)')
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)

    _sql_constraints = [
        ('product_unique', 'unique(product_id)', 'Chỉ một rule cho mỗi sản phẩm!'),
    ]

    @api.model
    def update_fbt_rules(self):
        # Phân tích đơn hàng để cập nhật FBT rule tự động
        SaleOrder = self.env['sale.order']
        Product = self.env['product.template']
        # Lấy các đơn hàng đã xác nhận
        orders = SaleOrder.search([('state', 'in', ['sale', 'done'])])
        product_pairs = {}
        for order in orders:
            product_ids = set(order.order_line.mapped('product_id.product_tmpl_id.id'))
            for pid in product_ids:
                others = product_ids - {pid}
                if not others:
                    continue
                product_pairs.setdefault(pid, {})
                for opid in others:
                    product_pairs[pid][opid] = product_pairs[pid].get(opid, 0) + 1
        for pid, related in product_pairs.items():
            # Lấy top 10 sản phẩm mua cùng nhiều nhất
            top_related = sorted(related.items(), key=lambda x: x[1], reverse=True)[:10]
            fbt_ids = [opid for opid, _ in top_related]
            rule = self.search([('product_id', '=', pid), ('is_manual', '=', False)], limit=1)
            if rule:
                rule.write({
                    'fbt_product_ids': [(6, 0, fbt_ids)],
                    'confidence': sum([c for _, c in top_related]) / (len(related) or 1),
                    'last_update': fields.Datetime.now(),
                })
            else:
                self.create({
                    'product_id': pid,
                    'fbt_product_ids': [(6, 0, fbt_ids)],
                    'is_manual': False,
                    'confidence': sum([c for _, c in top_related]) / (len(related) or 1),
                    'last_update': fields.Datetime.now(),
                })

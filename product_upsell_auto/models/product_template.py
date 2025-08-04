# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    auto_upsell_recommendation_ids = fields.One2many(
        "product.recommendation",
        "source_product_id",
        string="Auto Upsell Recommendations",
        domain=[("type", "=", "upsell"), ("active", "=", True)],
        help="Automatically generated upsell recommendations for this product",
    )

    auto_crosssell_recommendation_ids = fields.One2many(
        "product.recommendation",
        "source_product_id",
        string="Auto Cross-sell Recommendations",
        domain=[("type", "=", "crosssell"), ("active", "=", True)],
        help="Automatically generated cross-sell recommendations for this product",
    )

    upsell_recommendation_count = fields.Integer(
        string="Upsell Count", compute="_compute_recommendation_counts"
    )

    crosssell_recommendation_count = fields.Integer(
        string="Cross-sell Count", compute="_compute_recommendation_counts"
    )

    @api.depends("auto_upsell_recommendation_ids", "auto_crosssell_recommendation_ids")
    def _compute_recommendation_counts(self):
        for product in self:
            product.upsell_recommendation_count = len(
                product.auto_upsell_recommendation_ids
            )
            product.crosssell_recommendation_count = len(
                product.auto_crosssell_recommendation_ids
            )

    def action_generate_upsell(self):
        """Generate upsell recommendations for this product"""
        self.ensure_one()

        _logger.info(f"Generating upsell recommendations for product: {self.name}")

        # Clear existing auto-generated upsell recommendations
        existing_upsells = self.env["product.recommendation"].search(
            [
                ("source_product_id", "=", self.id),
                ("type", "=", "upsell"),
                ("created_by_system", "=", True),
            ]
        )
        existing_upsells.unlink()

        # Find potential upsell products
        upsell_candidates = self._find_upsell_candidates()

        # Create recommendations
        recommendations_created = 0
        for candidate, score in upsell_candidates:
            self.env["product.recommendation"].create(
                {
                    "source_product_id": self.id,
                    "recommended_product_id": candidate.id,
                    "type": "upsell",
                    "score": score,
                    "created_by_system": True,
                }
            )
            recommendations_created += 1

        _logger.info(
            f"Created {recommendations_created} upsell recommendations for {self.name}"
        )
        return recommendations_created

    def _find_upsell_candidates(self):
        """Find potential upsell products with scoring"""
        self.ensure_one()

        candidates = []

        # Criteria 1: Same category, higher price
        if self.categ_id:
            same_category_products = self.search(
                [
                    ("categ_id", "=", self.categ_id.id),
                    ("id", "!=", self.id),
                    ("list_price", ">", self.list_price),
                    ("sale_ok", "=", True),
                    ("active", "=", True),
                    ("website_published", "=", True),  # Only published products
                ]
            )

            for product in same_category_products:
                # Calculate score based on price difference
                price_ratio = (
                    product.list_price / self.list_price if self.list_price > 0 else 1
                )

                # Prefer products 1.2x to 3x the original price
                if 1.2 <= price_ratio <= 3.0:
                    score = 100 - abs(price_ratio - 1.5) * 20  # Optimal around 1.5x
                elif price_ratio < 1.2:
                    score = 50  # Too close in price
                else:
                    score = 30  # Too expensive

                # Boost score for products with higher ratings if available
                if hasattr(product, "rating_avg") and product.rating_avg:
                    score += product.rating_avg * 5

                candidates.append((product, score))

        # Criteria 2: Parent category, higher price (if same category has few results)
        if len(candidates) < 5 and self.categ_id and self.categ_id.parent_id:
            parent_category_products = self.search(
                [
                    ("categ_id", "child_of", self.categ_id.parent_id.id),
                    ("categ_id", "!=", self.categ_id.id),
                    ("id", "!=", self.id),
                    ("list_price", ">", self.list_price),
                    ("sale_ok", "=", True),
                    ("active", "=", True),
                    ("website_published", "=", True),
                ]
            )

            for product in parent_category_products:
                price_ratio = (
                    product.list_price / self.list_price if self.list_price > 0 else 1
                )

                if 1.1 <= price_ratio <= 2.5:
                    score = (
                        60 - abs(price_ratio - 1.3) * 15
                    )  # Lower base score for different category

                    if hasattr(product, "rating_avg") and product.rating_avg:
                        score += product.rating_avg * 3

                    candidates.append((product, score))

        # Sort by score and return top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:5]  # Top 5 recommendations

    @api.model
    def action_generate_all_upsell(self):
        """Generate upsell recommendations for all products"""
        _logger.info("Starting bulk upsell generation for all products")

        # Get all saleable products
        products = self.search(
            [
                ("sale_ok", "=", True),
                ("active", "=", True),
                ("list_price", ">", 0),
            ]
        )

        total_products = len(products)
        total_recommendations = 0

        for i, product in enumerate(products, 1):
            try:
                recommendations_count = product.action_generate_upsell()
                total_recommendations += recommendations_count

                # Log progress every 50 products
                if i % 50 == 0:
                    _logger.info(
                        f"Processed {i}/{total_products} products, {total_recommendations} recommendations created"
                    )

            except Exception as e:
                _logger.error(
                    f"Error generating upsell for product {product.name}: {e}"
                )
                continue

        _logger.info(
            f"Completed bulk upsell generation: {total_recommendations} recommendations for {total_products} products"
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Upsell Generation Complete"),
                "message": _("Generated %d upsell recommendations for %d products")
                % (total_recommendations, total_products),
                "type": "success",
                "sticky": False,
            },
        }

    def get_upsell_recommendations(self, limit=3):
        """Get active upsell recommendations for this product"""
        self.ensure_one()

        # Debug logging
        import logging

        _logger = logging.getLogger(__name__)
        _logger.info(f"=== GET UPSELL FOR {self.name} ===")

        # Đảm bảo sản phẩm recommended được published
        self.ensure_recommended_products_published()

        all_recommendations = self.auto_upsell_recommendation_ids
        _logger.info(f"All recommendations count: {len(all_recommendations)}")

        if not all_recommendations:
            _logger.info("No recommendations found, returning empty list")
            return self.env["product.template"]

        # Chỉ filter active recommendations, không filter gì khác
        active_recommendations = all_recommendations.filtered(lambda r: r.active)
        _logger.info(f"Active recommendations: {len(active_recommendations)}")

        if not active_recommendations:
            _logger.info("No active recommendations found")
            return self.env["product.template"]

        # Lấy sản phẩm recommended mà không filter gì thêm
        products = active_recommendations.mapped("recommended_product_id")[:limit]

        _logger.info(f"Final products returned: {len(products)}")
        for p in products:
            _logger.info(f"  - {p.name} (ID: {p.id})")
            _logger.info(f"    Active: {p.active}")
            _logger.info(f"    Sale OK: {p.sale_ok}")
            _logger.info(f"    Published: {p.website_published}")

        # Nếu vẫn không có sản phẩm nào, thử tạo một danh sách demo
        if not products:
            _logger.info("No valid products, trying to get some demo products")
            demo_products = self.env["product.template"].search(
                [("active", "=", True), ("sale_ok", "=", True), ("id", "!=", self.id)],
                limit=2,
            )
            _logger.info(f"Demo products found: {len(demo_products)}")
            return demo_products

        return products

    def action_view_recommendations(self):
        """Action to view recommendations for this product"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Product Recommendations"),
            "res_model": "product.recommendation",
            "view_mode": "tree,form",
            "domain": [("source_product_id", "=", self.id)],
            "context": {
                "default_source_product_id": self.id,
                "search_default_active": 1,
            },
        }

    def ensure_recommended_products_published(self):
        """Đảm bảo các sản phẩm được recommend có website_published = True"""
        import logging

        _logger = logging.getLogger(__name__)

        for rec in self.auto_upsell_recommendation_ids:
            if (
                rec.recommended_product_id
                and not rec.recommended_product_id.website_published
            ):
                _logger.info(
                    f"Setting website_published=True for {rec.recommended_product_id.name}"
                )
                rec.recommended_product_id.sudo().write({"website_published": True})
            if rec.recommended_product_id and not rec.recommended_product_id.sale_ok:
                _logger.info(
                    f"Setting sale_ok=True for {rec.recommended_product_id.name}"
                )
                rec.recommended_product_id.sudo().write({"sale_ok": True})

    def get_related_combos(self, limit=4):
        """Get combos that contain this product"""
        self.ensure_one()

        _logger.info(f"Getting related combos for product: {self.name} (ID: {self.id})")

        # Find combo lines that contain this product (search by product_tmpl_id)
        combo_lines = self.env["product.combo.line"].search(
            [("product_id.product_tmpl_id", "=", self.id)]
        )

        _logger.info(f"Found {len(combo_lines)} combo lines for product {self.id}")

        # Get the combos
        combos = combo_lines.mapped("combo_id").filtered(
            lambda c: c.active and c.website_published
        )

        _logger.info(
            f"Found {len(combos)} active combos for product {self.name}: {[c.name for c in combos]}"
        )

        return combos[:limit]

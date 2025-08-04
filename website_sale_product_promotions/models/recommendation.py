# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductRecommendation(models.Model):
    _name = "product.recommendation"
    _description = "Product Recommendation"
    _order = "source_product_id, score desc"

    source_product_id = fields.Many2one(
        "product.template",
        string="Source Product",
        required=True,
        ondelete="cascade",
        help="The product for which we are making recommendations",
    )

    recommended_product_id = fields.Many2one(
        "product.template",
        string="Recommended Product",
        required=True,
        ondelete="cascade",
        help="The product being recommended",
    )

    type = fields.Selection(
        [
            ("upsell", "Upsell"),
            ("crosssell", "Cross-sell"),
        ],
        string="Recommendation Type",
        required=True,
        default="upsell",
    )

    score = fields.Float(
        string="Recommendation Score",
        help="Higher score means higher priority for recommendation",
        default=1.0,
    )

    price_difference = fields.Float(
        string="Price Difference",
        compute="_compute_price_difference",
        store=True,
        help="Price difference between recommended and source product",
    )

    price_difference_percent = fields.Float(
        string="Price Difference (%)",
        compute="_compute_price_difference",
        store=True,
        help="Price difference percentage",
    )

    active = fields.Boolean(string="Active", default=True)

    created_by_system = fields.Boolean(
        string="Created by System",
        default=False,
        help="True if this recommendation was created automatically",
    )

    @api.depends("source_product_id.list_price", "recommended_product_id.list_price")
    def _compute_price_difference(self):
        for rec in self:
            if rec.source_product_id and rec.recommended_product_id:
                source_price = rec.source_product_id.list_price
                recommended_price = rec.recommended_product_id.list_price
                rec.price_difference = recommended_price - source_price
                if source_price > 0:
                    rec.price_difference_percent = (
                        rec.price_difference / source_price
                    ) * 100
                else:
                    rec.price_difference_percent = 0.0
            else:
                rec.price_difference = 0.0
                rec.price_difference_percent = 0.0

    @api.constrains("source_product_id", "recommended_product_id")
    def _check_different_products(self):
        for rec in self:
            if rec.source_product_id.id == rec.recommended_product_id.id:
                raise ValidationError(
                    _(u"Source product and recommended product must be different.")
                )

    @api.model
    def create(self, vals):
        # Check for duplicates
        existing = self.search(
            [
                ("source_product_id", "=", vals.get("source_product_id")),
                ("recommended_product_id", "=", vals.get("recommended_product_id")),
                ("type", "=", vals.get("type", "upsell")),
            ]
        )
        if existing:
            # Update existing record instead of creating duplicate
            existing.write(
                {
                    "score": vals.get("score", existing.score),
                    "active": vals.get("active", existing.active),
                    "created_by_system": vals.get(
                        "created_by_system", existing.created_by_system
                    ),
                }
            )
            return existing

        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.source_product_id.name} → {rec.recommended_product_id.name} ({rec.type})"
            result.append((rec.id, name))
        return result

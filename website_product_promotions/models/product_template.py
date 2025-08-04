# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    upsell_ids = fields.Many2many(
        "product.template",
        "product_upsell_rel",
        "product_id",
        "upsell_id",
        string="Upsell Products",
        help="Suggest higher-end alternatives to customers",
    )

    cross_sell_ids = fields.Many2many(
        "product.template",
        "product_cross_sell_rel",
        "product_id",
        "cross_sell_id",
        string="Cross-sell Products",
        help="Suggest complementary products",
    )

    combo_count = fields.Integer(
        string="Combo Count", compute="_compute_combo_count", store=True
    )

    def _compute_combo_count(self):
        for product in self:
            combo_lines = self.env["product.combo.line"].search(
                [("product_id.product_tmpl_id", "=", product.id)]
            )
            product.combo_count = len(combo_lines.mapped("combo_id"))

    def action_view_combos(self):
        """Action to view combos containing this product"""
        self.ensure_one()
        combo_lines = self.env["product.combo.line"].search(
            [("product_id.product_tmpl_id", "=", self.id)]
        )
        combo_ids = combo_lines.mapped("combo_id").ids

        return {
            "type": "ir.actions.act_window",
            "name": f"Combos containing {self.name}",
            "res_model": "product.combo",
            "view_mode": "tree,form",
            "domain": [("id", "in", combo_ids)],
            "context": {
                "default_combo_line_ids": [
                    (0, 0, {"product_id": self.product_variant_id.id})
                ]
            },
        }

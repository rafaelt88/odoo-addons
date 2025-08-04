# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductCombo(models.Model):
    _name = "product.combo"
    _description = "Product Combo"
    _order = "sequence, name"

    name = fields.Char(string="Combo Name", required=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    website_published = fields.Boolean(string="Website Published", default=True)

    # Pricing
    combo_price = fields.Float(string="Combo Price", required=True)
    original_price = fields.Float(
        string="Original Price", compute="_compute_original_price", store=True
    )
    discount_amount = fields.Float(
        string="Discount Amount", compute="_compute_discount", store=True
    )
    discount_percentage = fields.Float(
        string="Discount %", compute="_compute_discount", store=True
    )

    # Relations
    combo_line_ids = fields.One2many(
        "product.combo.line", "combo_id", string="Combo Products"
    )

    # Computed fields
    product_count = fields.Integer(
        string="Products Count", compute="_compute_product_count"
    )

    @api.depends("combo_line_ids.quantity", "combo_line_ids.product_id.list_price")
    def _compute_original_price(self):
        for combo in self:
            total = 0.0
            for line in combo.combo_line_ids:
                if line.product_id:
                    total += line.product_id.list_price * line.quantity
            combo.original_price = total

    @api.depends("original_price", "combo_price")
    def _compute_discount(self):
        for combo in self:
            if combo.original_price > 0:
                combo.discount_amount = combo.original_price - combo.combo_price
                combo.discount_percentage = (
                    combo.discount_amount / combo.original_price
                ) * 100
            else:
                combo.discount_amount = 0.0
                combo.discount_percentage = 0.0

    @api.depends("combo_line_ids")
    def _compute_product_count(self):
        for combo in self:
            combo.product_count = len(combo.combo_line_ids)

    @api.constrains("combo_price", "original_price")
    def _check_combo_price(self):
        for combo in self:
            if combo.combo_price < 0:
                raise ValidationError(_("Combo price cannot be negative."))
            if combo.combo_price > combo.original_price:
                raise ValidationError(
                    _("Combo price cannot be higher than original price.")
                )


class ProductComboLine(models.Model):
    _name = "product.combo.line"
    _description = "Product Combo Line"
    _order = "sequence, id"

    combo_id = fields.Many2one(
        "product.combo", string="Combo", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.template", string="Product", required=True)
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # Computed fields
    unit_price = fields.Float(
        string="Unit Price", related="product_id.list_price", readonly=True
    )
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

    @api.depends("quantity", "unit_price")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Quantity must be positive."))

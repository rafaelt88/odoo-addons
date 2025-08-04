# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductCombo(models.Model):
    _name = "product.combo"
    _description = "Product Combo"
    _order = "name"

    name = fields.Char(string="Combo Name", required=True, translate=True)

    active = fields.Boolean(string="Active", default=True)

    price_total = fields.Float(
        string="Combo Price",
        help="Special price for this combo (auto-calculated from discount %)",
    )

    combo_line_ids = fields.One2many(
        "product.combo.line", "combo_id", string="Combo Products", required=True
    )

    original_price = fields.Float(
        string="Original Total Price", compute="_compute_original_price", store=True
    )

    discount_amount = fields.Float(
        string="Discount Amount", compute="_compute_discount_amount", store=True
    )

    discount_percentage = fields.Float(
        string="Discount %",
        default=10.0,
        help="Enter discount percentage to auto-calculate combo price",
    )

    image = fields.Image(
        string="Combo Image", help="Image for combo display on website"
    )

    description = fields.Html(string="Description", translate=True)

    website_published = fields.Boolean(string="Published on Website", default=True)

    @api.depends("combo_line_ids.product_id.lst_price", "combo_line_ids.quantity")
    def _compute_original_price(self):
        for combo in self:
            total = 0.0
            for line in combo.combo_line_ids:
                if line.product_id:
                    total += line.product_id.lst_price * line.quantity
            combo.original_price = total

    @api.depends("original_price", "price_total")
    def _compute_discount_amount(self):
        for combo in self:
            if combo.original_price > 0:
                combo.discount_amount = combo.original_price - combo.price_total
            else:
                combo.discount_amount = 0.0

    @api.onchange("discount_percentage", "original_price", "combo_line_ids")
    def _onchange_discount_percentage(self):
        """Auto-calculate combo price when discount percentage changes"""
        for combo in self:
            if combo.original_price > 0:
                if combo.discount_percentage >= 0:
                    # Calculate new combo price based on discount percentage
                    discount_multiplier = combo.discount_percentage / 100.0
                    discount_amount = combo.original_price * discount_multiplier
                    combo.price_total = combo.original_price - discount_amount
                elif not combo.price_total or combo.price_total <= 0:
                    # If no valid discount set, use default 10% discount
                    combo.price_total = combo.original_price * 0.9
                    combo.discount_percentage = 10.0

                # Ensure price_total is never 0 or negative
                if combo.price_total <= 0:
                    combo.price_total = (
                        combo.original_price * 0.01
                    )  # Minimum 1% of original price

    @api.onchange("price_total", "original_price")
    def _onchange_price_total(self):
        """Auto-calculate discount percentage when combo price changes"""
        for combo in self:
            if combo.original_price > 0:
                discount_amount = combo.original_price - combo.price_total
                combo.discount_percentage = (
                    discount_amount / combo.original_price
                ) * 100

    @api.constrains("combo_line_ids")
    def _check_combo_lines(self):
        for combo in self:
            if len(combo.combo_line_ids) < 2:
                raise ValidationError(_("A combo must have at least 2 products."))

    def get_discount_rate(self):
        """Return discount rate for applying to sale order lines"""
        self.ensure_one()
        # Simply return the discount percentage as it's already stored
        return self.discount_percentage

    @api.model
    def create(self, vals):
        """Initialize combo with proper price calculation"""
        result = super().create(vals)

        # Ensure price_total is calculated
        if result.original_price > 0:
            if "discount_percentage" in vals and vals["discount_percentage"] >= 0:
                # Use provided discount percentage
                discount_multiplier = result.discount_percentage / 100.0
                result.price_total = result.original_price * (1 - discount_multiplier)
            elif "price_total" not in vals or not result.price_total:
                # Use default discount if no price_total provided
                result.price_total = result.original_price * 0.9  # 10% default discount
                result.discount_percentage = 10.0
            else:
                # Calculate discount percentage from provided price_total
                discount_amount = result.original_price - result.price_total
                result.discount_percentage = (
                    discount_amount / result.original_price
                ) * 100

        return result

    def write(self, vals):
        """Ensure price_total is updated when needed"""
        result = super().write(vals)

        # If discount_percentage changed, recalculate price_total
        if "discount_percentage" in vals:
            for combo in self:
                if combo.original_price > 0:
                    discount_multiplier = combo.discount_percentage / 100.0
                    combo.price_total = combo.original_price * (1 - discount_multiplier)

        # Final validation
        for combo in self:
            if combo.price_total <= 0:
                raise ValidationError(
                    _(
                        "Combo price must be greater than 0. Please check your discount percentage."
                    )
                )

        return result

    def _validate_combo_data(self):
        """Validate combo data before save"""
        for combo in self:
            if combo.original_price <= 0:
                raise ValidationError(_("Please add products to the combo first."))
            if combo.discount_percentage < 0 or combo.discount_percentage > 100:
                raise ValidationError(
                    _("Discount percentage must be between 0% and 100%.")
                )
            if combo.price_total <= 0:
                raise ValidationError(_("Combo price must be greater than 0."))
            if combo.price_total > combo.original_price:
                raise ValidationError(
                    _("Combo price cannot be greater than original price.")
                )

    def action_calculate_price(self):
        """Button action to recalculate combo price"""
        for combo in self:
            if combo.original_price > 0 and combo.discount_percentage >= 0:
                discount_multiplier = combo.discount_percentage / 100.0
                combo.price_total = combo.original_price * (1 - discount_multiplier)
        return True

    def check_combo_match(self, order_lines):
        """Check if order lines match this combo exactly"""
        self.ensure_one()

        combo_products = {}
        for line in self.combo_line_ids:
            product_id = line.product_id.id
            combo_products[product_id] = (
                combo_products.get(product_id, 0) + line.quantity
            )

        order_products = {}
        for line in order_lines:
            if line.product_id:
                product_id = line.product_id.id
                order_products[product_id] = (
                    order_products.get(product_id, 0) + line.product_uom_qty
                )

        return combo_products == order_products


class ProductComboLine(models.Model):
    _name = "product.combo.line"
    _description = "Product Combo Line"
    _order = "combo_id, sequence, id"

    combo_id = fields.Many2one(
        "product.combo", string="Combo", required=True, ondelete="cascade"
    )

    sequence = fields.Integer(string="Sequence", default=10)

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        domain=[("sale_ok", "=", True)],
    )

    quantity = fields.Float(string="Quantity", required=True, default=1.0)

    unit_price = fields.Float(
        string="Unit Price", related="product_id.lst_price", readonly=True
    )

    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

    @api.depends("product_id.lst_price", "quantity")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.unit_price * line.quantity

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than 0."))

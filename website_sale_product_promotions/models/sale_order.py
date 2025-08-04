# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    applied_combo_ids = fields.Many2many(
        "product.combo",
        string="Applied Combos",
        help="Combos that have been applied to this order",
    )

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs
    ):
        """Override to check and apply combo discounts after cart update"""
        try:
            result = super()._cart_update(
                product_id, line_id, add_qty, set_qty, **kwargs
            )

            # Check for applicable combos after cart update
            self._apply_combo_discounts()

            return result
        except Exception as e:
            # Log the error and continue with normal cart update
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error(f"Error in combo cart update: {e}")
            return super()._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

    def _apply_combo_discounts(self):
        """Check all active combos and apply discounts if cart matches"""
        self.ensure_one()

        # Skip if order is already confirmed or if no order lines
        if self.state != "draft" or not self.order_line:
            return

        try:
            # Reset previous combo applications
            existing_lines = self.order_line.filtered(lambda l: l.product_id)
            existing_lines.write({"discount": 0, "combo_applied": False})
            self.applied_combo_ids = [(5, 0, 0)]

            # Get all active combos
            active_combos = self.env["product.combo"].search([("active", "=", True)])

            applied_combos = []
            for combo in active_combos:
                if self._check_and_apply_combo(combo):
                    applied_combos.append(combo.id)

            if applied_combos:
                self.applied_combo_ids = [(6, 0, applied_combos)]
        except Exception as e:
            # Log the error but don't fail the entire operation
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error(f"Error applying combo discounts: {e}")
            pass

    def _check_and_apply_combo(self, combo):
        """Check if combo can be applied and apply it"""
        self.ensure_one()

        # Get order lines that haven't been used in other combos
        available_lines = self.order_line.filtered(
            lambda l: not l.combo_applied and l.product_id
        )

        # Check if we have all required products with sufficient quantities
        combo_products = {}
        for combo_line in combo.combo_line_ids:
            product_id = combo_line.product_id.id
            combo_products[product_id] = combo_line.quantity

        # Find matching order lines
        matching_lines = []
        for product_id, required_qty in combo_products.items():
            available_qty = 0
            product_lines = []

            for order_line in available_lines:
                if order_line.product_id.id == product_id:
                    available_qty += order_line.product_uom_qty
                    product_lines.append(order_line)

            if available_qty < required_qty:
                return False  # Not enough quantity for this product

            # Select lines to fulfill the combo requirement
            remaining_qty = required_qty
            for line in product_lines:
                if remaining_qty <= 0:
                    break

                take_qty = min(line.product_uom_qty, remaining_qty)
                matching_lines.append((line, take_qty))
                remaining_qty -= take_qty

        # Apply combo discount to matching lines
        if len(matching_lines) > 0:
            discount_rate = combo.get_discount_rate()

            for order_line, used_qty in matching_lines:
                # If we're using the full line quantity
                if used_qty == order_line.product_uom_qty:
                    order_line.write(
                        {
                            "discount": discount_rate,
                            "combo_applied": True,
                            "combo_id": combo.id,
                        }
                    )
                else:
                    # Split the line if we're only using part of it
                    order_line.write(
                        {"product_uom_qty": order_line.product_uom_qty - used_qty}
                    )

                    # Create new line for combo portion
                    new_line_vals = order_line.copy_data()[0]
                    new_line_vals.update(
                        {
                            "order_id": self.id,  # Fix: Ensure order_id is set
                            "product_uom_qty": used_qty,
                            "discount": discount_rate,
                            "combo_applied": True,
                            "combo_id": combo.id,
                        }
                    )
                    # Create with context to ensure proper order assignment
                    self.env["sale.order.line"].with_context(
                        default_order_id=self.id, active_order=self
                    ).create(new_line_vals)

            return True

        return False

    def add_combo_to_cart(self, combo_id):
        """Add all products from a combo to cart with appropriate discounts"""
        combo = self.env["product.combo"].browse(combo_id)
        if not combo.exists() or not combo.active:
            return False

        # Add each product from combo to cart
        for combo_line in combo.combo_line_ids:
            if combo_line.product_id and combo_line.quantity > 0:
                self._cart_update(
                    product_id=combo_line.product_id.id, add_qty=combo_line.quantity
                )

        return True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    combo_applied = fields.Boolean(
        string="Combo Applied",
        default=False,
        help="Indicates if this line is part of an applied combo",
    )

    combo_id = fields.Many2one(
        "product.combo",
        string="Applied Combo",
        help="The combo that was applied to this line",
    )

    @api.model
    def create(self, vals):
        """Override create to ensure order_id is always set"""
        if "order_id" not in vals and self.env.context.get("default_order_id"):
            vals["order_id"] = self.env.context["default_order_id"]

        if "order_id" not in vals:
            # If no order_id, try to get from current context
            active_order = self.env.context.get("active_order")
            if active_order:
                vals["order_id"] = active_order.id

        return super().create(vals)

# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json


class ComboController(WebsiteSale):

    @http.route(
        "/shop/combo/add",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def add_combo_to_cart(self, combo_id=None, **kwargs):
        """Add a complete combo to cart"""
        try:
            if not combo_id:
                return request.redirect("/shop")

            combo_id = int(combo_id)
            combo = request.env["product.combo"].sudo().browse(combo_id)

            if not combo.exists() or not combo.active:
                return request.redirect("/shop")

            # Get or create sale order
            order = request.website.sale_get_order(force_create=True)

            # Ensure order exists and is in draft state
            if not order or order.state != "draft":
                return request.redirect("/shop")

            # Add combo to cart using the method from website_product_promotions
            if hasattr(order, "add_combo_to_cart") and order.add_combo_to_cart(
                combo_id
            ):
                return request.redirect("/shop/cart")
            else:
                # Fallback: Add products individually
                for combo_line in combo.combo_line_ids:
                    if combo_line.product_id and combo_line.quantity > 0:
                        order._cart_update(
                            product_id=combo_line.product_id.id,
                            add_qty=combo_line.quantity,
                        )
                return request.redirect("/shop/cart")

        except (ValueError, TypeError) as e:
            # Log error for debugging
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error(f"Error adding combo to cart: {e}")
            return request.redirect("/shop")
        except Exception as e:
            # Log unexpected errors
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error(f"Unexpected error in add_combo_to_cart: {e}")
            return request.redirect("/shop")

    @http.route("/shop/combos", type="http", auth="public", website=True)
    def shop_combos(self, **kwargs):
        """Display all available combos"""
        combos = (
            request.env["product.combo"]
            .sudo()
            .search([("active", "=", True), ("website_published", "=", True)])
        )

        values = {
            "combos": combos,
            "page_name": "combos",
        }
        return request.render("website_sale_product_promotions.combo_list", values)

    @http.route("/shop/combo/<int:combo_id>", type="http", auth="public", website=True)
    def combo_detail(self, combo_id, **kwargs):
        """Display combo detail page"""
        combo = request.env["product.combo"].sudo().browse(combo_id)

        if not combo.exists() or not combo.active or not combo.website_published:
            return request.redirect("/shop/combos")

        values = {
            "combo": combo,
            "page_name": "combo_detail",
        }
        return request.render("website_sale_product_promotions.combo_detail", values)

    @http.route("/shop/product/upsell", type="json", auth="public", website=True)
    def get_upsell_products(self, product_id, **kwargs):
        """Get upsell products for a given product"""
        try:
            product = request.env["product.template"].sudo().browse(int(product_id))
            if product.exists():
                upsell_products = product.upsell_ids.filtered(
                    lambda p: p.website_published
                )
                return {
                    "success": True,
                    "products": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "price": p.list_price,
                            "image_url": f"/web/image/product.template/{p.id}/image_1920",
                            "url": f"/shop/product/{p.id}",
                        }
                        for p in upsell_products
                    ],
                }
        except:
            pass

        return {"success": False}

    @http.route("/shop/product/cross_sell", type="json", auth="public", website=True)
    def get_cross_sell_products(self, product_id, **kwargs):
        """Get cross-sell products for a given product"""
        try:
            product = request.env["product.template"].sudo().browse(int(product_id))
            if product.exists():
                cross_sell_products = product.cross_sell_ids.filtered(
                    lambda p: p.website_published
                )
                return {
                    "success": True,
                    "products": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "price": p.list_price,
                            "image_url": f"/web/image/product.template/{p.id}/image_1920",
                            "url": f"/shop/product/{p.id}",
                        }
                        for p in cross_sell_products
                    ],
                }
        except:
            pass

        return {"success": False}

    @http.route("/shop/product/combos", type="json", auth="public", website=True)
    def get_product_combos(self, product_id, **kwargs):
        """Get combos that contain a specific product"""
        try:
            product = request.env["product.template"].sudo().browse(int(product_id))
            if product.exists():
                # Find combos containing this product
                combo_lines = (
                    request.env["product.combo.line"]
                    .sudo()
                    .search([("product_id.product_tmpl_id", "=", product.id)])
                )
                combos = combo_lines.mapped("combo_id").filtered(
                    lambda c: c.active and c.website_published
                )

                return {
                    "success": True,
                    "combos": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "price_total": c.price_total,
                            "original_price": c.original_price,
                            "discount_percentage": c.discount_percentage,
                            "url": f"/shop/combo/{c.id}",
                        }
                        for c in combos
                    ],
                }
        except:
            pass

        return {"success": False}

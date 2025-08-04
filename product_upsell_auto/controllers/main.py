# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleUpsell(WebsiteSale):
    def debug_upsell_data(self, product):
        """Log and return all upsell recommendation data for a product for deep debugging"""
        import logging

        _logger = logging.getLogger(__name__)
        data = {
            "product_id": product.id,
            "product_name": product.name,
            "recommendations": [],
        }
        for rec in product.auto_upsell_recommendation_ids:
            rec_data = {
                "rec_id": rec.id,
                "recommended_product_id": rec.recommended_product_id.id,
                "recommended_product_name": rec.recommended_product_id.name,
                "active": rec.active,
                "type": rec.type,
                "website_published": rec.recommended_product_id.website_published,
                "sale_ok": rec.recommended_product_id.sale_ok,
                "product_active": rec.recommended_product_id.active,
                "score": rec.score,
            }
            data["recommendations"].append(rec_data)
            _logger.warning(f"[DEBUG] Upsell Rec: {rec_data}")
        _logger.warning(f"[DEBUG] All upsell data: {data}")
        return data

    def product(self, product, category="", search="", **kwargs):
        result = super().product(product, category, search, **kwargs)
        # Debug: kiểm tra product và context trả về
        import logging

        _logger = logging.getLogger(__name__)
        _logger.warning(f"[DEBUG] Controller product: {product}")
        _logger.warning(f"[DEBUG] Controller result type: {type(result)}")
        if isinstance(result, dict):
            _logger.warning(f"[DEBUG] Controller context keys: {list(result.keys())}")
            result["upsell_products"] = product.get_upsell_recommendations()
            _logger.warning(
                f"[DEBUG] Controller upsell_products: {result['upsell_products']}"
            )
        return result

    @http.route(
        ["/shop/product/upsell/<int:product_id>"],
        type="json",
        auth="public",
        website=True,
    )
    def get_product_upsell(self, product_id, limit=4, **kwargs):
        """JSON endpoint to get upsell recommendations"""
        try:
            product = request.env["product.template"].sudo().browse(product_id)
            if not product.exists():
                return {"success": False, "message": "Product not found"}

            upsell_products = product.get_upsell_recommendations(limit=limit)

            products_data = []
            for upsell_product in upsell_products:
                products_data.append(
                    {
                        "id": upsell_product.id,
                        "name": upsell_product.name,
                        "price": upsell_product.list_price,
                        "currency": request.env.company.currency_id.symbol,
                        "image_url": f"/web/image/product.template/{upsell_product.id}/image_1920",
                        "url": f"/shop/product/{upsell_product.id}",
                        "description_sale": upsell_product.description_sale or "",
                    }
                )

            return {
                "success": True,
                "products": products_data,
                "count": len(products_data),
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    @http.route(
        ["/shop/generate_upsell"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def generate_upsell_recommendations(self, **kwargs):
        """Manual trigger to generate upsell recommendations (admin only)"""
        if not request.env.user.has_group("sales_team.group_sale_manager"):
            return request.redirect("/shop")

        try:
            # Trigger upsell generation
            request.env["product.template"].sudo().action_generate_all_upsell()

            return request.redirect(
                "/web#action=product_upsell_auto.action_product_recommendation"
            )

        except Exception as e:
            # Log error and redirect
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error(f"Error generating upsell recommendations: {e}")
            return request.redirect("/shop")

    @http.route(
        ["/shop/combo/add_to_cart"],
        type="json",
        auth="public",
        website=True,
    )
    def add_combo_to_cart(self, combo_id, **kwargs):
        """Add combo products to cart"""
        try:
            combo = request.env["product.combo"].sudo().browse(combo_id)
            if not combo.exists() or not combo.active or not combo.website_published:
                return {"success": False, "message": "Combo not found or not available"}

            sale_order = request.website.sale_get_order(force_create=True)

            # Add each product in combo to cart
            for line in combo.combo_line_ids:
                if line.product_id and line.quantity > 0:
                    sale_order._cart_update(
                        product_id=line.product_id.product_variant_ids[0].id,
                        add_qty=line.quantity,
                        combo_id=combo.id,  # Track combo reference
                    )

            return {
                "success": True,
                "message": f"Combo '{combo.name}' added to cart",
                "cart_quantity": sale_order.cart_quantity,
            }

        except Exception as e:
            import logging

            _logger = logging.getLogger(__name__)
            _logger.error(f"Error adding combo to cart: {e}")
            return {"success": False, "message": str(e)}

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

    @http.route("/test/combo", type="http", auth="public", website=True)
    def test_combo(self, **kwargs):
        """Test route to debug combo functionality"""
        # Get any product for testing
        product = request.env["product.template"].search(
            [("website_published", "=", True)], limit=1
        )

        if not product:
            return "No products found"

        # Ensure we have at least one combo for testing
        combo_count = request.env["product.combo"].sudo().search_count([])
        if combo_count == 0:
            # Create a test combo if none exists
            try:
                products = (
                    request.env["product.product"]
                    .sudo()
                    .search([("sale_ok", "=", True)], limit=2)
                )
                if len(products) >= 2:
                    test_combo = (
                        request.env["product.combo"]
                        .sudo()
                        .create(
                            {
                                "name": "Test Combo for Debug",
                                "description": "Auto-generated combo for testing",
                                "discount_percentage": 15.0,
                                "active": True,
                                "website_published": True,
                            }
                        )
                    )

                    # Add products to combo
                    for i, prod in enumerate(products):
                        request.env["product.combo.line"].sudo().create(
                            {
                                "combo_id": test_combo.id,
                                "product_id": prod.id,
                                "quantity": 1,
                                "sequence": (i + 1) * 10,
                            }
                        )
            except Exception as e:
                import logging

                _logger = logging.getLogger(__name__)
                _logger.error(f"Error creating test combo: {e}")

        # Test get_related_combos method
        related_combos = product.get_related_combos()

        # Also get all combos for comparison
        all_combos = (
            request.env["product.combo"]
            .sudo()
            .search([("active", "=", True), ("website_published", "=", True)])
        )

        values = {
            "product": product,
            "related_combos": related_combos,
            "all_combos": all_combos,
        }

        return request.render("product_upsell_auto.test_combo_page", values)

    @http.route("/test/add-combo", type="http", auth="public", website=True)
    def test_add_combo(self, **kwargs):
        """Test add combo route"""
        return """
        <html>
        <body>
            <h1>Test Add Combo</h1>
            <form action="/shop/combo/add" method="post">
                <input type="hidden" name="combo_id" value="1"/>
                <button type="submit">Test Add Combo 1</button>
            </form>
            <br/>
            <a href="/test/combo">Back to Test Page</a>
        </body>
        </html>
        """

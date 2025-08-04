# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class SaasWebsitePlansController(http.Controller):
    """Controller for displaying SaaS plans on website"""

    @http.route("/saas/plans", type="http", auth="public", website=True, sitemap=True)
    def plans_index(self, **kwargs):
        """Display all active SaaS plans"""
        try:
            # Check if saas.plan model exists
            try:
                Plan = request.env["saas.plan"].sudo()
            except Exception as e:
                return f"<h1>Error: saas.plan model not found</h1><p>Please make sure saas_plan_management module is installed. Error: {str(e)}</p>"

            plans = Plan.search(
                [("active", "=", True)], order="sequence, plan_type, name"
            )

            if not plans:
                # If no plans available, show message
                try:
                    return request.render("saas_website_plans.no_plans_available")
                except Exception as e:
                    return f"<h1>No Plans Available</h1><p>No active SaaS plans found. Template error: {str(e)}</p>"

            # Group plans by type for better organization
            plans_by_type = {}
            for plan in plans:
                plan_type = plan.plan_type
                if plan_type not in plans_by_type:
                    plans_by_type[plan_type] = []
                plans_by_type[plan_type].append(plan)

            # Get plan type labels
            plan_type_labels = dict(Plan._fields["plan_type"].selection)

            values = {
                "plans": plans,
                "plans_by_type": plans_by_type,
                "plan_type_labels": plan_type_labels,
                "page_name": "saas_plans",
                "currency": request.env.company.currency_id,
                "main_object": request.env[
                    "saas.plan"
                ],  # Provide empty recordset to avoid singleton error
            }

            return request.render("saas_website_plans.plans_page", values)

        except Exception as e:
            _logger.error("Error displaying SaaS plans: %s", str(e))
            return request.render(
                "saas_website_plans.plans_error",
                {"error_message": "Unable to load SaaS plans. Please try again later."},
            )

    @http.route("/saas/plans/<int:plan_id>", type="http", auth="public", website=True)
    def plan_detail(self, plan_id, **kwargs):
        """Display detailed view of a specific plan"""
        try:
            Plan = request.env["saas.plan"].sudo()
            plan = Plan.browse(plan_id)

            if not plan.exists() or not plan.active:
                return request.not_found()

            # Get related plans (same type or similar price range)
            related_plans = Plan.search(
                [
                    ("active", "=", True),
                    ("id", "!=", plan.id),
                    "|",
                    ("plan_type", "=", plan.plan_type),
                    ("monthly_price", ">=", plan.monthly_price * 0.5),
                    ("monthly_price", "<=", plan.monthly_price * 2.0),
                ],
                limit=3,
                order="sequence",
            )

            values = {
                "plan": plan,
                "related_plans": related_plans,
                "page_name": "plan_detail",
                "main_object": plan,  # Set main_object to the specific plan
            }

            return request.render("saas_website_plans.plan_detail_page", values)

        except Exception as e:
            _logger.error("Error displaying plan %s: %s", plan_id, str(e))
            return request.not_found()

    @http.route(
        "/saas/checkout/<int:plan_id>", type="http", auth="public", website=True
    )
    def checkout(self, plan_id, billing_period="monthly", **kwargs):
        """Checkout page for plan subscription"""
        try:
            Plan = request.env["saas.plan"].sudo()
            plan = Plan.browse(plan_id)

            if not plan.exists() or not plan.active:
                return request.not_found()

            # Calculate price based on billing period
            if billing_period == "yearly" and plan.yearly_price:
                price = plan.yearly_price
                period_label = "year"
            elif billing_period == "quarterly" and plan.quarterly_price:
                price = plan.quarterly_price
                period_label = "quarter"
            else:
                price = plan.monthly_price
                period_label = "month"
                billing_period = "monthly"

            values = {
                "plan": plan,
                "billing_period": billing_period,
                "period_label": period_label,
                "price": price,
                "page_name": "checkout",
                "main_object": plan,  # Set main_object to the specific plan
            }

            return request.render("saas_website_plans.checkout_page", values)

        except Exception as e:
            _logger.error("Error in checkout for plan %s: %s", plan_id, str(e))
            return request.not_found()

    @http.route(
        "/saas/checkout/submit",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def checkout_submit(self, **post):
        """Process checkout form submission"""
        try:
            plan_id = int(post.get("plan_id", 0))
            Plan = request.env["saas.plan"].sudo()
            plan = Plan.browse(plan_id)

            if not plan.exists():
                return request.render(
                    "saas_website_plans.checkout_error",
                    {
                        "error_message": "Invalid plan selected.",
                        "main_object": request.env["saas.plan"],
                    },
                )

            # Validate required fields for customer
            required_fields = ["company_name", "contact_name", "contact_email"]
            missing_fields = [field for field in required_fields if not post.get(field)]

            if missing_fields:
                field_labels = {
                    "company_name": "Company Name",
                    "contact_name": "Contact Name",
                    "contact_email": "Contact Email",
                }
                missing_labels = [
                    field_labels.get(field, field) for field in missing_fields
                ]
                return request.render(
                    "saas_website_plans.checkout_error",
                    {
                        "error_message": f'Please fill in all required fields: {", ".join(missing_labels)}',
                        "main_object": request.env["saas.plan"],
                    },
                )  # Check if customer already exists
            Customer = request.env["saas.customer"].sudo()
            existing_customer = Customer.search(
                [
                    "|",
                    ("contact_email", "=", post.get("contact_email")),
                    ("company_name", "=", post.get("company_name")),
                ],
                limit=1,
            )

            # Auto-generate subdomain if not provided
            company_name = post.get("company_name")
            contact_email = post.get("contact_email")
            preferred_subdomain = post.get("preferred_subdomain", "")
            if not preferred_subdomain:
                # Generate from company name: remove special chars, convert to lowercase
                import re

                preferred_subdomain = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())[
                    :20
                ]

            if existing_customer:
                customer = existing_customer
                _logger.info(f"Found existing customer: {customer.company_name}")
            else:
                # Auto-generate company email from contact email domain if not provided
                company_email = post.get("company_email", "")
                if not company_email and contact_email:
                    domain = contact_email.split("@")[1] if "@" in contact_email else ""
                    if domain:
                        company_email = f"info@{domain}"

                # Create new customer record
                customer_data = {
                    "company_name": company_name,
                    "tax_code": post.get("tax_code", ""),
                    "email": company_email,
                    "contact_name": post.get("contact_name"),
                    "contact_phone": post.get("contact_phone", ""),
                    "contact_email": contact_email,
                    "contact_position": post.get("contact_position", ""),
                    "state": "prospect",
                }

                customer = Customer.create(customer_data)
                _logger.info(
                    f"Created new customer: {customer.company_name}"
                )  # Create lead in CRM
            Lead = request.env["crm.lead"].sudo()
            lead_data = {
                "name": f"SaaS Plan Request - {plan.name} - {customer.company_name}",
                "contact_name": customer.contact_name,
                "email_from": customer.contact_email,
                "phone": customer.contact_phone,
                "partner_name": customer.company_name,  # Use partner_name instead of company_name
                "description": f"""
SaaS Plan Request Details:
Plan: {plan.name}
Billing Period: {post.get('billing_period', 'monthly')}
Company: {customer.company_name}
Contact: {customer.contact_name}
Email: {customer.contact_email}
Preferred Subdomain: {preferred_subdomain}
Requirements: {post.get('requirements', 'None')}
                """,
                "stage_id": 1,
            }

            lead = Lead.create(lead_data)
            _logger.info(
                f"Created lead: {lead.name}"
            )  # Create SaaS Instance (need service package since it's required)
            Instance = request.env["saas.instance"].sudo()
            ServicePackage = request.env["saas.service.package"].sudo()

            # Find or create a default service package
            service_package = ServicePackage.search(
                [("name", "=", "Default Package")], limit=1
            )
            if not service_package:
                # Create a minimal service package
                package_data = {
                    "name": "Default Package",
                    "code": "DEFAULT",
                    "description": "Default service package for new instances",
                    "max_users": 10,
                    "storage_gb": 10.0,
                    "monthly_price": 0.0,
                    "yearly_price": 0.0,
                }
                service_package = ServicePackage.create(package_data)
                _logger.info(f"Created default service package: {service_package.name}")

            # Make subdomain unique if needed
            final_subdomain = preferred_subdomain
            existing_instance = Instance.search(
                [("subdomain", "=", final_subdomain)], limit=1
            )
            if existing_instance:
                counter = 1
                while existing_instance:
                    test_subdomain = f"{preferred_subdomain}{counter}"
                    existing_instance = Instance.search(
                        [("subdomain", "=", test_subdomain)], limit=1
                    )
                    counter += 1
                final_subdomain = f"{preferred_subdomain}{counter-1}"  # Create instance with service package
            instance_data = {
                "instance_name": f"{customer.company_name} - {plan.name}",
                "subdomain": final_subdomain,
                "customer_id": customer.id,
                "plan_id": plan.id,
                "service_package_id": service_package.id,
                "odoo_version": "17.0",
                "server_location": "us-east",
                "status": "trial",
                "billing_cycle": (
                    "monthly"
                    if post.get("billing_period", "monthly") == "monthly"
                    else "yearly"
                ),
            }

            instance = Instance.create(instance_data)
            _logger.info(f"Created instance: {instance.instance_name}")

            # Update customer state to active
            if customer.state == "prospect":
                customer.write({"state": "active"})

            values = {
                "plan": plan,
                "plan_name": plan.name,
                "lead": lead,
                "customer": customer,
                "instance": instance,
                "customer_name": customer.contact_name,
                "customer_email": customer.contact_email,
                "company_name": customer.company_name,
                "billing_period": post.get("billing_period", "monthly"),
                "preferred_subdomain": final_subdomain,
                "instance_url": f"https://{final_subdomain}.saas.com",
                "newsletter_subscribed": bool(post.get("newsletter")),
                "requirements": post.get("requirements", ""),
                "main_object": plan,
            }

            return request.render("saas_website_plans.checkout_success", values)

        except Exception as e:
            _logger.error("Error processing checkout: %s", str(e), exc_info=True)
            return request.render(
                "saas_website_plans.checkout_error",
                {
                    "error_message": f"System error: {str(e)}",
                    "main_object": request.env["saas.plan"],
                },
            )

    @http.route("/saas/api/plan/<int:plan_id>/pricing", type="json", auth="public")
    def get_plan_pricing(self, plan_id, **kwargs):
        """API endpoint to get pricing for different billing periods"""
        try:
            Plan = request.env["saas.plan"].sudo()
            plan = Plan.browse(plan_id)

            if not plan.exists():
                return {"error": "Plan not found"}

            pricing = {
                "monthly": {
                    "price": plan.monthly_price,
                    "period": "month",
                    "total": plan.monthly_price,
                    "savings": 0,
                }
            }

            if plan.quarterly_price:
                monthly_equivalent = plan.monthly_price * 3
                savings = monthly_equivalent - plan.quarterly_price
                pricing["quarterly"] = {
                    "price": plan.quarterly_price,
                    "period": "quarter",
                    "total": plan.quarterly_price,
                    "savings": savings,
                    "savings_percent": (
                        round((savings / monthly_equivalent) * 100, 1)
                        if monthly_equivalent > 0
                        else 0
                    ),
                }

            if plan.yearly_price:
                monthly_equivalent = plan.monthly_price * 12
                savings = monthly_equivalent - plan.yearly_price
                pricing["yearly"] = {
                    "price": plan.yearly_price,
                    "period": "year",
                    "total": plan.yearly_price,
                    "savings": savings,
                    "savings_percent": (
                        round((savings / monthly_equivalent) * 100, 1)
                        if monthly_equivalent > 0
                        else 0
                    ),
                }

            return {"pricing": pricing, "currency": plan.currency_id.symbol}

        except Exception as e:
            _logger.error("Error getting plan pricing: %s", str(e))
            return {"error": "Unable to get pricing information"} @ http.route(
                "/saas/test", type="http", auth="public", website=True
            )

    def test_route(self, **kwargs):
        """Test route to check if controller is working"""
        try:
            return request.render("saas_website_plans.test_page")
        except Exception as e:
            return f"<h1>Controller Working</h1><p>But template error: {str(e)}</p>"

    @http.route("/saas/debug", type="http", auth="public", website=True)
    def debug_info(self, **kwargs):
        """Debug route to check dependencies and data"""
        try:
            output = []
            output.append("<h1>SaaS Website Plans Debug Info</h1>")

            # Check if models exist
            try:
                Plan = request.env["saas.plan"].sudo()
                plans_count = Plan.search_count([])
                output.append(
                    f"<p>✅ saas.plan model found - {plans_count} total plans</p>"
                )

                active_plans = Plan.search_count([("active", "=", True)])
                output.append(f"<p>✅ Active plans: {active_plans}</p>")

                if plans_count > 0:
                    first_plan = Plan.search([], limit=1)
                    output.append(
                        f"<p>📋 First plan: {first_plan.name} (ID: {first_plan.id})</p>"
                    )

            except Exception as e:
                output.append(f"<p>❌ saas.plan model error: {str(e)}</p>")

            try:
                Customer = request.env["saas.customer"].sudo()
                customers_count = Customer.search_count([])
                output.append(
                    f"<p>✅ saas.customer model found - {customers_count} total customers</p>"
                )
            except Exception as e:
                output.append(f"<p>❌ saas.customer model error: {str(e)}</p>")

            # Check templates
            try:
                return request.render("saas_website_plans.test_page")
            except Exception as e:
                output.append(f"<p>❌ Template error: {str(e)}</p>")
                output.append("<p><a href='/saas/plans'>Try main page</a></p>")
                return "".join(output)

        except Exception as e:
            return f"<h1>Debug Error</h1><p>{str(e)}</p>"

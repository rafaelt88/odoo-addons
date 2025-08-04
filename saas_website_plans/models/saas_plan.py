# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaasPlan(models.Model):
    _inherit = "saas.plan"

    # Website-specific fields
    is_published = fields.Boolean(
        string="Published on Website",
        default=True,
        help="Display this plan on the public website",
    )

    is_featured = fields.Boolean(
        string="Featured Plan", default=False, help="Mark as featured/most popular plan"
    )

    website_sequence = fields.Integer(
        string="Website Display Order",
        default=10,
        help="Order for displaying on website (lower = first)",
    )

    short_description = fields.Char(
        string="Short Description", help="Brief description for website display"
    )

    website_button_text = fields.Char(
        string="Button Text",
        default="Get Started",
        help="Text for the CTA button on website",
    )

    # Computed fields for website display
    display_price = fields.Char(
        string="Display Price",
        compute="_compute_display_price",
        help="Formatted price for website display",
    )

    features_list = fields.Html(
        string="Features List", help="HTML list of features for website display"
    )

    @api.depends("monthly_price", "currency_id")
    def _compute_display_price(self):
        """Compute formatted price for display"""
        for plan in self:
            if plan.monthly_price and plan.currency_id:
                plan.display_price = (
                    f"{plan.currency_id.symbol}{plan.monthly_price:,.0f}/month"
                )
            else:
                plan.display_price = "Contact us"

    def get_website_features(self):
        """Get features formatted for website display"""
        self.ensure_one()
        features = []

        # User limit
        if self.unlimited_users:
            features.append("Unlimited users")
        else:
            features.append(f"Up to {self.max_users} users")

        # Storage
        if self.unlimited_storage:
            features.append("Unlimited storage")
        else:
            features.append(f"{self.storage_limit_gb}GB storage")

        # Transactions
        if self.unlimited_transactions:
            features.append("Unlimited transactions")
        else:
            features.append(f"{self.transaction_limit_monthly:,.0f} transactions/month")

        # Emails
        if self.unlimited_emails:
            features.append("Unlimited emails")
        else:
            features.append(f"{self.email_limit_monthly:,.0f} emails/month")

        # API calls
        if self.unlimited_api_calls:
            features.append("Unlimited API calls")
        else:
            features.append(f"{self.api_calls_limit_daily:,.0f} API calls/day")

        # Modules
        if self.included_module_ids:
            features.append(f"{len(self.included_module_ids)} included modules")

        # Additional features
        if self.multi_company_support:
            features.append("Multi-company support")

        if self.custom_domain_support:
            features.append("Custom domain support")

        if self.priority_support:
            features.append("Priority support")

        if self.white_label_option:
            features.append("White label option")

        features.append(f"{self.backup_frequency.title()} backups")

        return features

    def get_pricing_options(self):
        """Get pricing options for different billing cycles"""
        self.ensure_one()
        options = []

        # Monthly pricing
        if self.monthly_price:
            options.append(
                {
                    "period": "monthly",
                    "period_display": "Monthly",
                    "price": self.monthly_price,
                    "price_display": f"{self.currency_id.symbol}{self.monthly_price:,.0f}",
                    "period_label": "/month",
                    "total": self.monthly_price,
                    "savings": 0,
                    "savings_percent": 0,
                    "recommended": False,
                }
            )

        # Quarterly pricing
        if self.quarterly_price:
            monthly_equivalent = self.monthly_price * 3 if self.monthly_price else 0
            savings = (
                monthly_equivalent - self.quarterly_price
                if monthly_equivalent > 0
                else 0
            )
            savings_percent = (
                (savings / monthly_equivalent) * 100 if monthly_equivalent > 0 else 0
            )

            options.append(
                {
                    "period": "quarterly",
                    "period_display": "Quarterly",
                    "price": self.quarterly_price,
                    "price_display": f"{self.currency_id.symbol}{self.quarterly_price:,.0f}",
                    "period_label": "/quarter",
                    "monthly_equivalent": self.quarterly_price / 3,
                    "total": self.quarterly_price,
                    "savings": savings,
                    "savings_percent": round(savings_percent, 1),
                    "recommended": savings_percent > 10,
                }
            )

        # Yearly pricing
        if self.yearly_price:
            monthly_equivalent = self.monthly_price * 12 if self.monthly_price else 0
            savings = (
                monthly_equivalent - self.yearly_price if monthly_equivalent > 0 else 0
            )
            savings_percent = (
                (savings / monthly_equivalent) * 100 if monthly_equivalent > 0 else 0
            )

            options.append(
                {
                    "period": "yearly",
                    "period_display": "Yearly",
                    "price": self.yearly_price,
                    "price_display": f"{self.currency_id.symbol}{self.yearly_price:,.0f}",
                    "period_label": "/year",
                    "monthly_equivalent": self.yearly_price / 12,
                    "total": self.yearly_price,
                    "savings": savings,
                    "savings_percent": round(savings_percent, 1),
                    "recommended": savings_percent > 15,
                }
            )

        return options

    def get_plan_badge(self):
        """Get plan badge/label for display"""
        self.ensure_one()
        if self.is_featured:
            return {"text": "Most Popular", "class": "badge-primary"}
        elif self.plan_type == "free":
            return {"text": "Free Trial", "class": "badge-success"}
        elif self.plan_type == "enterprise":
            return {"text": "Enterprise", "class": "badge-dark"}
        return None

    @api.model
    def get_published_plans(self):
        """Get all published plans for website"""
        return self.search(
            [("active", "=", True), ("is_published", "=", True)],
            order="website_sequence, sequence, plan_type",
        )

    @api.model
    def get_featured_plans(self, limit=3):
        """Get featured plans for website homepage"""
        return self.search(
            [
                ("active", "=", True),
                ("is_published", "=", True),
                ("is_featured", "=", True),
            ],
            order="website_sequence, sequence",
            limit=limit,
        )

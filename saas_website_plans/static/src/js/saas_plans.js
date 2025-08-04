/* SaaS Website Plans - JavaScript */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize the SaaS plans functionality
    initSaasPlans();
});

function initSaasPlans() {
    // Handle form validation
    initFormValidation();

    // Handle smooth scrolling
    initSmoothScrolling();

    // Handle pricing toggles
    initPricingToggles();

    // Handle plan card animations
    initCardAnimations();

    // Auto-generate subdomain from company name
    initAutoGeneration();
}

function initFormValidation() {
    const forms = document.querySelectorAll('.saas-checkout-form');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input[required], textarea[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', function () {
                validateField(this);
            });

            input.addEventListener('input', function () {
                clearFieldError(this);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('input[required], textarea[required]');

    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    // Auto-generate subdomain from company name if empty
    const companyNameField = form.querySelector('#company_name');
    const subdomainField = form.querySelector('#preferred_subdomain');
    if (companyNameField && subdomainField && companyNameField.value && !subdomainField.value) {
        const autoSubdomain = companyNameField.value
            .toLowerCase()
            .replace(/[^a-zA-Z0-9]/g, '')
            .substring(0, 20);
        subdomainField.value = autoSubdomain;
        subdomainField.style.borderColor = '#28a745'; // Green border to show auto-generated
    }

    // Validate subdomain if provided
    if (subdomainField && subdomainField.value) {
        if (!validateSubdomain(subdomainField.value)) {
            showFieldError(subdomainField, 'Subdomain can only contain letters, numbers, and hyphens (3-20 characters)');
            isValid = false;
        }
    }

    // Validate all email fields
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !validateEmail(field.value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
    });

    // Validate phone fields
    const phoneFields = form.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        if (field.value && !validatePhone(field.value)) {
            showFieldError(field, 'Please enter a valid phone number');
            isValid = false;
        }
    });

    // Validate terms checkbox
    const termsCheckbox = form.querySelector('#terms_agreed');
    if (termsCheckbox && !termsCheckbox.checked) {
        showFieldError(termsCheckbox, 'You must agree to the terms and conditions');
        isValid = false;
    }

    return isValid;
}

function validateField(field) {
    const value = field.value.trim();

    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }

    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Please enter a valid email address');
        return false;
    }

    clearFieldError(field);
    return true;
}

function showFieldError(field, message) {
    clearFieldError(field);

    field.classList.add('is-invalid');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;

    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');

    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Additional validation functions
function validateSubdomain(subdomain) {
    const subdomainRegex = /^[a-zA-Z0-9-]+$/;
    return subdomainRegex.test(subdomain);
}

function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            const target = document.querySelector(href);

            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function initPricingToggles() {
    // Handle pricing period switching if implemented
    const pricingToggles = document.querySelectorAll('.pricing-toggle');

    pricingToggles.forEach(toggle => {
        toggle.addEventListener('change', function () {
            const period = this.value;
            updatePricingDisplay(period);
        });
    });
}

function updatePricingDisplay(period) {
    // This function would update pricing displays based on selected period
    // Implementation depends on specific requirements
    console.log('Updating pricing display for period:', period);
}

function initCardAnimations() {
    // Intersection Observer for card animations
    const cards = document.querySelectorAll('.plan-card');

    if ('IntersectionObserver' in window) {
        const cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = 'all 0.6s ease';
            cardObserver.observe(card);
        });
    }
}

// Auto-generate subdomain from company name
function initAutoGeneration() {
    const companyNameField = document.querySelector('#company_name');
    const subdomainField = document.querySelector('#preferred_subdomain');

    if (companyNameField && subdomainField) {
        companyNameField.addEventListener('input', function () {
            if (!subdomainField.value) { // Only auto-generate if subdomain is empty
                const companyName = this.value;
                const autoSubdomain = companyName
                    .toLowerCase()
                    .replace(/[^a-zA-Z0-9]/g, '')
                    .substring(0, 20);

                if (autoSubdomain) {
                    subdomainField.value = autoSubdomain;
                    subdomainField.style.borderColor = '#28a745';

                    // Add helper text
                    let helperText = subdomainField.parentNode.querySelector('.auto-generated-note');
                    if (!helperText) {
                        helperText = document.createElement('small');
                        helperText.className = 'form-text text-success auto-generated-note';
                        helperText.innerHTML = '<i class="fa fa-magic"></i> Auto-generated from company name';
                        subdomainField.parentNode.appendChild(helperText);
                    }
                }
            }
        });

        // Remove auto-generated styling when user manually types
        subdomainField.addEventListener('input', function () {
            this.style.borderColor = '';
            const helperText = this.parentNode.querySelector('.auto-generated-note');
            if (helperText) {
                helperText.remove();
            }
        });
    }
}

// Utility function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Handle form submission with loading state
function handleFormSubmission() {
    const forms = document.querySelectorAll('.saas-checkout-form');

    forms.forEach(form => {
        form.addEventListener('submit', function () {
            const submitButton = this.querySelector('button[type="submit"]');

            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Processing...';
                submitButton.disabled = true;

                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 10000);
            }
        });
    });
}

// Initialize form submission handling
document.addEventListener('DOMContentLoaded', handleFormSubmission);

// Handle plan card hover effects
function initPlanCardEffects() {
    const planCards = document.querySelectorAll('.plan-card');

    planCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Initialize plan card effects
document.addEventListener('DOMContentLoaded', initPlanCardEffects);

// Handle responsive table scrolling
function initResponsiveTable() {
    const tables = document.querySelectorAll('.table-responsive');

    tables.forEach(table => {
        if (table.scrollWidth > table.clientWidth) {
            table.setAttribute('data-scroll', 'true');

            // Add scroll indicators
            const scrollIndicator = document.createElement('div');
            scrollIndicator.className = 'table-scroll-indicator';
            scrollIndicator.innerHTML = '<small class="text-muted">Scroll horizontally to see more →</small>';
            table.parentNode.insertBefore(scrollIndicator, table.nextSibling);
        }
    });
}

// Initialize responsive table handling
document.addEventListener('DOMContentLoaded', initResponsiveTable);

// Handle pricing calculation API calls
async function updatePlanPricing(planId, period) {
    try {
        const response = await fetch(`/saas/api/plan/${planId}/pricing`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ period: period })
        });

        const data = await response.json();

        if (data.error) {
            console.error('Pricing API error:', data.error);
            return null;
        }

        return data.pricing;
    } catch (error) {
        console.error('Error fetching pricing:', error);
        return null;
    }
}

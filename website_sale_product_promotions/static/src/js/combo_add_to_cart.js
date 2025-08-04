/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ComboAddToCart = publicWidget.Widget.extend({
    selector: '.combo_add_to_cart_form',
    events: {
        'submit': '_onSubmitCombo',
    },

    /**
     * Handle combo add to cart form submission
     */
    _onSubmitCombo: function (ev) {
        ev.preventDefault();
        const $form = $(ev.currentTarget);
        const comboId = $form.find('input[name="combo_id"]').val();

        if (!comboId) {
            return;
        }

        // Show loading state
        const $submitBtn = $form.find('button[type="submit"]');
        const originalText = $submitBtn.html();
        $submitBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Adding...');

        // Submit form
        fetch('/shop/combo/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                combo_id: comboId
            })
        }).then(response => {
            if (response.ok) {
                window.location.href = '/shop/cart';
            } else {
                // Reset button state
                $submitBtn.prop('disabled', false).html(originalText);
                alert('Error adding combo to cart. Please try again.');
            }
        }).catch(error => {
            // Reset button state
            $submitBtn.prop('disabled', false).html(originalText);
            console.error('Error:', error);
            alert('Error adding combo to cart. Please try again.');
        });
    },
});

// Initialize widgets when DOM is ready
$(document).ready(function () {
    // Enhanced cart update notifications
    $('.combo_notification').each(function () {
        const $notification = $(this);
        setTimeout(() => {
            $notification.fadeOut();
        }, 5000);
    });

    // Smooth scrolling for suggestion sections
    $('a[href^="#"]').on('click', function (e) {
        const href = this.getAttribute('href');
        if (href === '#' || href === '' || href === null) {
            e.preventDefault();
            return;
        }
        const target = $(href);
        if (target.length) {
            e.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 80
            }, 1000);
        }
    });
});

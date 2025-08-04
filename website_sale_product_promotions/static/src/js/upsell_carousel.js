/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.UpsellCarousel = publicWidget.Widget.extend({
  selector: ".oe_upsell_section",
  start: function () {
    const carousel = this.el.querySelector(".upsell-carousel");
    const btnPrev = this.el.querySelector(".upsell-carousel-nav.prev");
    const btnNext = this.el.querySelector(".upsell-carousel-nav.next");

    if (!carousel || !btnPrev || !btnNext) return;

    btnPrev.addEventListener("click", function () {
      carousel.scrollBy({ left: -280, behavior: "smooth" });
    });
    btnNext.addEventListener("click", function () {
      carousel.scrollBy({ left: 280, behavior: "smooth" });
    });
  },
});

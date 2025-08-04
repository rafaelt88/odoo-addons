/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.FBTCarousel = publicWidget.Widget.extend({
  selector: ".oe_fbt_section",
  start: function () {
    const carousel = this.el.querySelector(".fbt-carousel");
    const btnPrev = this.el.querySelector(".fbt-carousel-nav.prev");
    const btnNext = this.el.querySelector(".fbt-carousel-nav.next");

    if (!carousel || !btnPrev || !btnNext) return;

    btnPrev.addEventListener("click", function () {
      carousel.scrollBy({ left: -280, behavior: "smooth" });
    });
    btnNext.addEventListener("click", function () {
      carousel.scrollBy({ left: 280, behavior: "smooth" });
    });
  },
});

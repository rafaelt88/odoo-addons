// Product Combo Cart JavaScript (No module import)

document.addEventListener("DOMContentLoaded", function () {
  // Handle combo add to cart buttons
  const comboButtons = document.querySelectorAll(".btn-combo-cart");

  comboButtons.forEach((button) => {
    button.addEventListener("click", async function (e) {
      e.preventDefault();

      const comboId = this.dataset.comboId;
      if (!comboId) {
        console.error("No combo ID found");
        return;
      }

      console.log("Adding combo to cart:", comboId);

      try {
        // Show loading state
        const originalText = this.innerHTML;
        this.innerHTML = '<i class="fa fa-spinner fa-spin me-2"></i>Adding...';
        this.disabled = true;

        // Get CSRF token
        const csrfToken =
          document
            .querySelector('meta[name="csrf-token"]')
            ?.getAttribute("content") ||
          document.querySelector('input[name="csrf_token"]')?.value;

        // Call backend to add combo to cart (using existing route from website_product_promotions)
        const formData = new FormData();
        formData.append("combo_id", comboId);
        if (csrfToken) {
          formData.append("csrf_token", csrfToken);
        }

        console.log(
          "Sending request to /shop/combo/add with combo_id:",
          comboId
        );

        const response = await fetch("/shop/combo/add", {
          method: "POST",
          body: formData,
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        console.log("Response status:", response.status);
        console.log("Response URL:", response.url);

        if (response.ok) {
          // Controller redirects, so check final URL
          const finalUrl = response.url;
          console.log("Final URL after redirect:", finalUrl);

          if (finalUrl.includes("/shop/cart")) {
            // Success - combo was added and redirected to cart
            this.innerHTML = '<i class="fa fa-check me-2"></i>Added!';
            this.classList.remove("btn-success");
            this.classList.add("btn-outline-success");

            showNotification("Combo added to cart successfully!", "success");

            // Redirect to cart after short delay
            setTimeout(() => {
              window.location.href = "/shop/cart";
            }, 1000);
          } else if (
            finalUrl.includes("/shop") &&
            !finalUrl.includes("/shop/cart")
          ) {
            // Redirected to shop - might be an error
            console.warn(
              "Redirected to shop page, combo might not have been added"
            );
            throw new Error("Combo could not be added to cart");
          } else {
            // Other successful case
            this.innerHTML = '<i class="fa fa-check me-2"></i>Added!';
            this.classList.remove("btn-success");
            this.classList.add("btn-outline-success");

            showNotification("Combo added to cart successfully!", "success");

            // Reset button after 2 seconds
            setTimeout(() => {
              this.innerHTML = originalText;
              this.classList.remove("btn-outline-success");
              this.classList.add("btn-success");
              this.disabled = false;
            }, 2000);
          }
        } else {
          console.error("Response not OK, status:", response.status);
          throw new Error(
            `HTTP ${response.status}: Failed to add combo to cart`
          );
        }
      } catch (error) {
        console.error("Error adding combo to cart:", error);

        // Error feedback
        this.innerHTML = '<i class="fa fa-exclamation-triangle me-2"></i>Error';
        this.classList.remove("btn-success");
        this.classList.add("btn-danger");

        showNotification("Failed to add combo to cart", "error");

        // Reset button after 3 seconds
        setTimeout(() => {
          this.innerHTML = originalText;
          this.classList.remove("btn-danger");
          this.classList.add("btn-success");
          this.disabled = false;
        }, 3000);
      }
    });
  });
});

// Utility function to show notifications
function showNotification(message, type = "info") {
  // Try to use Odoo's notification system if available
  if (window.owl && window.owl.services && window.owl.services.notification) {
    window.owl.services.notification.add(message, { type });
    return;
  }

  // Fallback: create a simple notification
  const notification = document.createElement("div");
  notification.className = `alert alert-${
    type === "error" ? "danger" : type
  } position-fixed`;
  notification.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 300px;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
  notification.innerHTML = `
        <button type="button" class="btn-close" aria-label="Close"></button>
        ${message}
    `;

  document.body.appendChild(notification);

  // Animate in
  setTimeout(() => {
    notification.style.opacity = "1";
  }, 100);

  // Handle close button
  notification.querySelector(".btn-close").addEventListener("click", () => {
    removeNotification(notification);
  });

  // Auto remove after 5 seconds
  setTimeout(() => {
    removeNotification(notification);
  }, 5000);
}

function removeNotification(notification) {
  notification.style.opacity = "0";
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 300);
}

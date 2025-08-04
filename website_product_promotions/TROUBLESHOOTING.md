# Website Product Promotions - Troubleshooting Guide

## Common Issues and Solutions

### 1. "Order Reference (order_id) field is mandatory" Error

**Symptoms:**
- Error occurs when adding combo products to cart
- Error message: "Create/update: a mandatory field is not set. Field: Order Reference (order_id)"
- Happens when adding same combo twice or adding individual products after combo

**Root Cause:**
When the combo system splits sale order lines or creates new lines for combo pricing, the `order_id` field was not being properly set.

**Solution Applied:**
1. **Fixed in `sale_order.py`:** Added explicit `order_id` setting when creating new sale order lines
2. **Added safety checks:** Override `create` method in `SaleOrderLine` to ensure `order_id` is always set
3. **Enhanced error handling:** Added try-catch blocks to prevent combo processing from breaking cart functionality
4. **Context passing:** Use proper context when creating sale order lines

### 2. How to Test the Fix

1. **Create a combo** in backend (Sales > Configuration > Product Combos)
2. **Add combo to cart** once - should work normally
3. **Add same combo again** - should work without error
4. **Add individual products** from the combo - should work without error

### 3. Best Practices

**For Developers:**
1. Always check order state before applying combos
2. Use proper context when creating sale order lines
3. Add error handling around combo processing

**For Users:**
1. Clear cart if experiencing combo issues and re-add products
2. Check combo configuration in backend if discounts aren't applying

## Technical Details

### Key Files Modified

1. **`models/sale_order.py`:**
   - Fixed `_check_and_apply_combo` method to set `order_id`
   - Added error handling in `_cart_update` and `_apply_combo_discounts`
   - Enhanced `SaleOrderLine.create()` with safety checks

2. **`controllers/combo_controller.py`:**
   - Enhanced error handling in `add_combo_to_cart`
   - Added order state validation

### The Fix

```python
# Before (BROKEN):
new_line_vals.update({
    "product_uom_qty": used_qty,
    "discount": discount_rate,
    "combo_applied": True,
    "combo_id": combo.id,
})
self.env["sale.order.line"].create(new_line_vals)

# After (FIXED):
new_line_vals.update({
    "order_id": self.id,  # CRITICAL: Set order_id
    "product_uom_qty": used_qty,
    "discount": discount_rate,
    "combo_applied": True,
    "combo_id": combo.id,
})
self.env["sale.order.line"].with_context(
    default_order_id=self.id,
    active_order=self
).create(new_line_vals)
```

## Debugging

### Enable Debug Mode
1. Go to Settings > Developer Tools > Activate Developer Mode
2. Check server logs for detailed error messages
3. Use browser developer tools to check AJAX responses

### Common Log Messages
- `"Error in combo cart update"`: Check sale_order.py line processing
- `"Error applying combo discounts"`: Check combo configuration
- `"Error adding combo to cart"`: Check controller and order state

## Version History

### v17.0.1.0.1 (Current)
- Fixed order_id mandatory field error
- Added comprehensive error handling
- Improved stability for multiple combo scenarios

### v17.0.1.0.0
- Initial release with combo functionality

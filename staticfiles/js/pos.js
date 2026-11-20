// ==========================================================================
// POS TERMINAL INTERACTIVE ENGINE
// ==========================================================================

let cart = [];
let selectedPaymentMethod = 'cash';

document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  initBarcodeScanner();
  initCustomerQuickAdd();
  renderCart();

  const tenderedInput = document.getElementById('tendered-amount');
  if (tenderedInput) {
    tenderedInput.addEventListener('input', calculateChange);
  }

  const discountInput = document.getElementById('cart-discount-input');
  if (discountInput) {
    discountInput.addEventListener('input', () => {
      calculateTotals();
    });
  }
});

// Category filtering
function filterCategory(catId, btnElement) {
  document.querySelectorAll('.pos-cat-btn').forEach(btn => btn.classList.remove('active'));
  btnElement.classList.add('active');

  const tiles = document.querySelectorAll('.product-tile');
  tiles.forEach(tile => {
    const tileCat = tile.getAttribute('data-category');
    if (catId === 'all' || tileCat === catId) {
      tile.style.display = 'flex';
    } else {
      tile.style.display = 'none';
    }
  });
}

// Search bar filter
function initSearch() {
  const searchInput = document.getElementById('pos-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    const tiles = document.querySelectorAll('.product-tile');

    tiles.forEach(tile => {
      const name = tile.getAttribute('data-name').toLowerCase();
      const sku = tile.getAttribute('data-sku').toLowerCase();
      const barcode = (tile.getAttribute('data-barcode') || '').toLowerCase();

      if (name.includes(q) || sku.includes(q) || barcode.includes(q)) {
        tile.style.display = 'flex';
      } else {
        tile.style.display = 'none';
      }
    });
  });
}

// Barcode scanner auto-enter
function initBarcodeScanner() {
  const barcodeInput = document.getElementById('pos-barcode-input');
  if (!barcodeInput) return;

  barcodeInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const code = barcodeInput.value.trim();
      if (!code) return;

      const tile = document.querySelector(`.product-tile[data-barcode="${code}"]`) ||
                   document.querySelector(`.product-tile[data-sku="${code}"]`);

      if (tile) {
        tile.click();
        barcodeInput.value = '';
      } else {
        alert(`No product found with barcode/SKU: ${code}`);
      }
    }
  });
}

// Add product to cart
function addToCart(productId, name, price, maxStock) {
  if (maxStock <= 0) {
    alert(`Sorry, "${name}" is out of stock!`);
    return;
  }

  const existing = cart.find(item => item.productId === productId);
  if (existing) {
    if (existing.quantity >= maxStock) {
      alert(`Cannot add more than ${maxStock} in stock for "${name}".`);
      return;
    }
    existing.quantity += 1;
  } else {
    cart.push({
      productId: productId,
      name: name,
      price: parseFloat(price),
      quantity: 1,
      maxStock: maxStock
    });
  }

  renderCart();
}

// Adjust cart item quantity
function updateQty(productId, delta) {
  const item = cart.find(i => i.productId === productId);
  if (!item) return;

  const newQty = item.quantity + delta;
  if (newQty <= 0) {
    removeFromCart(productId);
    return;
  }
  if (newQty > item.maxStock) {
    alert(`Cannot exceed available stock of ${item.maxStock}.`);
    return;
  }

  item.quantity = newQty;
  renderCart();
}

// Remove item from cart
function removeFromCart(productId) {
  cart = cart.filter(i => i.productId !== productId);
  renderCart();
}

// Clear entire cart
function clearCart() {
  if (cart.length === 0) return;
  if (confirm('Clear all items from the current cart?')) {
    cart = [];
    renderCart();
  }
}

// Render Cart UI and calculate totals
function renderCart() {
  const container = document.getElementById('cart-items-container');
  const countBadge = document.getElementById('cart-count');
  const btnCheckout = document.getElementById('btn-checkout');

  if (!container) return;

  if (cart.length === 0) {
    container.innerHTML = `
      <div class="cart-empty">
        <i class="fa-solid fa-cart-shopping"></i>
        <p>No items in cart</p>
        <span style="font-size: 0.8rem; color: #94a3b8;">Click on products or scan barcodes to begin sale</span>
      </div>
    `;
    if (countBadge) countBadge.textContent = '0';
    if (btnCheckout) btnCheckout.disabled = true;
    calculateTotals();
    return;
  }

  let totalQty = 0;
  let html = '';

  cart.forEach(item => {
    totalQty += item.quantity;
    const itemTotal = (item.price * item.quantity).toFixed(2);

    html += `
      <div class="cart-item">
        <div class="cart-item-details">
          <div class="cart-item-name" title="${item.name}">${item.name}</div>
          <div class="cart-item-unit-price">Rs. ${item.price.toFixed(2)} each</div>
        </div>
        <div class="cart-item-qty-controls">
          <button class="qty-btn" onclick="updateQty(${item.productId}, -1)">
            <i class="fa-solid fa-minus"></i>
          </button>
          <span class="cart-item-qty">${item.quantity}</span>
          <button class="qty-btn" onclick="updateQty(${item.productId}, 1)">
            <i class="fa-solid fa-plus"></i>
          </button>
        </div>
        <div class="cart-item-total">Rs. ${itemTotal}</div>
        <button class="cart-item-remove" onclick="removeFromCart(${item.productId})" title="Remove item">
          <i class="fa-solid fa-trash-can"></i>
        </button>
      </div>
    `;
  });

  container.innerHTML = html;
  if (countBadge) countBadge.textContent = totalQty;
  if (btnCheckout) btnCheckout.disabled = false;

  calculateTotals();
}

function calculateTotals() {
  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  const discountInput = document.getElementById('cart-discount-input');
  let discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
  if (discount > subtotal) discount = subtotal;

  const total = Math.max(0, subtotal - discount);
  const tax = 0;

  const elSubtotal = document.getElementById('cart-subtotal');
  const elTax = document.getElementById('cart-tax');
  const elTotal = document.getElementById('cart-total');
  const modalTotal = document.getElementById('modal-pay-total');

  if (elSubtotal) elSubtotal.textContent = `Rs. ${subtotal.toFixed(2)}`;
  if (elTax) elTax.textContent = `Rs. ${tax.toFixed(2)}`;
  if (elTotal) elTotal.textContent = `Rs. ${total.toFixed(2)}`;
  if (modalTotal) modalTotal.textContent = `Rs. ${total.toFixed(2)}`;

  calculateChange();
}

// Select Payment Method
function setPaymentMethod(method) {
  selectedPaymentMethod = method;
  document.querySelectorAll('.btn-payment-method').forEach(b => b.classList.remove('active'));
  
  const activeBtn = document.getElementById(`pay-method-${method}`);
  if (activeBtn) activeBtn.classList.add('active');

  const cashSection = document.getElementById('cash-details-section');
  const cardSection = document.getElementById('card-details-section');
  const qrSection = document.getElementById('qr-details-section');

  if (cashSection) cashSection.style.display = method === 'cash' ? 'block' : 'none';
  if (cardSection) cardSection.style.display = method === 'card' ? 'block' : 'none';
  if (qrSection) qrSection.style.display = method === 'qr' ? 'block' : 'none';

  calculateChange();
}

function calculateChange() {
  if (selectedPaymentMethod !== 'cash') {
    const changeBox = document.getElementById('change-box');
    if (changeBox) changeBox.style.display = 'none';
    return;
  }

  const changeBox = document.getElementById('change-box');
  if (changeBox) changeBox.style.display = 'block';

  const totalStr = (document.getElementById('cart-total')?.textContent || '0').replace('Rs. ', '');
  const total = parseFloat(totalStr) || 0;
  const tenderedInput = document.getElementById('tendered-amount');
  const tendered = parseFloat(tenderedInput?.value) || total;

  const change = Math.max(0, tendered - total);
  const elChange = document.getElementById('change-amount');
  if (elChange) elChange.textContent = `Rs. ${change.toFixed(2)}`;
}

// Open Payment Modal
function openPaymentModal() {
  if (cart.length === 0) return;
  calculateTotals();
  
  const totalStr = (document.getElementById('cart-total')?.textContent || '0').replace('Rs. ', '');
  const total = parseFloat(totalStr) || 0;
  const tenderedInput = document.getElementById('tendered-amount');
  if (tenderedInput) tenderedInput.value = total.toFixed(2);

  setPaymentMethod('cash');
  openModal('payment-modal');
}

// Submit checkout sale via API
async function submitSale() {
  if (cart.length === 0) return;

  const btn = document.getElementById('btn-confirm-payment');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
  }

  const subtotalStr = (document.getElementById('cart-subtotal')?.textContent || '0').replace('Rs. ', '');
  const taxStr = (document.getElementById('cart-tax')?.textContent || '0').replace('Rs. ', '');
  const totalStr = (document.getElementById('cart-total')?.textContent || '0').replace('Rs. ', '');
  const discountInput = document.getElementById('cart-discount-input');

  const customerSelect = document.getElementById('cart-customer-select');
  const customerId = customerSelect ? customerSelect.value : null;

  const tenderedInput = document.getElementById('tendered-amount');
  const tendered = parseFloat(tenderedInput?.value) || parseFloat(totalStr);
  const change = Math.max(0, tendered - parseFloat(totalStr));

  const payload = {
    customer_id: customerId || null,
    payment_method: selectedPaymentMethod,
    subtotal: parseFloat(subtotalStr),
    discount: parseFloat(discountInput?.value || 0),
    tax: parseFloat(taxStr),
    total: parseFloat(totalStr),
    amount_tendered: tendered,
    change_amount: change,
    items: cart.map(i => ({
      product_id: i.productId,
      quantity: i.quantity,
      price: i.price
    }))
  };

  try {
    const res = await fetch('/sales/api/process-sale/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(payload)
    });

    let data;
    try {
      data = await res.json();
    } catch (error) {
      if (res.status === 403) {
        throw new Error('POS security token expired. Reload this page and try again.');
      }
      throw new Error(`Unexpected server response (${res.status}). Please reload and try again.`);
    }

    if (data.success) {
      closeModal('payment-modal');
      
      // Update receipt modal with dynamic sale info
      populateReceiptModal(data);
      openModal('receipt-modal');

      // Clear cart
      cart = [];
      renderCart();

      // Refresh product stock dynamically in DOM
      payload.items.forEach(sold => {
        const tile = document.querySelector(`.product-tile[data-id="${sold.product_id}"]`);
        if (tile) {
          const currentStock = parseInt(tile.getAttribute('data-stock')) - sold.quantity;
          tile.setAttribute('data-stock', currentStock);
          const stockSpan = tile.querySelector('.tile-stock');
          if (stockSpan) {
            stockSpan.textContent = `${currentStock} in stock`;
            if (currentStock <= 0) {
              tile.classList.add('out-of-stock');
              stockSpan.textContent = 'Out of Stock';
            }
          }
        }
      });

    } else {
      alert('Error completing sale: ' + (data.error || 'Unknown error'));
    }
  } catch (err) {
    alert('Server error while processing sale: ' + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-check"></i> Complete & Print Receipt';
    }
  }
}

// Populate Receipt Modal
function populateReceiptModal(saleData) {
  const elInv = document.getElementById('receipt-invoice-no');
  const elTotal = document.getElementById('receipt-total');
  const elChange = document.getElementById('receipt-change');
  const btnViewInvoice = document.getElementById('receipt-view-invoice');

  if (elInv) elInv.textContent = `#${saleData.invoice_number}`;
  if (elTotal) elTotal.textContent = `Rs. ${saleData.total.toFixed(2)}`;
  if (elChange) elChange.textContent = `Rs. ${saleData.change_amount.toFixed(2)}`;
  if (btnViewInvoice) btnViewInvoice.href = saleData.invoice_url;
}

// Print Receipt
function printReceipt() {
  const viewInvoiceBtn = document.getElementById('receipt-view-invoice');
  if (!viewInvoiceBtn || !viewInvoiceBtn.href) return;

  const invoiceUrl = viewInvoiceBtn.href + '?print=1';
  const popup = window.open(invoiceUrl, '_blank', 'noopener,noreferrer');

  if (!popup) {
    window.location.href = invoiceUrl;
  } else {
    popup.focus();
  }
}

// Quick Customer Modal in POS
function initCustomerQuickAdd() {
  const form = document.getElementById('quick-customer-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('quick-cust-name').value;
    const phone = document.getElementById('quick-cust-phone').value;
    const email = document.getElementById('quick-cust-email').value;

    try {
      const res = await fetch('/customers/api/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ name, phone, email })
      });

      const data = await res.json();
      if (data.success) {
        const select = document.getElementById('cart-customer-select');
        const opt = document.createElement('option');
        opt.value = data.customer.id;
        opt.textContent = `${data.customer.name} (${data.customer.phone || 'No phone'})`;
        opt.selected = true;
        select.appendChild(opt);

        closeModal('quick-customer-modal');
        form.reset();
      } else {
        alert('Error: ' + data.error);
      }
    } catch (err) {
      alert('Failed to add customer: ' + err.message);
    }
  });
}

# 🛡️ Simple POS — User, Block/Unblock & License Management Guide

Welcome to the comprehensive management guide for **Simple POS v3.15 Enterprise**. This document explains how to manage store users, block/unblock accounts, enforce software licenses, manage 14-day free trials, and upgrade subscription plans.

---

## 📌 Quick Access & Credentials

| Resource | URL | Credentials / Notes |
| :--- | :--- | :--- |
| **Admin Control Portal** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) | `admin` / `admin123` |
| **User & Trial Manager** | [http://127.0.0.1:8000/admin/accounts/user/](http://127.0.0.1:8000/admin/accounts/user/) | Full list, bulk actions & filters |
| **Software License Console** | [http://127.0.0.1:8000/accounts/activate-license/](http://127.0.0.1:8000/accounts/activate-license/) | License verification & unlock |
| **POS Terminal** | [http://127.0.0.1:8000/pos/](http://127.0.0.1:8000/pos/) | Cashier checkout screen |
| **Store Dashboard** | [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/) | Retail sales & stock dashboard |

---

## 🚫 1. User Block & Unblock Management

### How It Works:
- When a user or cashier is **Blocked**:
  1. Their `is_active` status is immediately set to `False`.
  2. Any active session is invalidated.
  3. When attempting to log in, the system displays an explicit alert:
     > `🛑 Account / Software Blocked: Your store access has been suspended by the system administrator.`
  4. The user cannot access the POS Terminal, Product Catalog, or Store Dashboard.
- When **Unblocked**:
  1. Their `is_active` status is restored to `True`.
  2. They can immediately log in and resume transactions without password resets.

### How to Block / Unblock a User:
1. Go to the Admin Dashboard: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
2. Scroll to the **User & License Management Console** table.
3. For any user:
   - Click the red **Block** button to immediately suspend access.
   - Click the green **Unblock** button to immediately restore access.
4. **Bulk Method**: Open [User List](http://127.0.0.1:8000/admin/accounts/user/), select multiple checkboxes, and choose `🚫 Deactivate Selected User Accounts` or `✅ Activate Selected User Accounts` from the Action dropdown.

---

## 🔑 2. Software Lock & License Key System

### License Key Architecture:
Each store account is automatically assigned a unique, cryptographic hardware-tied license key based on store credentials:
```
Format: SPOS-2026-XXXX-XXXX-XXXX
Example: SPOS-2026-8A3F-E29B-C410
```

### Master Lifetime Keys:
For permanent offline activations, the system recognizes master enterprise keys:
- `SPOS-LIFETIME-MASTER-2026` — Grants non-expiring permanent Enterprise access.

### Software Blocking & Revocation:
- **Block Software (Revoke License)**:
  - Inside the Admin Dashboard user row, click `Manage` &rarr; `Block Software (Revoke License)`.
  - This immediately sets the user's trial to expired and disables the login access.
- **Unblock Software (+14d License)**:
  - Inside the Admin Dashboard user row, click `Manage` &rarr; `Unblock Software (+14d Trial)`.
  - Re-enables the store account and issues a fresh 14-day validity period.

### License Activation Console:
Users whose license has expired or who receive a license renewal can visit:
[http://127.0.0.1:8000/accounts/activate-license/](http://127.0.0.1:8000/accounts/activate-license/)
- Paste their valid license key or renewal code.
- Click **Verify & Activate License**.
- The software verifies the key and automatically extends the subscription.

---

## ⚡ 2.5 Software License Key Generator Module

Simple POS includes an integrated **Cryptographic License Key Generator Module** directly accessible from the Admin Portal (`/admin/`) and under the database list (`/admin/accounts/softwarelicense/`).

### Key Serial Syntax & Architecture:
Generated keys follow an industrial standard segmented serial architecture:
```
SPOS-{PLAN_CODE}-{DURATION_CODE}-{HASH_1}-{HASH_2}-{HASH_3}
```

| Segment | Possible Values | Meaning |
| :--- | :--- | :--- |
| **Vendor Prefix** | `SPOS` | Simple POS System Identity |
| **Plan Code** | `STR` / `BUS` / `ENT` | Starter, Business, or Enterprise |
| **Duration Code** | `14D`, `1M`, `3M`, `6M`, `1Y`, `LIFE` | Validity length granted upon redemption |
| **Hash Blocks** | Hex tokens (e.g. `9A2F-C810-7B4D`) | Cryptographically random unique entropy |

#### Examples of Generated Keys:
- 🏢 `SPOS-BUS-1Y-4B8C-9F12-7A3D` — Business Edition, 1 Year (Annual) License
- 👑 `SPOS-ENT-LIFE-A1C9-E4D2-88F0` — Enterprise Multi-Branch, Lifetime License
- 🛒 `SPOS-STR-3M-2F11-8C90-5E4A` — Starter Edition, 3 Months Access
- ⏳ `SPOS-BUS-14D-6D7A-0E33-91B2` — Business Edition, 14-Day Evaluation Key

### How to Generate a New License Key:
1. Open the Admin Control Portal: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
2. In the top metric card or in the **Software License Key Generator Module** section, click **"⚡ Generate License Key"**.
3. In the interactive modal:
   - **Subscription Tier**: Choose Starter, Business, or Enterprise.
   - **Duration**: Choose 14 Days, 1 Month, 3 Months, 6 Months, 1 Year, or Lifetime.
   - **Client / Store Name**: Enter the client or store name (e.g. *"Kathmandu Fresh Mart"*).
   - **Assign to Existing Account (Optional)**: Select an existing store account from the dropdown.
   - **Auto-Activate Checkbox**: If checked, automatically applies the plan and extends the store's validity immediately without needing manual entry.
   - **Invoicing Notes (Optional)**: Enter invoice number, eSewa transaction code, or bank receipt info.
   - Observe the **Live Serial Key Format Preview** updating dynamically.
4. Click **"⚡ Generate & Issue License Key"**.
5. The key is generated, recorded in the database, and added to the dashboard table.
6. Click the **Copy** button to copy the key directly to your clipboard to send to the client via SMS, email, or invoice.

### Superadmin License Key Type Controls

The Admin Dashboard includes a **License Key Type Controls** table for
superusers. Each plan and duration combination (for example, Starter + 1 Year
or Enterprise + Lifetime) can be enabled or disabled independently.

- Enabled combinations appear in the license generator.
- Disabled combinations cannot be generated, and existing unredeemed keys of
  that combination cannot be redeemed.
- Keys already redeemed retain their account access; disabling a type does not
  revoke an active subscription.
- The full matrix is also available under **Accounts → License Key Types** in
  Django Admin. Options cannot be added or deleted there; supported plans and
  durations are maintained by the application.
- Only Django superusers can change these settings. Store-level `admin` roles
  cannot modify platform license types.

If every combination is disabled, license generation remains unavailable until
a superuser enables at least one type.

### Key Lifecycle & Redemption:
- **Available to Redeem**: Key is generated and valid. Anyone with the key can redeem it at `/accounts/activate-license/`.
- **Redeemed**: The key has been bound to a user account. The redemption date and username are recorded. Keys cannot be reused by other stores.
- **Revoked / Inactive**: Admin clicked "Revoke". If a user attempts to activate a revoked key, the system rejects it with an error.
- **Reactivate / Delete**: Revoked keys can be restored with 1 click or permanently purged from the database.

---

## ⏳ 3. 14-Day Free Trial Management

### Status Indicators:
| Badge | Condition | System Action |
| :--- | :--- | :--- |
| 🟢 **Active (X days left)** | `days_left > 3` | Full access to POS and dashboard |
| 🟠 **Ending Soon (1-3 days left)** | `1 <= days_left <= 3` | Reminder badge shown in admin |
| 🔴 **Trial Expired** | `days_left <= 0` | Access prompt shown; requires license extension or upgrade |
| ⚪ **Lifetime License** | `trial_ends_at is None` | Permanent non-expiring license |

### Quick Trial Adjustments:
From the Admin Console (`/admin/`):
- Click `Manage` &rarr; `Extend 14-Day Free Access` (+14 Days)
- Click `Manage` &rarr; `Add +30 Days Access` (+30 Days)
- Click `Manage` &rarr; `Set Permanent Lifetime License` (No expiry)
- Click `Manage` &rarr; `Expire Trial Now` (Force expiration)

---

## 💎 4. Subscription Plans & Upgrades

Simple POS offers three distinct subscription tiers:

| Feature / Limit | 🔹 Starter (Rs. 999/mo) | 🟣 Business (Rs. 2,499/mo) | 🟡 Enterprise (Custom) |
| :--- | :---: | :---: | :---: |
| **Target Stores** | Grocery Kiosks, Cafes | Supermarkets, Boutiques | Multi-Branch Franchises |
| **Cashier Terminals** | 1 POS Terminal | Unlimited Terminals | Unlimited Multi-Register |
| **Product Limit** | Up to 500 Products | Unlimited Products | Unlimited Products |
| **Barcode & Thermal** | 80mm / 58mm Printers | Yes + Scanner Wedge | Yes + Custom Branding |
| **Inventory & POs** | Basic Stock Count | Warehouse & Supplier POs | Multi-Warehouse Cloud Sync |
| **Sales & Net Profit** | Daily Shift Invoices | True Net Profit & COGS | Full Audit & Tax Export |
| **Weighing Scales** | ❌ | ❌ | Electronic Serial / USB Scales |
| **Support SLA** | Standard Email | Priority WhatsApp | 24/7 VIP Phone Support |

### Upgrading a Store's Plan:
In the Admin Console (`/admin/`):
1. Locate the store or user row in the table.
2. Click **Manage** &rarr; Select **Starter**, **Business**, or **Enterprise**.
3. The store's tier updates instantly without restarting the server.
4. The Monthly Recurring Revenue (MRR) chart on the dashboard recalculates automatically.

---

## 📊 5. Executive SaaS Metrics & Reports

On the main Admin Dashboard (`/admin/`):
- **Total Users & Stores**: Dynamic breakdown of store owners (Admins), inventory managers, and cashiers, with a dedicated counter for Blocked Accounts.
- **Software Sales (MRR & ARR)**:
  $$\text{MRR} = (\text{Starters} \times 999) + (\text{Businesses} \times 2499) + (\text{Enterprises} \times 4999)$$
  $$\text{ARR} = \text{MRR} \times 12$$
- **Software Sales & Signups Growth Chart**: Interactive 6-month visual progression line graph with monthly revenue trends.
- **Plan Distribution Doughnut Chart**: Visual breakdown of store subscriptions across Starter, Business, and Enterprise.

---

## 🛠️ 6. Emergency Recovery Commands (PowerShell)

### Unblock all admin accounts:
```powershell
python manage.py shell -c "from accounts.models import User; User.objects.filter(role='admin').update(is_active=True); print('Admins unblocked!')"
```

### Grant lifetime license to admin:
```powershell
python manage.py shell -c "from accounts.models import User; User.objects.filter(role='admin').update(trial_ends_at=None, plan='enterprise'); print('Lifetime Enterprise license granted!')"
```

### Create an instant database snapshot:
```powershell
Copy-Item db.sqlite3 ("backup_" + (Get-Date -Format "yyyyMMdd_HHmm") + ".sqlite3")
```

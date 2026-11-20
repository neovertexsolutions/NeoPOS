# Superadmin Feature Controls and Product Roadmap

## Purpose

Give SahajPOS superadmins a safe, auditable way to control which product
features are available globally, by subscription plan, and for an individual
store—without deploying code for every access change.

The broader roadmap is a proposal; see the implementation status below for
the license-type controls being added now.

## Implementation status

The current change implements superadmin enable/disable controls for the
existing plan-and-duration license-key combinations. This is a focused first
step; the broader feature catalogue, per-store feature entitlements, usage
limits, rollout controls, and audit history below remain proposed work.

## Existing project context reviewed

The existing [User and License Management guide](./USER_AND_LICENSE_MANAGEMENT.md)
documents account blocking, trial extensions, license issuing, three plans
(Starter, Business, Enterprise), payment review, and administrative metrics.
The application currently has a custom Django admin, a `User.plan` field,
license and upgrade-request models, and middleware that checks whether a
user's account has active access.

The repository did not contain a separate PRD or product requirements document.
The plan comparison in the existing guide is therefore the available product
baseline; confirm the intended plan entitlements and limits before making them
enforceable.

## Recommended feature-control capabilities

### 1. Feature catalogue

Maintain a centrally managed list of features, each with a stable key, display
name, description, category, and active state. Suggested initial entries:

| Feature key | Suggested control |
| --- | --- |
| `pos.multi_register` | Number of concurrent/register terminals |
| `catalog.product_limit` | Maximum active products |
| `inventory.advanced` | Advanced stock controls and adjustments |
| `purchases.purchase_orders` | Purchase orders and supplier workflows |
| `reports.profit` | Profit and COGS reports |
| `reports.tax_export` | Tax and audit exports |
| `store.multi_branch` | Multiple branches / stores |
| `hardware.custom_branding` | Custom receipt and interface branding |
| `hardware.scale_integration` | Weighing-scale integrations |
| `support.priority` | Priority support entitlement |

Keep limits (such as product or register counts) as typed values, rather than
representing every entitlement as only on/off.

### 2. Plan entitlements

Let superadmins assign each catalogue feature to Starter, Business, and
Enterprise, including its limit where relevant. Show a plan comparison preview
before saving. Existing paid accounts should retain their current plan; changes
to plan entitlements should affect access according to a clearly documented
effective-time policy.

### 3. Per-store overrides

Allow superadmins to grant or disable a feature for one store, with an optional
expiry date and required reason. This supports trials, pilots, support
exceptions, and negotiated Enterprise contracts without changing the plan for
every customer.

### 4. Global kill switch and rollout

Provide a global on/off switch for incidents or maintenance, plus an optional
percentage rollout for staged releases. A global disable must take precedence
over plan access and store overrides. Display a clear disabled/maintenance
message to affected users rather than leaving broken navigation or unexplained
errors.

### 5. Limits and usage

Configure caps such as products, registers, branches, and users by plan. Show
current usage and cap in the admin and store UI. Warn near the limit; block
only the operation that exceeds it, with a clear upgrade path. Never silently
delete or truncate customer data when a cap is lowered.

### 6. Audit history and safe administration

Record who changed a flag or entitlement, what changed, when, why, and the
previous and new values. Provide filters and search for this history. Restrict
configuration changes to Django superusers (not merely store users whose role
is `admin`); consider a separate read-only support role later. Require a reason
for overrides and destructive or high-impact changes.

## Implementation principles

1. **One server-side authorization path:** add a shared entitlement service
   (for example, `has_feature(user, feature_key)` and
   `get_feature_limit(user, feature_key)`). Use it in views and APIs; hiding a
   menu item in a template is not access control.
2. **Separate subscription access from feature entitlement:** keep account
   active/trial/expiry checks distinct from plan feature checks so an active
   account can still have plan-specific access.
3. **Consistent UI:** use the same entitlement service to hide or explain
   unavailable navigation and controls, while enforcing access at the endpoint.
4. **Safe defaults:** unknown or inactive feature keys must not grant access.
   Admin changes should be validated and transactional.
5. **Cache safely:** if entitlements are cached, invalidate them immediately
   after a superadmin change; document any maximum propagation delay.
6. **Do not change plan rules implicitly:** migrate existing plan entitlements
   from an approved product matrix and test the behavior for current accounts
   before enabling enforcement.

## Suggested data model

Use normalized records rather than a collection of scattered plan checks:

- **Feature** — stable key, name, description, category, type, global enabled
  state, and optional rollout percentage.
- **PlanFeature** — feature, plan, enabled state, and optional typed limit.
- **StoreFeatureOverride** — store/user, feature, enabled state or limit,
  effective and expiry dates, reason, and creating superadmin.
- **FeatureAuditEvent** — actor, affected plan/store/feature, old and new
  values, reason, and timestamp.

Adapt the store relationship to the application's actual tenant model. At
present, the codebase centers on `User` and `store_name`; confirm whether one
account represents one store before building multi-branch controls.

## Proposed superadmin experience

Add a **Feature Controls** area to the existing admin portal:

- **Overview:** enabled features, active overrides, rollout state, and recently
  changed controls.
- **Feature catalogue:** search/filter, global availability, and rollout.
- **Plans:** side-by-side plan matrix with limits and a change preview.
- **Stores:** search a store, inspect plan and current usage, grant/revoke
  temporary exceptions, and see override expiry.
- **Audit log:** searchable, read-only history of all entitlement changes.

Before applying a global disable or changing a plan matrix, show the number of
affected stores and require confirmation. Provide a rollback path through
audited changes rather than silently overwriting history.

## Delivery roadmap

### Phase 0 — Confirm requirements

- Obtain or create the missing PRD and approve a canonical plan/feature matrix.
- Confirm plan limits, trial behavior, whether overrides can exceed plan caps,
  and whether changes take effect immediately or at renewal.
- Confirm whether a store is one user account or can contain multiple users and
  branches.

**Exit criteria:** signed-off feature list, limit definitions, and migration
policy for existing subscribers.

### Phase 1 — Core entitlements

- Add the feature catalogue and plan-entitlement records.
- Add one shared, tested entitlement service.
- Convert a small set of high-value features (for example, product limit,
  advanced reports, and multi-register) from hard-coded assumptions to this
  service.
- Add server-side checks and consistent unavailable-feature messages.

**Exit criteria:** plan access is enforced consistently in views and UI, with
tests for every plan and expired/inactive users.

### Phase 2 — Superadmin controls

- Add the plan matrix editor and global kill switch.
- Add per-store overrides with expiry, reason, confirmation, and audit events.
- Add cache invalidation and admin-facing impact previews.

**Exit criteria:** only authorized superusers can modify controls; every change
is auditable and effective within the documented propagation time.

### Phase 3 — Usage limits and customer experience

- Enforce product, register, user, and branch limits at write operations.
- Add usage meters, near-limit warnings, and an upgrade path.
- Add a store-facing feature/plan explanation page.

**Exit criteria:** limit enforcement is race-safe and lowering limits never
deletes existing records.

### Phase 4 — SaaS operations and growth

- Add scheduled entitlement changes, trial feature bundles, and controlled
rollouts.
- Add feature adoption and conversion reporting.
- Add customer lifecycle workflows: trial reminders, renewal notices, failed
payment follow-up, and churn feedback.

**Exit criteria:** scheduled changes are visible, reversible, audited, and
covered by tests; analytics use trustworthy event and billing data.

## Other future product priorities

After the entitlement foundation, consider these in order:

1. **Reliable backups and restore drills** — automated, encrypted backups,
   retention policy, and documented recovery objectives.
2. **Multi-user store management** — invite staff, role-based permissions, and
   clear separation between platform superadmins and store admins.
3. **Multi-branch operations** — branch-scoped stock, registers, transfers, and
   consolidated reporting.
4. **Payments and subscription lifecycle** — payment reconciliation, invoices,
   renewal dates, refunds/credit notes, and clear subscription states.
5. **Integrations** — accounting export, payment providers, barcode hardware,
   and printer/device compatibility checks.
6. **Operational visibility** — audit trails for sensitive store actions,
   application error monitoring, and support diagnostics that do not expose
   customer secrets.
7. **Offline resilience** — resilient checkout during connectivity loss,
   conflict-aware synchronization, and explicit recovery status.

## Key risks to resolve before implementation

- The documented plan matrix may not match all currently shipped behavior.
- Existing plan, payment, license, and trial logic is distributed across
  account/admin flows; entitlement checks must not bypass or contradict it.
- User-level accounts may not yet model a distinct store/tenant boundary,
  limiting safe store-wide overrides.
- A feature hidden only in the UI can still be reached directly; enforce every
  entitlement on the server.
- Lowering limits or disabling a feature must preserve existing data and give
  users a clear export or resolution path.

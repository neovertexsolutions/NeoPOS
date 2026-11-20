-- ============================================================
-- SIMPLE POS SYSTEM
-- COMPLETE MYSQL / MARIADB DATABASE
-- ============================================================

-- ------------------------------------------------------------
-- DATABASE
-- ------------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;


-- ============================================================
-- DJANGO CONTENT TYPES
-- Required because accounts_user uses Django permissions/groups
-- ============================================================

DROP TABLE IF EXISTS support_ticketreply;
DROP TABLE IF EXISTS support_ticket;

DROP TABLE IF EXISTS expenses_expense;
DROP TABLE IF EXISTS expenses_expensecategory;

DROP TABLE IF EXISTS purchases_purchaseitem;
DROP TABLE IF EXISTS purchases_purchase;

DROP TABLE IF EXISTS inventory_stockmovement;

DROP TABLE IF EXISTS sales_saleitem;
DROP TABLE IF EXISTS sales_sale;

DROP TABLE IF EXISTS products_product;
DROP TABLE IF EXISTS products_category;

DROP TABLE IF EXISTS customers_customer;
DROP TABLE IF EXISTS suppliers_supplier;

DROP TABLE IF EXISTS accounts_user_user_permissions;
DROP TABLE IF EXISTS accounts_user_groups;
DROP TABLE IF EXISTS accounts_user;

DROP TABLE IF EXISTS auth_group_permissions;
DROP TABLE IF EXISTS auth_group;
DROP TABLE IF EXISTS auth_permission;

DROP TABLE IF EXISTS django_content_type;


-- ============================================================
-- DJANGO CONTENT TYPE
-- ============================================================

CREATE TABLE django_content_type (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_content_type_app_model (
        app_label,
        model
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- DJANGO PERMISSION
-- ============================================================

CREATE TABLE auth_permission (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    content_type_id INT UNSIGNED NOT NULL,
    codename VARCHAR(100) NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_permission_content_codename (
        content_type_id,
        codename
    ),

    KEY idx_permission_content_type (
        content_type_id
    ),

    CONSTRAINT fk_permission_content_type
        FOREIGN KEY (content_type_id)
        REFERENCES django_content_type(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- DJANGO GROUP
-- ============================================================

CREATE TABLE auth_group (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_group_name (name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- DJANGO GROUP PERMISSIONS
-- ============================================================

CREATE TABLE auth_group_permissions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    group_id INT UNSIGNED NOT NULL,
    permission_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_group_permission (
        group_id,
        permission_id
    ),

    KEY idx_group_permissions_group (
        group_id
    ),

    KEY idx_group_permissions_permission (
        permission_id
    ),

    CONSTRAINT fk_group_permissions_group
        FOREIGN KEY (group_id)
        REFERENCES auth_group(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_group_permissions_permission
        FOREIGN KEY (permission_id)
        REFERENCES auth_permission(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- ACCOUNTS / USERS
-- ============================================================

CREATE TABLE accounts_user (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    password VARCHAR(128) NOT NULL,

    last_login DATETIME NULL,

    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,

    username VARCHAR(150) NOT NULL,

    first_name VARCHAR(150) NOT NULL DEFAULT '',

    last_name VARCHAR(150) NOT NULL DEFAULT '',

    email VARCHAR(254) NOT NULL DEFAULT '',

    is_staff BOOLEAN NOT NULL DEFAULT FALSE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    date_joined DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    role VARCHAR(20) NOT NULL DEFAULT 'cashier',

    phone VARCHAR(20) NULL,

    address TEXT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_user_username (
        username
    ),

    KEY idx_user_email (
        email
    ),

    KEY idx_user_role (
        role
    ),

    KEY idx_user_is_active (
        is_active
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- USER GROUPS
-- ============================================================

CREATE TABLE accounts_user_groups (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    user_id BIGINT UNSIGNED NOT NULL,

    group_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_user_group (
        user_id,
        group_id
    ),

    KEY idx_user_groups_user (
        user_id
    ),

    KEY idx_user_groups_group (
        group_id
    ),

    CONSTRAINT fk_user_groups_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_groups_group
        FOREIGN KEY (group_id)
        REFERENCES auth_group(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- USER PERMISSIONS
-- ============================================================

CREATE TABLE accounts_user_user_permissions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    user_id BIGINT UNSIGNED NOT NULL,

    permission_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_user_permission (
        user_id,
        permission_id
    ),

    KEY idx_user_permissions_user (
        user_id
    ),

    KEY idx_user_permissions_permission (
        permission_id
    ),

    CONSTRAINT fk_user_permissions_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_permissions_permission
        FOREIGN KEY (permission_id)
        REFERENCES auth_permission(id)
        ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- PRODUCTS
-- ============================================================

CREATE TABLE products_category (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(100) NOT NULL,

    description TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    UNIQUE KEY uq_category_name (
        name
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- PRODUCTS
-- ============================================================

CREATE TABLE products_product (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(200) NOT NULL,

    sku VARCHAR(50) NOT NULL,

    barcode VARCHAR(50) NULL,

    purchase_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    selling_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    stock INT NOT NULL DEFAULT 0,

    minimum_stock INT NOT NULL DEFAULT 0,

    image VARCHAR(255) NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    category_id BIGINT UNSIGNED NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_product_sku (
        sku
    ),

    KEY idx_product_barcode (
        barcode
    ),

    KEY idx_product_category (
        category_id
    ),

    KEY idx_product_active (
        is_active
    ),

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES products_category(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT chk_product_stock
        CHECK (stock >= 0),

    CONSTRAINT chk_product_minimum_stock
        CHECK (minimum_stock >= 0),

    CONSTRAINT chk_product_purchase_price
        CHECK (purchase_price >= 0),

    CONSTRAINT chk_product_selling_price
        CHECK (selling_price >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE customers_customer (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(150) NOT NULL,

    phone VARCHAR(30) NULL,

    email VARCHAR(254) NULL,

    address TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    KEY idx_customer_phone (
        phone
    ),

    KEY idx_customer_email (
        email
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- SUPPLIERS
-- ============================================================

CREATE TABLE suppliers_supplier (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(150) NOT NULL,

    phone VARCHAR(30) NULL,

    email VARCHAR(254) NULL,

    address TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    KEY idx_supplier_phone (
        phone
    ),

    KEY idx_supplier_email (
        email
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- INVENTORY / STOCK MOVEMENT
-- ============================================================

CREATE TABLE inventory_stockmovement (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    movement_type VARCHAR(20) NOT NULL,

    quantity INT NOT NULL,

    previous_stock INT NOT NULL,

    new_stock INT NOT NULL,

    reference VARCHAR(100) NULL,

    notes TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_by_id BIGINT UNSIGNED NULL,

    product_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    KEY idx_stockmovement_created_by (
        created_by_id
    ),

    KEY idx_stockmovement_product (
        product_id
    ),

    KEY idx_stockmovement_type (
        movement_type
    ),

    KEY idx_stockmovement_created_at (
        created_at
    ),

    CONSTRAINT fk_stockmovement_user
        FOREIGN KEY (created_by_id)
        REFERENCES accounts_user(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_stockmovement_product
        FOREIGN KEY (product_id)
        REFERENCES products_product(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT chk_stockmovement_quantity
        CHECK (quantity >= 0),

    CONSTRAINT chk_stockmovement_previous_stock
        CHECK (previous_stock >= 0),

    CONSTRAINT chk_stockmovement_new_stock
        CHECK (new_stock >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- SALES
-- ============================================================

CREATE TABLE sales_sale (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    invoice_number VARCHAR(50) NOT NULL,

    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    discount DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    tax DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    total DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    payment_method VARCHAR(20) NOT NULL,

    amount_tendered DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    change_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    notes TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    cashier_id BIGINT UNSIGNED NULL,

    customer_id BIGINT UNSIGNED NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_sale_invoice (
        invoice_number
    ),

    KEY idx_sale_cashier (
        cashier_id
    ),

    KEY idx_sale_customer (
        customer_id
    ),

    KEY idx_sale_created_at (
        created_at
    ),

    KEY idx_sale_payment_method (
        payment_method
    ),

    CONSTRAINT fk_sale_cashier
        FOREIGN KEY (cashier_id)
        REFERENCES accounts_user(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_sale_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers_customer(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT chk_sale_subtotal
        CHECK (subtotal >= 0),

    CONSTRAINT chk_sale_discount
        CHECK (discount >= 0),

    CONSTRAINT chk_sale_tax
        CHECK (tax >= 0),

    CONSTRAINT chk_sale_total
        CHECK (total >= 0),

    CONSTRAINT chk_sale_amount_tendered
        CHECK (amount_tendered >= 0),

    CONSTRAINT chk_sale_change
        CHECK (change_amount >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- SALE ITEMS
-- ============================================================

CREATE TABLE sales_saleitem (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    product_name VARCHAR(200) NOT NULL,

    quantity INT NOT NULL,

    unit_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    total DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    product_id BIGINT UNSIGNED NULL,

    sale_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    KEY idx_saleitem_product (
        product_id
    ),

    KEY idx_saleitem_sale (
        sale_id
    ),

    CONSTRAINT fk_saleitem_product
        FOREIGN KEY (product_id)
        REFERENCES products_product(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_saleitem_sale
        FOREIGN KEY (sale_id)
        REFERENCES sales_sale(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT chk_saleitem_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_saleitem_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT chk_saleitem_total
        CHECK (total >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- PURCHASES
-- ============================================================

CREATE TABLE purchases_purchase (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    reference_no VARCHAR(50) NOT NULL,

    total DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    payment_status VARCHAR(20) NOT NULL,

    notes TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_by_id BIGINT UNSIGNED NULL,

    supplier_id BIGINT UNSIGNED NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_purchase_reference (
        reference_no
    ),

    KEY idx_purchase_created_by (
        created_by_id
    ),

    KEY idx_purchase_supplier (
        supplier_id
    ),

    KEY idx_purchase_created_at (
        created_at
    ),

    CONSTRAINT fk_purchase_created_by
        FOREIGN KEY (created_by_id)
        REFERENCES accounts_user(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_purchase_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers_supplier(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT chk_purchase_total
        CHECK (total >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- PURCHASE ITEMS
-- ============================================================

CREATE TABLE purchases_purchaseitem (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    quantity INT NOT NULL,

    purchase_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    total DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    product_id BIGINT UNSIGNED NOT NULL,

    purchase_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    KEY idx_purchaseitem_product (
        product_id
    ),

    KEY idx_purchaseitem_purchase (
        purchase_id
    ),

    CONSTRAINT fk_purchaseitem_product
        FOREIGN KEY (product_id)
        REFERENCES products_product(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_purchaseitem_purchase
        FOREIGN KEY (purchase_id)
        REFERENCES purchases_purchase(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT chk_purchaseitem_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_purchaseitem_price
        CHECK (purchase_price >= 0),

    CONSTRAINT chk_purchaseitem_total
        CHECK (total >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- EXPENSE CATEGORIES
-- ============================================================

CREATE TABLE expenses_expensecategory (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(100) NOT NULL,

    description TEXT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_expense_category_name (
        name
    )
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- EXPENSES
-- ============================================================

CREATE TABLE expenses_expense (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    description TEXT NULL,

    date DATE NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    category_id BIGINT UNSIGNED NOT NULL,

    created_by_id BIGINT UNSIGNED NULL,

    PRIMARY KEY (id),

    KEY idx_expense_category (
        category_id
    ),

    KEY idx_expense_created_by (
        created_by_id
    ),

    KEY idx_expense_date (
        date
    ),

    CONSTRAINT fk_expense_category
        FOREIGN KEY (category_id)
        REFERENCES expenses_expensecategory(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_expense_created_by
        FOREIGN KEY (created_by_id)
        REFERENCES accounts_user(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT chk_expense_amount
        CHECK (amount >= 0)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- SUPPORT TICKETS
-- ============================================================

CREATE TABLE support_ticket (
    id CHAR(32) NOT NULL,

    ticket_number VARCHAR(20) NOT NULL,

    subject VARCHAR(255) NOT NULL,

    description TEXT NOT NULL,

    category VARCHAR(50) NOT NULL,

    priority VARCHAR(20) NOT NULL,

    status VARCHAR(20) NOT NULL,

    attachment VARCHAR(255) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    user_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    UNIQUE KEY uq_ticket_number (
        ticket_number
    ),

    KEY idx_ticket_user (
        user_id
    ),

    KEY idx_ticket_status (
        status
    ),

    KEY idx_ticket_priority (
        priority
    ),

    KEY idx_ticket_created_at (
        created_at
    ),

    CONSTRAINT fk_ticket_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- SUPPORT TICKET REPLIES
-- ============================================================

CREATE TABLE support_ticketreply (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    message TEXT NOT NULL,

    attachment VARCHAR(255) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    ticket_id CHAR(32) NOT NULL,

    user_id BIGINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),

    KEY idx_ticketreply_ticket (
        ticket_id
    ),

    KEY idx_ticketreply_user (
        user_id
    ),

    KEY idx_ticketreply_created_at (
        created_at
    ),

    CONSTRAINT fk_ticketreply_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES support_ticket(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_ticketreply_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- RESTORE FOREIGN KEY CHECKING
-- ============================================================

SET FOREIGN_KEY_CHECKS = 1;


-- ============================================================
-- DONE
-- ============================================================
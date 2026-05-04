-- ============================================================
-- Loan Data Quality Control System
-- Table Definitions
-- Author: Chaoda Jiang | UC San Diego, MS Business Analytics
--
-- Account Code Reference:
--   1xxx = Assets
--   4xxx = Revenue / Income
--   6xxx = Other Income (Gains)
--   7xxx = Expenses / Losses
-- ============================================================


-- ------------------------------------------------------------
-- 1. Loan Transactions
-- ------------------------------------------------------------
CREATE TABLE loan_transactions (
    loan_id                VARCHAR(20)     NOT NULL,
    disbursement_id        VARCHAR(30)     NOT NULL,
    customer_id            VARCHAR(20)     NOT NULL,
    source_system          VARCHAR(30)     NOT NULL,
    transaction_date       DATE            NOT NULL,
    accounting_date        DATE            NOT NULL,
    disbursement_amount    DECIMAL(15, 2)  NOT NULL,
    interest_rate          DECIMAL(6, 4)   NOT NULL,
    term_months            INT             NOT NULL,
    loan_status            VARCHAR(20)     NOT NULL,
    region                 VARCHAR(5),
    charge_off_date        DATE,
    charge_off_amount      DECIMAL(15, 2),

    CONSTRAINT pk_loan_transactions     PRIMARY KEY (disbursement_id),
    CONSTRAINT uq_loan_id               UNIQUE (loan_id),
    CONSTRAINT ck_disbursement_amount   CHECK (disbursement_amount > 0),
    CONSTRAINT ck_interest_rate         CHECK (interest_rate > 0 AND interest_rate <= 0.36),
    CONSTRAINT ck_term_months           CHECK (term_months > 0),
    CONSTRAINT ck_source_system         CHECK (source_system IN ('internal_core', 'partner_platform')),
    CONSTRAINT ck_loan_status           CHECK (loan_status IN ('active', 'closed', 'defaulted', 'written_off')),
    CONSTRAINT ck_disbursement_id_fmt   CHECK (disbursement_id LIKE 'DISB______________')
);


-- ------------------------------------------------------------
-- 2. Repayment Schedule
-- ------------------------------------------------------------
CREATE TABLE repayment_schedule (
    loan_id                     VARCHAR(20)     NOT NULL,
    installment_no              INT             NOT NULL,
    due_date                    DATE            NOT NULL,
    loan_overdue_flag           BOOLEAN         NOT NULL DEFAULT FALSE,
    installment_overdue_flag    BOOLEAN         NOT NULL DEFAULT FALSE,
    installment_settled_flag    BOOLEAN         NOT NULL DEFAULT FALSE,
    due_principal               DECIMAL(15, 2)  NOT NULL,
    paid_principal              DECIMAL(15, 2)  NOT NULL DEFAULT 0,
    due_interest                DECIMAL(15, 2)  NOT NULL,
    paid_interest               DECIMAL(15, 2)  NOT NULL DEFAULT 0,
    overdue_days                INT             NOT NULL DEFAULT 0,
    overdue_interest_due        DECIMAL(15, 2)  NOT NULL DEFAULT 0,
    overdue_interest_paid       DECIMAL(15, 2)  NOT NULL DEFAULT 0,

    CONSTRAINT pk_repayment_schedule    PRIMARY KEY (loan_id, installment_no),
    CONSTRAINT fk_schedule_loan         FOREIGN KEY (loan_id) REFERENCES loan_transactions(loan_id),
    CONSTRAINT ck_due_principal         CHECK (due_principal >= 0),
    CONSTRAINT ck_paid_principal        CHECK (paid_principal >= 0),
    CONSTRAINT ck_due_interest          CHECK (due_interest >= 0),
    CONSTRAINT ck_paid_interest         CHECK (paid_interest >= 0),
    CONSTRAINT ck_overdue_days          CHECK (overdue_days >= 0),
    CONSTRAINT ck_overdue_interest_due  CHECK (overdue_interest_due >= 0),
    CONSTRAINT ck_overdue_interest_paid CHECK (overdue_interest_paid >= 0)
);


-- ------------------------------------------------------------
-- 3. Repayment Transactions
-- ------------------------------------------------------------
CREATE TABLE repayment_transactions (
    repayment_transaction_id    VARCHAR(40)     NOT NULL,
    loan_id                     VARCHAR(20)     NOT NULL,
    transaction_date            DATE            NOT NULL,
    accounting_date             DATE            NOT NULL,
    repayment_total_amount      DECIMAL(15, 2)  NOT NULL,
    repayment_principal         DECIMAL(15, 2)  NOT NULL,
    repayment_interest          DECIMAL(15, 2)  NOT NULL,
    repayment_overdue_interest  DECIMAL(15, 2)  NOT NULL DEFAULT 0,
    payment_status              VARCHAR(20)     NOT NULL,

    CONSTRAINT pk_repayment_transactions    PRIMARY KEY (repayment_transaction_id),
    CONSTRAINT fk_repay_loan                FOREIGN KEY (loan_id) REFERENCES loan_transactions(loan_id),
    CONSTRAINT ck_repay_total               CHECK (repayment_total_amount > 0),
    CONSTRAINT ck_repay_components          CHECK (repayment_principal >= 0 AND repayment_interest >= 0),
    CONSTRAINT ck_payment_status            CHECK (payment_status IN ('successful', 'failed', 'reversed'))
);


-- ------------------------------------------------------------
-- 4. Accounting Entries
-- ------------------------------------------------------------
CREATE TABLE accounting_entries (
    entry_id            VARCHAR(60)     NOT NULL,
    transaction_id      VARCHAR(50)     NOT NULL,
    loan_id             VARCHAR(20)     NOT NULL,
    transaction_type    VARCHAR(30)     NOT NULL,
    transaction_date    DATE            NOT NULL,
    accounting_date     DATE            NOT NULL,
    account_code        VARCHAR(10)     NOT NULL,
    account_name        VARCHAR(60)     NOT NULL,
    debit_amount        DECIMAL(15, 2)  NOT NULL DEFAULT 0,
    credit_amount       DECIMAL(15, 2)  NOT NULL DEFAULT 0,
    signed_amount       DECIMAL(15, 2)  NOT NULL,

    CONSTRAINT pk_accounting_entries    PRIMARY KEY (entry_id),
    CONSTRAINT fk_entry_loan            FOREIGN KEY (loan_id) REFERENCES loan_transactions(loan_id),
    CONSTRAINT ck_debit_amount          CHECK (debit_amount >= 0),
    CONSTRAINT ck_credit_amount         CHECK (credit_amount >= 0),
    CONSTRAINT ck_transaction_type      CHECK (transaction_type IN (
        'disbursement',
        'interest_accrual',
        'overdue_interest_accrual',
        'repayment',
        'charge_off',
        'loan_transfer'
    ))
);


-- ------------------------------------------------------------
-- 5. Loan Transfers
-- ------------------------------------------------------------
CREATE TABLE loan_transfers (
    transfer_id     VARCHAR(20)     NOT NULL,
    loan_id         VARCHAR(20)     NOT NULL,
    transfer_date   DATE            NOT NULL,
    transfer_type   VARCHAR(10)     NOT NULL,
    face_value      DECIMAL(15, 2)  NOT NULL,
    transfer_price  DECIMAL(15, 2)  NOT NULL,
    discount_rate   DECIMAL(6, 4)   NOT NULL,
    counterparty    VARCHAR(60)     NOT NULL,

    CONSTRAINT pk_loan_transfers        PRIMARY KEY (transfer_id),
    CONSTRAINT fk_transfer_loan         FOREIGN KEY (loan_id) REFERENCES loan_transactions(loan_id),
    CONSTRAINT ck_transfer_type         CHECK (transfer_type IN ('NPL', 'ABS')),
    CONSTRAINT ck_face_value            CHECK (face_value > 0),
    CONSTRAINT ck_transfer_price        CHECK (transfer_price > 0),
    CONSTRAINT ck_discount_rate         CHECK (discount_rate >= 0 AND discount_rate < 1),
    CONSTRAINT uq_transfer_loan         UNIQUE (loan_id)
);


-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
CREATE INDEX idx_loans_status       ON loan_transactions(loan_status);
CREATE INDEX idx_loans_region       ON loan_transactions(region);
CREATE INDEX idx_loans_source       ON loan_transactions(source_system);
CREATE INDEX idx_loans_date         ON loan_transactions(transaction_date);

CREATE INDEX idx_schedule_loan      ON repayment_schedule(loan_id);
CREATE INDEX idx_schedule_overdue   ON repayment_schedule(installment_overdue_flag);
CREATE INDEX idx_schedule_overdue_days ON repayment_schedule(overdue_days);

CREATE INDEX idx_repay_loan         ON repayment_transactions(loan_id);
CREATE INDEX idx_repay_date         ON repayment_transactions(transaction_date);
CREATE INDEX idx_repay_status       ON repayment_transactions(payment_status);

CREATE INDEX idx_entries_loan       ON accounting_entries(loan_id);
CREATE INDEX idx_entries_type       ON accounting_entries(transaction_type);
CREATE INDEX idx_entries_date       ON accounting_entries(accounting_date);
CREATE INDEX idx_entries_account    ON accounting_entries(account_code);

CREATE INDEX idx_transfers_loan     ON loan_transfers(loan_id);
CREATE INDEX idx_transfers_type     ON loan_transfers(transfer_type);
CREATE INDEX idx_transfers_date     ON loan_transfers(transfer_date);

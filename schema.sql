DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions
(
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    date DATE NOT NULL,
    description TEXT NOT NULL
);


DROP TABLE IF EXISTS users;

CREATE TABLE users
(
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL
);


DROP TABLE IF EXISTS budgets;

CREATE TABLE budgets
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    month TEXT NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL
);


DROP TABLE IF EXISTS quick;

CREATE TABLE quick
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL
);

INSERT INTO quick (user_id, currency, amount, type, category)
VALUES ('tracy', 'EUR', 200, 'income', 'salary');

CREATE TABLE saving_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    goal_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    currency TEXT NOT NULL
);
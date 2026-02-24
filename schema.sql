DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions
(
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    date DATE NOT NULL
);

INSERT INTO transactions (user_id, currency, amount, type, category, date)
VALUES
  ('1', 'EUR', '10', 'income', 'food', 2026-2-20);







DROP TABLE IF EXISTS users;

CREATE TABLE users
(
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL
);
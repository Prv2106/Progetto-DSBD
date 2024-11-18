-- init.sql

-- Crea la tabella 'Users'
CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    ticker VARCHAR(50) NOT NULL
);

-- Crea la tabella 'Data' con una foreign key che fa riferimento a 'Users'
CREATE TABLE IF NOT EXISTS Data (
    timestamp DATETIME NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    valore_euro DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (timestamp, ticker)
);


INSERT INTO Users (email, ticker) VALUES
('alberto@example.com', 'AAPL'),
('giuseppe@example.com', 'GOOG'),
('maria@example.com', 'MSFT'),
('luigi@example.com', 'AMZN');
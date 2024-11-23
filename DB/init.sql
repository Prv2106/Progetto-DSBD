-- init.sql

CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    pwd VARCHAR(255) NOT NULL,
    ticker VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS Data (
    timestamp DATETIME NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    valore_euro DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (timestamp, ticker)
);


INSERT INTO Users (email, pwd, ticker) VALUES
('alberto@example.com', '$2b$12$KjM6u9zUJG/examplehash1', 'AAPL'),
('giuseppe@example.com', '$2b$12$hBd3ERkZ2J/examplehash2', 'GOOG'),
('maria@example.com', '$2b$12$Tj9dsfL8OJ/examplehash3', 'MSFT'),
('luigi@example.com', '$2b$12$Ygdfj76TLN/examplehash4', 'AMZN');

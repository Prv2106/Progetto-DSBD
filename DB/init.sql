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



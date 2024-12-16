-- init.sql

CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    pwd VARCHAR(255) NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    low_value DECIMAL(10, 2),
    high_value DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS Data (
    timestamp DATETIME NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    valore_euro DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (timestamp, ticker)
);



-- Inserimenti per AAPL
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:12', 'AAPL', 200);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:02', 'AAPL', 201);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:03:24', 'AAPL', 202);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:02', 'AAPL', 203);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:00:02', 'AAPL', 204);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:04', 'AAPL', 205);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:03:22', 'AAPL', 206);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:03:20', 'AAPL', 223.32);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:05', 'AAPL', 223.32);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:07', 'AAPL', 223.32);

-- Inserimenti per AMZN
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:59:34', 'AMZN', 190);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:59:31', 'AMZN', 191);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:28', 'AMZN', 192);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:01:26', 'AMZN', 193);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:00:56', 'AMZN', 190);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:23', 'AMZN', 204.71);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:21', 'AMZN', 204.71);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:01:19', 'AMZN', 204.71);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:49', 'AMZN', 204.71);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:01:15', 'AMZN', 204.71);

-- Inserimenti per GOOG
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:45', 'GOOG', 150);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:51', 'GOOG', 160);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:02', 'GOOG', 148);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:41', 'GOOG', 170);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:43', 'GOOG', 170);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:42', 'GOOG', 170);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:09', 'GOOG', 172.24);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:02:46', 'GOOG', 172.24);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:01:33', 'GOOG', 172.24);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:04:49', 'GOOG', 172.24);

-- Inserimenti per TSLA
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:57:05', 'TSLA', 300.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:04', 'TSLA', 396.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:57:17', 'TSLA', 392.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:07', 'TSLA', 392.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:03:24', 'TSLA', 392.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:03:50', 'TSLA', 200);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:02', 'TSLA', 392.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:56:35', 'TSLA', 392.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 19:03:22', 'TSLA', 392.61);
INSERT INTO Data (timestamp, ticker, valore_euro) VALUES ('2024-12-15 18:58:00', 'TSLA', 392.61);

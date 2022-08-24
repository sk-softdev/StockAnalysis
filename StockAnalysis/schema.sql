DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS userStats;
DROP TABLE IF EXISTS marketStats;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  stocks TEXT,
  lastLogin TEXT
);

CREATE TABLE marketStats (
  ticker TEXT,
  volume INTEGER,
  change FLOAT,
  dateUpdated TEXT
);

CREATE TABLE userStats (
  username TEXT NOT NULL,
  name TEXT NOT NULL,
  ticker TEXT NOT NULL,
  logo TEXT NOT NULL,
  tickerID INTEGER NOT NULL,
  buttonID INTEGER NOT NULL,
  stockPrice FLOAT NOT NULL,
  priceChange INTEGER NOT NULL,
  volume INTEGER NOT NULL,
  newsTitle TEXT NOT NULL,
  newsPublisher TEXT NOT NULL,
  newsDate TEXT NOT NULL,
  newsURL TEXT NOT NULL
);
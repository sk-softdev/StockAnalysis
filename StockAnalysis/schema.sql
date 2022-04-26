DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS userStats;
DROP TABLE IF EXISTS marketStats;
DROP TABLE IF EXISTS researchStats;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  stocks TEXT
);

CREATE TABLE marketStats (
  ticker TEXT NOT NULL,
  volume INTEGER NOT NULL,
  change FLOAT NOT NULL
);

CREATE TABLE userStats (
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
  newsDate TEXT NOT NULL
);

CREATE TABLE researchStats (
  label TEXT NOT NULL,
  value FLOAT NOT NULL
);
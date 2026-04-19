-- Creates the test database alongside portal_dev on first Postgres boot.
CREATE DATABASE portal_test;
GRANT ALL PRIVILEGES ON DATABASE portal_test TO portal;

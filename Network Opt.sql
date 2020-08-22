-- Optimiser
USE NO; -- Use this DB/schema
-- Create the location table
DROP TABLE IF EXISTS `Location`;
CREATE TABLE Location (
    Location CHAR(100) NOT NULL
);
-- Create the product table
DROP TABLE IF EXISTS `Product`;
CREATE TABLE Product (
    Product CHAR(100) NOT NULL
);
DROP TABLE IF EXISTS `Demand`;
CREATE TABLE Demand (
    Customer CHAR(100) NOT NULL,
    Product CHAR(100) NOT NULL,
    DemandUnits FLOAT NOT NULL
);
DROP TABLE IF EXISTS `CustomerLanes`;
CREATE TABLE CustomerLanes (
	Location CHAR(100) NOT NULL,
    Customer CHAR(100) NOT NULL,
    Product CHAR(100) NOT NULL,
    Rate FLOAT NOT NULL
);
DROP TABLE IF EXISTS `InterLocationLanes`;
CREATE TABLE InterLocationLanes (
	OriginLocation CHAR(100) NOT NULL,
    DestinationLocation CHAR(100) NOT NULL,
    Product CHAR(100) NOT NULL,
    Rate FLOAT NOT NULL
);
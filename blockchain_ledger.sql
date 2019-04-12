USE `database_name`;

CREATE TABLE `table_name` (
    id INT NOT NULL  AUTO_INCREMENT,
    txn_no VARCHAR(100) NOT NULL UNIQUE ,
    metaData TEXT NOT NULL ,
    trade_hash VARCHAR(100) NULL ,
    created_at DATETIME NOT NULL ,
    PRIMARY KEY (id)
);

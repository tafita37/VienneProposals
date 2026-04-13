CREATE DATABASE vienne_proposal;
\c vienne_proposal

CREATE TABLE role(
   id SERIAL,
   name VARCHAR(30)  NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(name)
);

CREATE TABLE users(
   id SERIAL,
   first_name VARCHAR(100)  NOT NULL,
   last_name VARCHAR(100)  NOT NULL,
   email VARCHAR(50)  NOT NULL,
   password TEXT NOT NULL,
   failed_login_attempts INTEGER NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(email)
);

CREATE TABLE category(
   id SERIAL,
   name VARCHAR(50)  NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(name)
);

CREATE TABLE unit(
   id SERIAL,
   name VARCHAR(50)  NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(name)
);

CREATE TABLE product(
   id SERIAL,
   designation TEXT NOT NULL,
   purchase_unit_price DOUBLE PRECISION NOT NULL,
   sale_unit_price DOUBLE PRECISION NOT NULL,
   coefficient NUMERIC(15,2) NOT NULL,
   unit_id INTEGER NOT NULL,
   category_id INTEGER NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(designation),
   FOREIGN KEY(unit_id) REFERENCES unit(id),
   FOREIGN KEY(category_id) REFERENCES category(id)
);

CREATE TABLE client(
   id SERIAL,
   name VARCHAR(100)  NOT NULL,
   address VARCHAR(100)  NOT NULL,
   email VARCHAR(100)  NOT NULL,
   website_url TEXT,
   phone VARCHAR(50)  NOT NULL,
   is_company BOOLEAN NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(address),
   UNIQUE(email),
   UNIQUE(website_url),
   UNIQUE(phone)
);

CREATE TABLE individual(
   id SERIAL,
   first_name VARCHAR(100)  NOT NULL,
   last_name VARCHAR(100)  NOT NULL,
   birth_date DATE NOT NULL,
   id_card_number VARCHAR(20)  NOT NULL,
   client_id INTEGER NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(id_card_number),
   FOREIGN KEY(client_id) REFERENCES client(id)
);

CREATE TABLE company_type(
   id SERIAL,
   name VARCHAR(50)  NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(name)
);

CREATE TABLE company(
   id SERIAL,
   name VARCHAR(100)  NOT NULL,
   registration_number VARCHAR(50)  NOT NULL,
   tax_identification_number VARCHAR(50)  NOT NULL,
   created_at DATE NOT NULL,
   company_type_id INTEGER NOT NULL,
   client_id INTEGER NOT NULL,
   PRIMARY KEY(id),
   UNIQUE(name),
   UNIQUE(registration_number),
   UNIQUE(tax_identification_number),
   FOREIGN KEY(company_type_id) REFERENCES company_type(id),
   FOREIGN KEY(client_id) REFERENCES client(id)
);

CREATE TABLE commercial_proposal(
   id SERIAL,
   date_proposal DATE NOT NULL,
   amount_ht DOUBLE PRECISION NOT NULL,
   amount_ttc DOUBLE PRECISION NOT NULL,
   client_id INTEGER NOT NULL,
   commercial_id INTEGER NOT NULL,
   PRIMARY KEY(id),
   FOREIGN KEY(client_id) REFERENCES client(id),
   FOREIGN KEY(commercial_id) REFERENCES users(id)
);

CREATE TABLE proposal_product(
   id SERIAL,
   coefficient DOUBLE PRECISION NOT NULL,
   quantity DOUBLE PRECISION NOT NULL,
   purchase_unit_price DOUBLE PRECISION NOT NULL,
   sale_unit_price DOUBLE PRECISION NOT NULL,
   product_id INTEGER NOT NULL,
   commercial_proposal_id INTEGER NOT NULL,
   PRIMARY KEY(id),
   FOREIGN KEY(product_id) REFERENCES product(id),
   FOREIGN KEY(commercial_proposal_id) REFERENCES commercial_proposal(id)
);

CREATE TABLE excel_import(
   id SERIAL,
   name VARCHAR(50)  NOT NULL,
   date_import DATE NOT NULL,
   product_count INTEGER NOT NULL,
   category_id INTEGER NOT NULL,
   FOREIGN KEY(category_id) REFERENCES category(id),
   PRIMARY KEY(id)
);

-- 

CREATE TABLE users_role(
   id INTEGER,
   id_1 INTEGER,
   PRIMARY KEY(id, id_1),
   FOREIGN KEY(id) REFERENCES role(id),
   FOREIGN KEY(id_1) REFERENCES users(id)
);

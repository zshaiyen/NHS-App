CREATE TABLE IF NOT EXISTS organization (
    organization_id INTEGER PRIMARY KEY,
    domain_root TEXT,
    name TEXT,
    short_name TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS organization_domain_root ON organization(domain_root);

INSERT INTO organization (domain_root, name, short_name) VALUES('nhshbhs.com', 'Huntington Beach High School', 'HBHS');


CREATE TABLE IF NOT EXSITS category (
    category_id INTEGER PRIMARY KEY,
    name TEXT,
    -- FPJS (F=Freshman; P=Sophomore; J=Junior; S=Senior)
    visibility TEXT,
    display_order INTEGER
;

CREATE UNIQUE INDEX IF NOT EXISTS category_name ON category(name);

INSERT INTO category (name, visibility, display_order) VALUES('NHS', 'FPJS', 10);
INSERT INTO category (name, visibility, display_order) VALUES('Tutoring', 'FPJS', 20);
INSERT INTO category (name, visibility, display_order) VALUES('Other', 'FPJS', 30);
INSERT INTO category (name, visibility, display_order) VALUES('Sophomore Project', 'P', 50);
INSERT INTO category (name, visibility, display_order) VALUES('Senior Cord', 'S', 60);


CREATE TABLE IF NOT EXISTS app_user (
    app_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    full_name TEXT,
    photo_url TEXT,
    class_of TEXT,
    school_id TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS app_user_email ON app_user(email);


CREATE TABLE IF NOT EXISTS verification_log (
    verification_log_id INTEGER PRIMARY KEY,
    hours_worked INTEGER,
    event_name TEXT,
    event_date DATE,
    event_supervisor TEXT,
    supervisor_signature TEXT,
    location_coords TEXT,
    app_user_id INTEGER,
    category_id INTEGER,
    FOREIGN KEY (app_user_id) REFERENCES app_user(app_user_id),
    FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE INDEX IF NOT EXISTS verification_log_app_user_id ON verification_log(app_user_id);
CREATE INDEX IF NOT EXISTS verification_log_category_id ON verification_log(category_id);

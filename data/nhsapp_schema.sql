CREATE TABLE organization (
    organization_id INTEGER PRIMARY KEY,
    domain_root TEXT NOT NULL UNIQUE,
    name TEXT,
    short_name TEXT
);

INSERT INTO organization (domain_root, name, short_name) VALUES('127.0.0.1:5000', 'Zane Academy', 'ZANE');
INSERT INTO organization (domain_root, name, short_name) VALUES('nhshbhs.com', 'Huntington Beach High School', 'HBHS');


CREATE TABLE category (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    -- FPJS (F=Freshman; P=Sophomore; J=Junior; S=Senior)
    visibility TEXT,
    display_order INTEGER,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    UNIQUE(name, organization_id)
);

CREATE INDEX category_organization_id ON category(organization_id);

INSERT INTO category (name, visibility, display_order, organization_id) VALUES('NHS', 'FPJS', 10, 1);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Tutoring', 'FPJS', 20, 1);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Other', 'FPJS', 30, 1);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Sophomore Project', 'P', 50, 1);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Senior Cord', 'S', 60, 1);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('NHS', 'FPJS', 10, 2);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Tutoring', 'FPJS', 20, 2);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Other', 'FPJS', 30, 2);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Sophomore Project', 'P', 50, 2);
INSERT INTO category (name, visibility, display_order, organization_id) VALUES('Senior Cord', 'S', 60, 2);


CREATE TABLE period (
    period_id INTEGER PRIMARY KEY,
    academic_year INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    UNIQUE(academic_year, name, organization_id)
);

CREATE INDEX period_organization_id ON period(organization_id);
CREATE INDEX period_start_date ON period(start_date);

INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2024, 'Summer', '2024-06-15', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, 'Semester 1', '2024-08-28', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, 'Semester 2', '2025-02-01', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, 'Summer', '2025-06-13', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2024, 'Summer', '2024-06-15', 2);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, 'Semester 1', '2024-08-28', 2);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, 'Semester 2', '2025-02-01', 2);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, 'Summer', '2025-06-13', 2);


CREATE TABLE app_user (
    app_user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    photo_url TEXT,
    class_of TEXT,
    school_id TEXT,
    admin_flag INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id)
);

CREATE INDEX app_user_admin_flag ON app_user(admin_flag);
CREATE INDEX app_user_organiazation_id ON app_user(organization_id);

INSERT INTO app_user (email, full_name, organization_id) VALUES ('support@nhshbhs.com', 'NHS App Support', 1);


CREATE TABLE app_user_log_category (
    app_user_log_category_id INTEGER PRIMARY KEY,
    app_user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    hours_worked INTEGER,
    UNIQUE(period_id, app_user_id, category_id)
);


CREATE TABLE verification_log (
    verification_log_id INTEGER PRIMARY KEY,
    hours_worked INTEGER,
    event_name TEXT,
    event_date DATE,
    event_supervisor TEXT,
    supervisor_signature TEXT,
    location_coords TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    app_user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    FOREIGN KEY (app_user_id) REFERENCES app_user(app_user_id),
    FOREIGN KEY (category_id) REFERENCES category(category_id),
    FOREIGN KEY (period_id) REFERENCES period(period_id)
);

CREATE INDEX verification_log_app_user_id ON verification_log(app_user_id);
CREATE INDEX verification_log_category_id ON verification_log(category_id);
CREATE INDEX verification_log_period_id ON verification_log(period_id);
CREATE TABLE organization (
    organization_id INTEGER PRIMARY KEY,
    domain_root TEXT NOT NULL UNIQUE,
    name TEXT,
    short_name TEXT
);


CREATE TABLE category (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    display_order INTEGER,
    freshman_visible_flag INTEGER,
    freshman_hours_required INTEGER,
    sophomore_visible_flag INTEGER,
    sophomore_hours_required INTEGER,
    junior_visible_flag INTEGER,
    junior_hours_required INTEGER,
    senior_visible_flag INTEGER,
    senior_hours_required INTEGER,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    UNIQUE(name, organization_id)
);

CREATE INDEX category_organization_id ON category(organization_id);


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


CREATE TABLE app_user (
    app_user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    photo_url TEXT,
    class_of TEXT,
    school_id TEXT,
    admin_flag INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    UNIQUE (email, organization_id)
);

CREATE INDEX app_user_admin_flag ON app_user(admin_flag);
CREATE INDEX app_user_organization_id ON app_user(organization_id);


CREATE TABLE app_user_log_category (
    app_user_log_category_id INTEGER PRIMARY KEY,
    app_user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    hours_worked INTEGER,
    UNIQUE(period_id, app_user_id, category_id),
    FOREIGN KEY (app_user_id) REFERENCES app_user(app_user_id),
    FOREIGN KEY (category_id) REFERENCES category(category_id),
    FOREIGN KEY (period_id) REFERENCES period(period_id),
    UNIQUE (app_user_id, category_id, period_id)
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

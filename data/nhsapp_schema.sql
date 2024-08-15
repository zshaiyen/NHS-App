CREATE TABLE organization (
    organization_id INTEGER PRIMARY KEY,
    domain_root TEXT NOT NULL UNIQUE,
    name TEXT,
    short_name TEXT,
    logo TEXT,
    support_email TEXT,
    disabled_flag INTEGER
);


-- Used to populate "Class of" drop-down
CREATE TABLE class_year (
    year_num INTEGER NOT NULL,
    name TEXT,
    organization_id INTEGER NOT NULL,
    PRIMARY KEY(organization_id, year_num),
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id)
) WITHOUT ROWID;


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
    UNIQUE(organization_id, name)
);

CREATE INDEX category_organization_id ON category(organization_id);
CREATE INDEX category_informational_only_flag ON category(informational_only_flag);


CREATE TABLE period (
    period_id INTEGER PRIMARY KEY,
    academic_year INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    locked_flag INTEGER,
    no_required_hours_flag INTEGER,
    organization_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_at DATETIME,
    updated_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES app_user(app_user_id),
    FOREIGN KEY (updated_by) REFERENCES app_user(app_user_id),
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    UNIQUE(organization_id, name)
);

CREATE INDEX period_organization_id ON period(organization_id);
CREATE INDEX period_dates ON period(start_date, end_date);


CREATE TABLE app_user (
    app_user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    photo_url TEXT,
    class_of TEXT,
    school_id TEXT,
    team_name TEXT,
    super_user_flag INTEGER,
    admin_flag INTEGER,
    disabled_flag INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    updated_by INTEGER,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (updated_by) REFERENCES app_user(app_user_id),
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    UNIQUE (organization_id, email)
);

CREATE INDEX app_user_organization_id ON app_user(organization_id);
CREATE INDEX app_user_admin_flag ON app_user(admin_flag);
CREATE INDEX app_user_disabled_flag ON app_user(disabled_flag);


CREATE TABLE verification_log (
    verification_log_id INTEGER PRIMARY KEY,
    hours_worked INTEGER NOT NULL,
    event_date DATE NOT NULL,
    event_name TEXT,
    event_supervisor TEXT,
    supervisor_signature TEXT,
    signature_file TEXT,
    location_coords TEXT,
    location_accuracy TEXT,
    app_user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_at DATETIME,
    updated_by INTEGER NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    mobile_flag INTEGER,
    FOREIGN KEY (created_by) REFERENCES app_user(app_user_id),
    FOREIGN KEY (updated_by) REFERENCES app_user(app_user_id),
    FOREIGN KEY (app_user_id) REFERENCES app_user(app_user_id),
    FOREIGN KEY (category_id) REFERENCES category(category_id),
    FOREIGN KEY (period_id) REFERENCES period(period_id)
);

CREATE INDEX verification_log_app_user_id ON verification_log(app_user_id);
CREATE INDEX verification_log_category_id ON verification_log(category_id);
CREATE INDEX verification_log_period_id ON verification_log(period_id);

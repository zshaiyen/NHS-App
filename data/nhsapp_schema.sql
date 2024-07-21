CREATE TABLE IF NOT EXISTS app_user (
    app_user_id INTEGER PRIMARY KEY,
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
    app_user_id INTEGER,
    FOREIGN KEY (app_user_id) REFERENCES app_user(app_user_id)
);
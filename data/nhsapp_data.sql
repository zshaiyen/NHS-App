-- organization
INSERT INTO organization (domain_root, name, short_name) VALUES('127.0.0.1:5000', 'Zane Academy', 'ZANE');

INSERT INTO organization (domain_root, name, short_name) VALUES('nhshbhs.com', 'Huntington Beach High School', 'HBHS');

-- category
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('NHS', 10, 1, 0, null, 1, 15, 1, 10, 1, 5);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Tutoring', 20, 1, 0, null, 1, 5, 1, 15, 1, 10);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Other', 30, 1, 0, null, 1, 5, 1, 5, 1, 5);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Sophomore Project', 40, 1, 0, null, 1, 15, 0, null, 0, null);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Senior Cord', 50, 1, 0, null, 0, null, 0, null, 1, 10);
INSERT INTO category

(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('NHS', 10, 2, 0, null, 1, 15, 1, 10, 1, 5);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Tutoring', 20, 2, 0, null, 1, 5, 1, 15, 1, 10);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Other', 30, 2, 0, null, 1, 5, 1, 5, 1, 5);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Sophomore Project', 40, 2, 0, null, 1, 15, 0, null, 0, null);
INSERT INTO category
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required)
VALUES('Senior Cord', 50, 2, 0, null, 0, null, 0, null, 1, 10);

-- period
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2024, '2024 Summer', '2024-06-15', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, '2024-2025 Semester 1', '2024-08-28', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, '2024-2025 Semester 2', '2025-02-01', 1);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, '2025 Summer', '2025-06-13', 1);

INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2024, '2024 Summer', '2024-06-15', 2);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, '2024-2025 Semester 1', '2024-08-28', 2);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, '2024-2025 Semester 2', '2025-02-01', 2);
INSERT INTO period (academic_year, name, start_date, organization_id) VALUES(2025, '2025 Summer', '2025-06-13', 2);

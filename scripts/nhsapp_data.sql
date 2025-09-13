-- organization
INSERT INTO organization (domain_root, name, short_name, support_email, logo, allowed_domains) VALUES('127.0.0.1:5000', 'Zane Academy', 'ZANE', 'support@zaneacademy.com', '/img/nhs_hbhs_logo.png', 'student.hbuhsd.edu, gmail.com');

-- class_year
INSERT INTO class_year (year_num, name, organization_id) VALUES(2025, 'Senior', 1);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2026, 'Junior', 1);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2027, 'Sophomore', 1);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2028, 'Freshman', 1);

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
VALUES('Senior Cord', 50, 1, 0, null, 0, null, 0, null, 1, 10);

-- period
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2026, '2025 Summer', '2025-06-15', '2025-08-27', 1);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2026, '2025-2026 Semester 1', '2025-08-28', '2026-01-31', 1);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2026, '2025-2026 Semester 2', '2026-02-01', '2026-06-12', 1);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2027, '2026 Summer', '2026-06-13', '2026-08-27', 1);
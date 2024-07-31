-- organization
INSERT INTO organization (domain_root, name, short_name, support_email, logo) VALUES('127.0.0.1:5000', 'Zane Academy', 'ZANE', 'zaneshaiyen@gmail.com', 'img/nhs_hbhs_logo.png');

INSERT INTO organization (domain_root, name, short_name, support_email, logo) VALUES('nhshbhs.com', 'Huntington Beach High School', 'HBHS', 'support@nhshbhs.com', 'img/nhs_hbhs_logo.png');


-- class_year
INSERT INTO class_year (year_num, name, organization_id) VALUES(2025, 'Senior', 1);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2026, 'Junior', 1);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2027, 'Sophomore', 1);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2028, 'Freshman', 1);

INSERT INTO class_year (year_num, name, organization_id) VALUES(2025, 'Senior', 2);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2026, 'Junior', 2);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2027, 'Sophomore', 2);
INSERT INTO class_year (year_num, name, organization_id) VALUES(2028, 'Freshman', 2);


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
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required, informational_only_flag)
VALUES('Senior Cord', 50, 1, 0, null, 0, null, 0, null, 1, 10, 1);
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
(name, display_order, organization_id, freshman_visible_flag, freshman_hours_required, sophomore_visible_flag, sophomore_hours_required, junior_visible_flag, junior_hours_required, senior_visible_flag, senior_hours_required, informational_only_flag)
VALUES('Senior Cord', 50, 2, 0, null, 0, null, 0, null, 1, 10, 1);


-- period
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2025, '2024 Summer', '2024-06-15', '2024-08-27', 1);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2025, '2024-2025 Semester 1', '2024-08-28', '2025-01-31', 1);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2025, '2024-2025 Semester 2', '2025-02-01', '2025-06-12', 1);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2026, '2025 Summer', '2025-06-13', '2025-08-27', 1);

INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2025, '2024 Summer', '2024-06-15', '2024-08-27', 2);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2025, '2024-2025 Semester 1', '2024-08-28', '2025-01-31', 2);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2025, '2024-2025 Semester 2', '2025-02-01', '2025-06-12', 2);
INSERT INTO period (academic_year, name, start_date, end_date, organization_id) VALUES(2026, '2025 Summer', '2025-06-13', '2025-08-27', 2);

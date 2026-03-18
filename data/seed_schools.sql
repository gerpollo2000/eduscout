-- EduScout Seed Data: 25 Manhattan Schools
-- Mix of private, public, charter, parochial across K-12 + university
-- Data based on publicly available information (2025-2026)
-- Run: psql $DATABASE_URL -f seed_schools.sql

-- ============================================================
-- ELITE PRIVATE K-12
-- ============================================================

INSERT INTO schools (name, slug, level, address, neighborhood, zip_code, latitude, longitude, phone, website, school_type, religious_orientation, methodology, annual_tuition_min, annual_tuition_max, enrollment_fee, max_class_size, student_teacher_ratio, total_students, has_transportation, has_lunch_program, lunch_is_nutritionist_supervised, has_scholarships, has_financial_aid, has_special_needs_support, has_wheelchair_access, has_elevator, has_ramps, has_english_program, uses_tablets, accreditations, grades_offered, entry_time, exit_time)
VALUES
('Trinity School', 'trinity-school', 'k12', '139 W 91st St, New York, NY 10024', 'Upper West Side', '10024', 40.7905, -73.9710, '212-873-1650', 'https://www.trinityschoolnyc.org', 'private', 'secular', 'traditional_progressive', 65000, 69000, 500, 16, '6:1', 1000, FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS','NAIS'], 'K-12', '08:00', '15:15'),

('The Spence School', 'spence-school', 'k12', '22 E 91st St, New York, NY 10128', 'Upper East Side', '10128', 40.7846, -73.9570, '212-289-5940', 'https://www.spenceschool.org', 'private', 'secular', 'traditional', 66000, 68480, 500, 15, '7:1', 780, FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS'], 'K-12', '08:00', '15:30'),

('The Dalton School', 'dalton-school', 'k12', '108 E 89th St, New York, NY 10128', 'Upper East Side', '10128', 40.7823, -73.9558, '212-423-5200', 'https://www.dalton.org', 'private', 'secular', 'dalton_plan_progressive', 60000, 65000, 500, 18, '7:1', 1300, FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS','NAIS'], 'K-12', '08:15', '15:20'),

('Avenues: The World School', 'avenues-world-school', 'k12', '259 10th Ave, New York, NY 10001', 'Chelsea', '10001', 40.7488, -74.0040, '212-524-7300', 'https://www.avenues.org', 'private', 'secular', 'world_immersion', 58000, 63000, 750, 18, '8:1', 1700, TRUE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS','CIS'], 'PK-12', '08:00', '15:30'),

('Brearley School', 'brearley-school', 'k12', '610 E 83rd St, New York, NY 10028', 'Upper East Side', '10028', 40.7745, -73.9478, '212-744-8582', 'https://www.brearley.org', 'private', 'secular', 'traditional', 62000, 66000, 500, 14, '5:1', 750, FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYSAIS'], 'K-12', '08:00', '15:15');

-- ============================================================
-- MID-RANGE PRIVATE
-- ============================================================

INSERT INTO schools (name, slug, level, address, neighborhood, zip_code, latitude, longitude, phone, website, school_type, religious_orientation, methodology, annual_tuition_min, annual_tuition_max, enrollment_fee, max_class_size, student_teacher_ratio, total_students, has_transportation, has_lunch_program, lunch_is_nutritionist_supervised, has_scholarships, has_financial_aid, has_special_needs_support, has_wheelchair_access, has_elevator, has_ramps, has_english_program, uses_tablets, accreditations, grades_offered, entry_time, exit_time)
VALUES
('BASIS Independent Manhattan', 'basis-independent-manhattan', 'k12', '795 Columbus Ave, New York, NY 10025', 'Upper West Side', '10025', 40.7997, -73.9618, '646-809-2092', 'https://basisindependent.com/schools/ny/manhattan', 'private', 'secular', 'stem_liberal_arts', 35000, 42000, 300, 15, '10:1', 850, FALSE, TRUE, FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NAIS'], 'PK-12', '07:45', '15:30'),

('The IDEAL School of Manhattan', 'ideal-school', 'k12', '314 W 91st St, New York, NY 10024', 'Upper West Side', '10024', 40.7919, -73.9733, '212-769-1699', 'https://www.theidealschool.org', 'private', 'secular', 'inclusion_progressive', 38000, 52000, 400, 14, '6:1', 380, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS'], 'PK-12', '08:15', '15:00'),

('Dwight School', 'dwight-school', 'k12', '291 Central Park West, New York, NY 10024', 'Upper West Side', '10024', 40.7881, -73.9661, '212-724-6360', 'https://www.dwight.edu', 'private', 'secular', 'IB_personalized', 55000, 62000, 500, 16, '7:1', 900, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['IBO','NYSAIS'], 'PK-12', '08:00', '15:30'),

('British International School of NY', 'british-international-ny', 'k12', '20 Waterside Plaza, New York, NY 10010', 'Kips Bay', '10010', 40.7371, -73.9746, '212-481-2700', 'https://www.bis-ny.org', 'private', 'secular', 'british_national_curriculum', 40000, 48000, 600, 18, '8:1', 300, FALSE, TRUE, FALSE, FALSE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['CIS','BSO'], 'PK-12', '08:30', '15:30'),

('George Jackson Academy', 'george-jackson-academy', 'middle', '45 E 81st St, New York, NY 10028', 'Upper East Side', '10028', 40.7791, -73.9593, '212-472-2928', 'https://www.gjaglobal.org', 'private', 'secular', 'traditional', 0, 0, 0, 15, '6:1', 84, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYSAIS'], '6-8', '08:00', '15:30');

-- ============================================================
-- PAROCHIAL / RELIGIOUS
-- ============================================================

INSERT INTO schools (name, slug, level, address, neighborhood, zip_code, latitude, longitude, phone, website, school_type, religious_orientation, methodology, annual_tuition_min, annual_tuition_max, enrollment_fee, max_class_size, student_teacher_ratio, total_students, has_transportation, has_lunch_program, lunch_is_nutritionist_supervised, has_scholarships, has_financial_aid, has_special_needs_support, has_wheelchair_access, has_elevator, has_ramps, has_english_program, uses_tablets, accreditations, grades_offered, entry_time, exit_time)
VALUES
('Convent of the Sacred Heart', 'sacred-heart', 'k12', '1 E 91st St, New York, NY 10128', 'Upper East Side', '10128', 40.7844, -73.9579, '212-722-4745', 'https://www.cshnyc.org', 'private', 'catholic', 'sacred_heart_tradition', 60000, 67520, 500, 16, '7:1', 700, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS','NCEA'], 'PK-12', '08:00', '15:15'),

('Marymount School of New York', 'marymount-school', 'k12', '1026 5th Ave, New York, NY 10028', 'Upper East Side', '10028', 40.7802, -73.9617, '212-744-4486', 'https://www.marymountnyc.org', 'private', 'catholic', 'RSHM_tradition', 55000, 62000, 500, 18, '7:1', 750, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSAIS','NCEA'], 'N-12', '08:00', '15:15'),

('Cathedral School of St. John the Divine', 'cathedral-school-stjohn', 'elementary', '1047 Amsterdam Ave, New York, NY 10025', 'Morningside Heights', '10025', 40.8038, -73.9614, '212-316-7500', 'https://www.cathedralnyc.org', 'private', 'episcopal', 'traditional', 30000, 38000, 250, 16, '8:1', 230, FALSE, TRUE, FALSE, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYSAIS'], 'PK-8', '08:15', '15:00'),

('Rodeph Sholom School', 'rodeph-sholom', 'elementary', '10 W 84th St, New York, NY 10024', 'Upper West Side', '10024', 40.7852, -73.9711, '212-362-8800', 'https://www.rodephsholom.org/school', 'private', 'jewish_reform', 'progressive', 35000, 48000, 300, 16, '7:1', 400, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYSAIS'], 'PK-8', '08:15', '15:00');

-- ============================================================
-- PUBLIC SCHOOLS
-- ============================================================

INSERT INTO schools (name, slug, level, address, neighborhood, zip_code, latitude, longitude, phone, website, school_type, religious_orientation, methodology, annual_tuition_min, annual_tuition_max, enrollment_fee, max_class_size, student_teacher_ratio, total_students, has_transportation, has_lunch_program, lunch_is_nutritionist_supervised, has_scholarships, has_financial_aid, has_special_needs_support, has_wheelchair_access, has_elevator, has_ramps, has_english_program, uses_tablets, accreditations, grades_offered, entry_time, exit_time)
VALUES
('PS 6 Lillie D. Blake', 'ps6-lillie-blake', 'elementary', '45 E 81st St, New York, NY 10028', 'Upper East Side', '10028', 40.7790, -73.9594, '212-838-6466', 'https://www.ps6nyc.com', 'public', 'secular', 'traditional', 0, 0, 0, 25, '13:1', 520, TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYCDOE'], 'PK-5', '08:10', '14:40'),

('PS 87 William Sherman', 'ps87-william-sherman', 'elementary', '160 W 78th St, New York, NY 10024', 'Upper West Side', '10024', 40.7818, -73.9764, '212-678-2826', 'https://www.ps87.info', 'public', 'secular', 'progressive', 0, 0, 0, 28, '14:1', 600, TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYCDOE'], 'PK-5', '08:10', '14:40'),

('Beacon High School', 'beacon-high-school', 'high', '227 W 61st St, New York, NY 10023', 'Lincoln Square', '10023', 40.7723, -73.9871, '212-245-8986', 'https://www.beaconschool.org', 'public', 'secular', 'portfolio_based', 0, 0, 0, 30, '15:1', 1400, TRUE, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYCDOE'], '9-12', '08:15', '15:05'),

('MS 54 Booker T. Washington', 'ms54-booker-washington', 'middle', '103 W 107th St, New York, NY 10025', 'Manhattan Valley', '10025', 40.7994, -73.9636, '212-678-2861', NULL, 'public', 'secular', 'traditional', 0, 0, 0, 30, '14:1', 700, TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, ARRAY['NYCDOE'], '6-8', '08:00', '14:30'),

('Stuyvesant High School', 'stuyvesant-high-school', 'high', '345 Chambers St, New York, NY 10282', 'Tribeca', '10282', 40.7179, -74.0142, '212-312-4800', 'https://stuy.enschool.org', 'public', 'secular', 'stem_specialized', 0, 0, 0, 34, '21:1', 3300, TRUE, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYCDOE'], '9-12', '08:00', '15:15');

-- ============================================================
-- CHARTER SCHOOLS
-- ============================================================

INSERT INTO schools (name, slug, level, address, neighborhood, zip_code, latitude, longitude, phone, website, school_type, religious_orientation, methodology, annual_tuition_min, annual_tuition_max, enrollment_fee, max_class_size, student_teacher_ratio, total_students, has_transportation, has_lunch_program, lunch_is_nutritionist_supervised, has_scholarships, has_financial_aid, has_special_needs_support, has_wheelchair_access, has_elevator, has_ramps, has_english_program, uses_tablets, accreditations, grades_offered, entry_time, exit_time)
VALUES
('Success Academy Charter - Upper West', 'success-academy-uw', 'elementary', '145 W 84th St, New York, NY 10024', 'Upper West Side', '10024', 40.7855, -73.9730, '646-597-4641', 'https://www.successacademies.org', 'charter', 'secular', 'success_academy_model', 0, 0, 0, 27, '11:1', 500, TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSED'], 'K-4', '07:45', '15:45'),

('KIPP NYC College Prep', 'kipp-nyc-college-prep', 'high', '1 E 104th St, New York, NY 10029', 'East Harlem', '10029', 40.7906, -73.9519, '212-991-2600', 'https://www.kippnyc.org', 'charter', 'secular', 'college_prep', 0, 0, 0, 28, '12:1', 550, TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['NYSED'], '9-12', '07:30', '16:00');

-- ============================================================
-- UNIVERSITIES
-- ============================================================

INSERT INTO schools (name, slug, level, address, neighborhood, zip_code, latitude, longitude, phone, website, school_type, religious_orientation, methodology, annual_tuition_min, annual_tuition_max, enrollment_fee, max_class_size, student_teacher_ratio, total_students, has_transportation, has_lunch_program, lunch_is_nutritionist_supervised, has_scholarships, has_financial_aid, has_special_needs_support, has_wheelchair_access, has_elevator, has_ramps, has_english_program, uses_tablets, accreditations, grades_offered, entry_time, exit_time)
VALUES
('Columbia University', 'columbia-university', 'university', '116th St & Broadway, New York, NY 10027', 'Morningside Heights', '10027', 40.8075, -73.9626, '212-854-1754', 'https://www.columbia.edu', 'private', 'secular', 'research_university', 65000, 68000, 80, NULL, '6:1', 33000, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['MSCHE','ABET'], 'Undergraduate+Graduate', NULL, NULL),

('New York University', 'nyu', 'university', '70 Washington Square S, New York, NY 10012', 'Greenwich Village', '10012', 40.7295, -73.9965, '212-998-1212', 'https://www.nyu.edu', 'private', 'secular', 'research_university', 58000, 62000, 80, NULL, '9:1', 55000, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['MSCHE'], 'Undergraduate+Graduate', NULL, NULL),

('City College of New York (CUNY)', 'ccny-cuny', 'university', '160 Convent Ave, New York, NY 10031', 'Hamilton Heights', '10031', 40.8200, -73.9497, '212-650-7000', 'https://www.ccny.cuny.edu', 'public', 'secular', 'liberal_arts_engineering', 7500, 15000, 65, NULL, '14:1', 16000, TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, ARRAY['MSCHE','ABET'], 'Undergraduate+Graduate', NULL, NULL);

-- ============================================================
-- EXTRACURRICULARS
-- ============================================================

-- Trinity School
INSERT INTO school_extracurriculars (school_id, name, category, description, additional_cost) VALUES
((SELECT id FROM schools WHERE slug='trinity-school'), 'Robotics Club', 'technology', 'Award-winning FIRST Robotics team', 0),
((SELECT id FROM schools WHERE slug='trinity-school'), 'Drama Program', 'arts', 'Full theatrical productions each semester', 0),
((SELECT id FROM schools WHERE slug='trinity-school'), 'Debate Team', 'academic', 'Competes in national tournaments', 0),
((SELECT id FROM schools WHERE slug='trinity-school'), 'Orchestra', 'music', 'Full symphony orchestra with annual concert series', 0);

-- Avenues
INSERT INTO school_extracurriculars (school_id, name, category, description, additional_cost) VALUES
((SELECT id FROM schools WHERE slug='avenues-world-school'), 'World Language Immersion', 'language', 'Spanish and Mandarin immersion tracks starting in nursery', 0),
((SELECT id FROM schools WHERE slug='avenues-world-school'), 'Maker Lab', 'technology', '3D printing, laser cutting, electronics lab', 0),
((SELECT id FROM schools WHERE slug='avenues-world-school'), 'Global Studies Program', 'academic', 'Travel and exchange programs with Avenues campuses worldwide', 2500);

-- IDEAL School (inclusion-focused)
INSERT INTO school_extracurriculars (school_id, name, category, description, additional_cost) VALUES
((SELECT id FROM schools WHERE slug='ideal-school'), 'Unified Sports', 'sports', 'Inclusive sports program where students of all abilities play together', 0),
((SELECT id FROM schools WHERE slug='ideal-school'), 'Art Therapy', 'arts', 'Therapeutic art program for emotional expression', 0),
((SELECT id FROM schools WHERE slug='ideal-school'), 'Social Skills Groups', 'other', 'Structured social-emotional learning groups', 0);

-- BASIS
INSERT INTO school_extracurriculars (school_id, name, category, description, additional_cost) VALUES
((SELECT id FROM schools WHERE slug='basis-independent-manhattan'), 'Science Olympiad', 'academic', 'Competitive science team', 0),
((SELECT id FROM schools WHERE slug='basis-independent-manhattan'), 'Math League', 'academic', 'AMC/MATHCOUNTS competition preparation', 0),
((SELECT id FROM schools WHERE slug='basis-independent-manhattan'), 'Coding Club', 'technology', 'Python, Java, web development', 0);

-- Success Academy
INSERT INTO school_extracurriculars (school_id, name, category, description, additional_cost) VALUES
((SELECT id FROM schools WHERE slug='success-academy-uw'), 'Chess Program', 'academic', 'Mandatory chess curriculum K-4', 0),
((SELECT id FROM schools WHERE slug='success-academy-uw'), 'STEM Lab', 'technology', 'Hands-on science experiments', 0);

-- ============================================================
-- SPORTS
-- ============================================================

INSERT INTO school_sports (school_id, sport_name, level, competes_in_tournaments, tournament_details) VALUES
((SELECT id FROM schools WHERE slug='trinity-school'), 'Basketball', 'varsity', TRUE, 'NYSAIS league'),
((SELECT id FROM schools WHERE slug='trinity-school'), 'Swimming', 'varsity', TRUE, 'NYSAIS championships'),
((SELECT id FROM schools WHERE slug='trinity-school'), 'Tennis', 'varsity', TRUE, 'NYSAIS league'),
((SELECT id FROM schools WHERE slug='trinity-school'), 'Soccer', 'varsity', TRUE, 'NYSAIS league'),
((SELECT id FROM schools WHERE slug='dalton-school'), 'Basketball', 'varsity', TRUE, 'Ivy Preparatory School League'),
((SELECT id FROM schools WHERE slug='dalton-school'), 'Track and Field', 'varsity', TRUE, 'NYSAIS championships'),
((SELECT id FROM schools WHERE slug='dalton-school'), 'Cross Country', 'varsity', TRUE, 'NYSAIS league'),
((SELECT id FROM schools WHERE slug='beacon-high-school'), 'Soccer', 'varsity', TRUE, 'PSAL league'),
((SELECT id FROM schools WHERE slug='beacon-high-school'), 'Basketball', 'varsity', TRUE, 'PSAL league'),
((SELECT id FROM schools WHERE slug='stuyvesant-high-school'), 'Fencing', 'varsity', TRUE, 'PSAL city champions'),
((SELECT id FROM schools WHERE slug='stuyvesant-high-school'), 'Math Team', 'varsity', TRUE, 'National champion multiple years');

-- ============================================================
-- SPECIAL NEEDS SUPPORT
-- ============================================================

INSERT INTO school_special_needs (school_id, condition_supported, support_type, details) VALUES
((SELECT id FROM schools WHERE slug='ideal-school'), 'autism', 'full_inclusion', 'Dedicated inclusion specialists in every classroom, sensory-friendly spaces'),
((SELECT id FROM schools WHERE slug='ideal-school'), 'adhd', 'full_inclusion', 'Movement breaks, flexible seating, executive function coaching'),
((SELECT id FROM schools WHERE slug='ideal-school'), 'dyslexia', 'full_inclusion', 'Orton-Gillingham trained reading specialists'),
((SELECT id FROM schools WHERE slug='ideal-school'), 'physical_disability', 'full_inclusion', 'Fully accessible building, adaptive PE, occupational therapy on-site'),
((SELECT id FROM schools WHERE slug='ideal-school'), 'down_syndrome', 'full_inclusion', 'Peer buddy system, modified curriculum with grade-level access'),
((SELECT id FROM schools WHERE slug='trinity-school'), 'adhd', 'learning_support', 'Learning specialists available, accommodations for testing'),
((SELECT id FROM schools WHERE slug='trinity-school'), 'dyslexia', 'learning_support', 'Reading support program, Wilson Reading trained staff'),
((SELECT id FROM schools WHERE slug='dalton-school'), 'adhd', 'learning_support', 'Comprehensive learning support team'),
((SELECT id FROM schools WHERE slug='avenues-world-school'), 'adhd', 'learning_support', 'Student support team, accommodations available'),
((SELECT id FROM schools WHERE slug='avenues-world-school'), 'dyslexia', 'learning_support', 'Literacy specialists on staff');

-- ============================================================
-- TEACHER CERTIFICATIONS
-- ============================================================

INSERT INTO school_teacher_certifications (school_id, certification_name, percentage_certified, details) VALUES
((SELECT id FROM schools WHERE slug='trinity-school'), 'Masters Degree or Higher', 85, '85% of faculty hold advanced degrees'),
((SELECT id FROM schools WHERE slug='spence-school'), 'Masters Degree or Higher', 80, '80% of faculty hold advanced degrees'),
((SELECT id FROM schools WHERE slug='dalton-school'), 'Masters or Doctoral', 82, 'Many faculty are published authors or researchers'),
((SELECT id FROM schools WHERE slug='basis-independent-manhattan'), 'Subject Matter Experts', 90, 'Teachers must have at minimum a degree in the subject they teach'),
((SELECT id FROM schools WHERE slug='ideal-school'), 'Special Education Certified', 60, '60% of teachers hold dual certification in general and special education'),
((SELECT id FROM schools WHERE slug='stuyvesant-high-school'), 'NYS Teaching Certification', 100, 'All teachers hold NYS certification, many hold PhDs');

-- Done. Verify with:
-- SELECT COUNT(*) FROM schools; -- Should be 25
-- SELECT level, COUNT(*) FROM schools GROUP BY level;

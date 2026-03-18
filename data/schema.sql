-- EduScout Database Schema
-- DigitalOcean Managed PostgreSQL
-- Run: psql $DATABASE_URL -f schema.sql

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- SCHOOL DATA
-- ============================================================

CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    level VARCHAR(50) NOT NULL CHECK (level IN ('kindergarten','elementary','middle','high','k12','university')),
    address TEXT NOT NULL,
    borough VARCHAR(50) DEFAULT 'Manhattan',
    neighborhood VARCHAR(100),
    zip_code VARCHAR(10),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(500),
    whatsapp VARCHAR(20),
    school_type VARCHAR(50) DEFAULT 'private' CHECK (school_type IN ('public','private','charter','parochial')),
    religious_orientation VARCHAR(50) DEFAULT 'secular',
    methodology VARCHAR(100),
    annual_tuition_min DECIMAL(10,2),
    annual_tuition_max DECIMAL(10,2),
    enrollment_fee DECIMAL(10,2),
    max_class_size INTEGER,
    student_teacher_ratio VARCHAR(10),
    total_students INTEGER,
    has_transportation BOOLEAN DEFAULT FALSE,
    transportation_cost_annual DECIMAL(10,2),
    has_lunch_program BOOLEAN DEFAULT FALSE,
    lunch_is_nutritionist_supervised BOOLEAN DEFAULT FALSE,
    has_scholarships BOOLEAN DEFAULT FALSE,
    scholarship_details TEXT,
    has_financial_aid BOOLEAN DEFAULT FALSE,
    has_special_needs_support BOOLEAN DEFAULT FALSE,
    special_needs_details TEXT,
    has_wheelchair_access BOOLEAN DEFAULT FALSE,
    has_elevator BOOLEAN DEFAULT FALSE,
    has_ramps BOOLEAN DEFAULT FALSE,
    has_english_program BOOLEAN DEFAULT FALSE,
    uses_tablets BOOLEAN DEFAULT FALSE,
    accreditations TEXT[],
    awards TEXT[],
    grades_offered VARCHAR(20),
    entry_time TIME,
    exit_time TIME,
    data_source VARCHAR(50) DEFAULT 'seed',
    data_confidence VARCHAR(20) DEFAULT 'verified',
    last_verified_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE school_extracurriculars (
    id SERIAL PRIMARY KEY,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) CHECK (category IN ('sports','arts','academic','technology','music','language','community_service','other')),
    description TEXT,
    additional_cost DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE school_sports (
    id SERIAL PRIMARY KEY,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    sport_name VARCHAR(100) NOT NULL,
    level VARCHAR(50),
    competes_in_tournaments BOOLEAN DEFAULT FALSE,
    tournament_details TEXT
);

CREATE TABLE school_special_needs (
    id SERIAL PRIMARY KEY,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    condition_supported VARCHAR(100) NOT NULL,
    support_type VARCHAR(100),
    details TEXT
);

CREATE TABLE school_teacher_certifications (
    id SERIAL PRIMARY KEY,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    certification_name VARCHAR(255) NOT NULL,
    percentage_certified INTEGER,
    details TEXT
);

CREATE TABLE school_documents (
    id SERIAL PRIMARY KEY,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    document_type VARCHAR(50) CHECK (document_type IN ('regulation','study_plan','flyer','requirements','scholarship','calendar','handbook','other')),
    title VARCHAR(255) NOT NULL,
    spaces_url TEXT,
    file_name VARCHAR(255),
    kb_indexed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PARENT / USER DATA
-- ============================================================

CREATE TABLE parents (
    id SERIAL PRIMARY KEY,
    whatsapp_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    work_address TEXT,
    work_latitude DECIMAL(10,8),
    work_longitude DECIMAL(11,8),
    home_address TEXT,
    home_latitude DECIMAL(10,8),
    home_longitude DECIMAL(11,8),
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE search_sessions (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES parents(id) ON DELETE CASCADE,
    student_name VARCHAR(255),
    target_level VARCHAR(50),
    budget_max DECIMAL(10,2),
    interests TEXT[],
    special_needs TEXT[],
    religious_preference VARCHAR(50),
    preferred_neighborhood VARCHAR(100),
    preferred_methodology VARCHAR(100),
    needs_transportation BOOLEAN,
    needs_wheelchair_access BOOLEAN,
    needs_lunch_program BOOLEAN,
    additional_requirements JSONB DEFAULT '{}',
    intake_complete BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','completed','abandoned')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES search_sessions(id) ON DELETE CASCADE,
    school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
    match_score DECIMAL(5,2),
    reasoning TEXT,
    commute_from_home_minutes INTEGER,
    commute_from_work_minutes INTEGER,
    traffic_adjusted_home_minutes INTEGER,
    traffic_adjusted_work_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ASYNC TASK TRACKING
-- ============================================================

CREATE TABLE agent_tasks (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES search_sessions(id) ON DELETE SET NULL,
    school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
    parent_id INTEGER REFERENCES parents(id) ON DELETE SET NULL,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('phone_call','web_scrape','email','whatsapp_inquiry')),
    question TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','in_progress','completed','failed')),
    result TEXT,
    vapi_call_id VARCHAR(255),
    call_transcript TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- ============================================================
-- CONVERSATION MEMORY
-- ============================================================

CREATE TABLE conversation_messages (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES parents(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES search_sessions(id) ON DELETE SET NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_schools_level ON schools(level);
CREATE INDEX idx_schools_borough ON schools(borough);
CREATE INDEX idx_schools_neighborhood ON schools(neighborhood);
CREATE INDEX idx_schools_type ON schools(school_type);
CREATE INDEX idx_schools_tuition ON schools(annual_tuition_min, annual_tuition_max);
CREATE INDEX idx_schools_location ON schools(latitude, longitude);
CREATE INDEX idx_schools_wheelchair ON schools(has_wheelchair_access);
CREATE INDEX idx_schools_special_needs ON schools(has_special_needs_support);
CREATE INDEX idx_schools_scholarships ON schools(has_scholarships);

CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_agent_tasks_session ON agent_tasks(session_id);
CREATE INDEX idx_search_sessions_parent ON search_sessions(parent_id);
CREATE INDEX idx_search_sessions_status ON search_sessions(status);
CREATE INDEX idx_conversation_parent ON conversation_messages(parent_id);
CREATE INDEX idx_conversation_session ON conversation_messages(session_id);
CREATE INDEX idx_recommendations_session ON recommendations(session_id);

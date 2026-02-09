-- Run this in psql or pgAdmin to create a dedicated user for the project
-- First, connect as superuser (postgres)

-- Create a new user
CREATE USER tvirtebis_user WITH PASSWORD 'admin123';

-- Create the database
CREATE DATABASE tvirtebis_platform OWNER tvirtebis_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tvirtebis_platform TO tvirtebis_user;

-- Connect to the new database
\c tvirtebis_platform

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO tvirtebis_user;

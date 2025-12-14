CREATE DATABASE FitHub;
USE FitHub;

CREATE TABLE app_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    handle VARCHAR(50) UNIQUE NOT NULL,
    contact_email VARCHAR(100) UNIQUE NOT NULL,
    security_hash VARCHAR(255) NOT NULL,
    account_type VARCHAR(20) DEFAULT 'client'
);

CREATE TABLE workouts (
    workout_id INT AUTO_INCREMENT PRIMARY KEY,
    creator_id INT NOT NULL,
    workout_name VARCHAR(100) NOT NULL,
    details TEXT,
    cost DECIMAL(10, 2) NOT NULL,
    program_length INT NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES app_members(member_id) ON DELETE CASCADE
);

CREATE TABLE enrollments (
    enroll_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    workout_id INT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES app_members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (workout_id) REFERENCES workouts(workout_id) ON DELETE CASCADE,
    UNIQUE(client_id, workout_id)
);


CREATE TABLE connections (
    fan_id INT NOT NULL,
    coach_id INT NOT NULL,
    PRIMARY KEY (fan_id, coach_id),
    FOREIGN KEY (fan_id) REFERENCES app_members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES app_members(member_id) ON DELETE CASCADE
);
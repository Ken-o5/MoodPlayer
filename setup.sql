-- MoodPlayer database setup
-- Run with:  mysql -u root -p < setup.sql

CREATE DATABASE IF NOT EXISTS musicplayerdb;
USE musicplayerdb;

CREATE TABLE IF NOT EXISTS mood_folders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    mood        VARCHAR(50)  NOT NULL UNIQUE,
    folder_path VARCHAR(255) NOT NULL
);

-- One row per mood. folder_path must be a real folder on your computer
-- that contains .mp3 files. Keep mood names in lowercase, because the app
-- lowercases whatever the user types before searching.
INSERT INTO mood_folders (mood, folder_path) VALUES
    ('happy',     'C:/Music/happy/'),
    ('sad',       'C:/Music/sad/'),
    ('energetic', 'C:/Music/energetic/'),
    ('calm',      'C:/Music/calm/')
ON DUPLICATE KEY UPDATE folder_path = VALUES(folder_path);

-- To add a new mood later:
-- INSERT INTO mood_folders (mood, folder_path) VALUES ('romantic', 'C:/Music/romantic/');

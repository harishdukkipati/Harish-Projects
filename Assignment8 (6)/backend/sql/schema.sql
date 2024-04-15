--
-- All SQL statements must be on a single line and end in a semicolon.
--

-- Dummy table --
DROP TABLE IF EXISTS dummy;
CREATE TABLE dummy(created TIMESTAMP WITH TIME ZONE);

-- Your database schema goes here --
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users(id UUID PRIMARY KEY, user_data JSONB NOT NULL);

DROP TABLE IF EXISTS workspaces CASCADE;
CREATE TABLE workspaces(id UUID PRIMARY KEY, workspace_data JSONB NOT NULL);

DROP TABLE IF EXISTS users_workspaces CASCADE;
CREATE TABLE users_workspaces(user_id UUID REFERENCES users(id), workspace_id UUID REFERENCES workspaces(id), PRIMARY KEY (user_id, workspace_id));

DROP TABLE IF EXISTS channels CASCADE;
CREATE TABLE channels(id UUID PRIMARY KEY, workspace_id UUID REFERENCES workspaces(id), channel_data JSONB NOT NULL);

DROP TABLE IF EXISTS messages CASCADE;
CREATE TABLE messages(id UUID PRIMARY KEY, channel_id UUID REFERENCES channels(id), user_id UUID REFERENCES users(id), message_data JSONB NOT NULL);
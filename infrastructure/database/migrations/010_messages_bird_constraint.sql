-- msgs_bird is NOT globally unique: the Bird API returns the same message
-- IDs across multiple conversations (e.g. archived/continuation conversations).
-- Make the uniqueness scoped per conversation instead.
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_msgs_bird_key;
CREATE UNIQUE INDEX IF NOT EXISTS messages_msgs_cnvs_bird_uidx ON messages (msgs_cnvs, msgs_bird);
-- Remove colunas placeholders nunca escritas/lidas
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom1;
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom2;
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom3;
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom4;
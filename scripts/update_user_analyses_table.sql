-- Script SQL alternativo para agregar columnas faltantes SIN eliminar datos
-- Usa este script si ya tienes datos en la tabla y quieres preservarlos

-- Agregar columnas si no existen
DO $$
BEGIN
    -- Agregar identified_risks si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'identified_risks'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN identified_risks JSONB DEFAULT '[]'::jsonb;
    END IF;

    -- Agregar action_items si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'action_items'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN action_items JSONB DEFAULT '[]'::jsonb;
    END IF;

    -- Agregar otras columnas si no existen
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'thread_id'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN thread_id TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'doc_type'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN doc_type TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'simplified_explanation'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN simplified_explanation TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'confidence_score'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN confidence_score REAL DEFAULT 0.0;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'language'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN language TEXT DEFAULT 'es';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'raw_text'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN raw_text TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_analyses' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE user_analyses 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- Crear índices si no existen
CREATE INDEX IF NOT EXISTS idx_user_analyses_thread_id ON user_analyses(thread_id);
CREATE INDEX IF NOT EXISTS idx_user_analyses_created_at ON user_analyses(created_at DESC);

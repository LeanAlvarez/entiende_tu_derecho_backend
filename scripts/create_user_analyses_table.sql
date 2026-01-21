-- Script SQL para crear o actualizar la tabla user_analyses en Supabase
-- Ejecutar este script en Supabase SQL Editor

-- Eliminar la tabla si existe para recrearla desde cero
DROP TABLE IF EXISTS user_analyses CASCADE;

-- Crear la tabla con todas las columnas necesarias
CREATE TABLE user_analyses (
    id BIGSERIAL PRIMARY KEY,
    thread_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    doc_type TEXT,
    simplified_explanation TEXT,
    identified_risks JSONB DEFAULT '[]'::jsonb,
    action_items JSONB DEFAULT '[]'::jsonb,
    confidence_score REAL DEFAULT 0.0,
    language TEXT DEFAULT 'es',
    raw_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índice en user_id para búsquedas rápidas por usuario
CREATE INDEX idx_user_analyses_user_id ON user_analyses(user_id);

-- Crear índice en thread_id para búsquedas rápidas
CREATE INDEX idx_user_analyses_thread_id ON user_analyses(thread_id);

-- Crear índice compuesto para búsquedas por usuario y fecha
CREATE INDEX idx_user_analyses_user_created ON user_analyses(user_id, created_at DESC);

-- Crear índice en created_at para ordenamiento temporal
CREATE INDEX idx_user_analyses_created_at ON user_analyses(created_at DESC);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER update_user_analyses_updated_at
    BEFORE UPDATE ON user_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentación
COMMENT ON TABLE user_analyses IS 'Tabla para almacenar los análisis de documentos legales realizados por los usuarios';
COMMENT ON COLUMN user_analyses.user_id IS 'ID del usuario autenticado (de Supabase Auth)';
COMMENT ON COLUMN user_analyses.thread_id IS 'ID único del thread/conversación del usuario';
COMMENT ON COLUMN user_analyses.identified_risks IS 'Lista de riesgos identificados en formato JSON';
COMMENT ON COLUMN user_analyses.action_items IS 'Lista de acciones sugeridas en formato JSON';

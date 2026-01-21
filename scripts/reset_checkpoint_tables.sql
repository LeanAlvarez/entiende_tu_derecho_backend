-- Script SQL para eliminar y recrear las tablas de checkpoint
-- Ejecutar este script en Supabase SQL Editor si las tablas tienen esquemas antiguos

-- Eliminar TODAS las tablas relacionadas con checkpoints
DROP TABLE IF EXISTS checkpoints CASCADE;
DROP TABLE IF EXISTS checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS checkpoint_writes CASCADE;
DROP TABLE IF EXISTS checkpoint_migrations CASCADE;

-- Las tablas se recrearán automáticamente cuando se ejecute setup()
-- Ejecuta la aplicación nuevamente después de ejecutar este script
-- El setup() creará todas las tablas necesarias desde cero

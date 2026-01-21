-- Script SQL para configurar las políticas RLS correctas para user_analyses
-- Ejecutar este script en Supabase SQL Editor

-- Primero, habilitar RLS en la tabla si no está habilitado
ALTER TABLE user_analyses ENABLE ROW LEVEL SECURITY;

-- Eliminar políticas existentes si las hay (para recrearlas)
DROP POLICY IF EXISTS "Permitir insercion a dueños" ON user_analyses;
DROP POLICY IF EXISTS "Permitir lectura a dueños" ON user_analyses;
DROP POLICY IF EXISTS "Los usuarios pueden ver sus propios análisis" ON user_analyses;

-- Política para INSERT: Los usuarios autenticados solo pueden insertar filas con su propio user_id
-- IMPORTANTE: Convertir user_id (TEXT) a UUID para comparar con auth.uid() (UUID)
-- Esto evita el error de tipos "text = uuid"
CREATE POLICY "Permitir insercion a dueños"
ON user_analyses
FOR INSERT
TO authenticated
WITH CHECK (auth.uid()::uuid = user_id::uuid);

-- Política para SELECT: Los usuarios autenticados solo pueden ver sus propios análisis
CREATE POLICY "Permitir lectura a dueños"
ON user_analyses
FOR SELECT
TO authenticated
USING (auth.uid()::uuid = user_id::uuid);

-- Política adicional para UPDATE: Los usuarios pueden actualizar sus propios análisis
CREATE POLICY "Permitir actualizacion a dueños"
ON user_analyses
FOR UPDATE
TO authenticated
USING (auth.uid()::uuid = user_id::uuid)
WITH CHECK (auth.uid()::uuid = user_id::uuid);

-- Política adicional para DELETE: Los usuarios pueden eliminar sus propios análisis
CREATE POLICY "Permitir eliminacion a dueños"
ON user_analyses
FOR DELETE
TO authenticated
USING (auth.uid()::uuid = user_id::uuid);

-- Verificar las políticas creadas
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'user_analyses'
ORDER BY policyname;

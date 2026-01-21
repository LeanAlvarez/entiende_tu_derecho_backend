# Documentación de API - EntiendeTuDerecho AI

Esta documentación describe cómo consumir los endpoints del backend desde el frontend (React Native o web).

## 📋 Tabla de Contenidos

- [Configuración Base](#configuración-base)
- [Autenticación](#autenticación)
- [Endpoints](#endpoints)
  - [Analizar Documento](#1-analizar-documento)
  - [Obtener Historial](#2-obtener-historial)
  - [Obtener Análisis por Thread ID](#3-obtener-análisis-por-thread-id)
- [Códigos de Error](#códigos-de-error)
- [Ejemplos Completos](#ejemplos-completos)

---

## Configuración Base

### URL Base

```
Producción: https://tu-dominio.com
Desarrollo: http://localhost:8000
```

### Headers Comunes

Todos los endpoints requieren el siguiente header para autenticación:

```
Authorization: Bearer <TOKEN>
Content-Type: application/json (excepto para /analyze que usa multipart/form-data)
```

---

## Autenticación

El backend utiliza **Supabase Auth** con tokens JWT. El frontend debe:

1. Autenticar al usuario con Supabase Auth
2. Obtener el `access_token` del usuario
3. Incluir el token en el header `Authorization: Bearer <TOKEN>` en todas las peticiones

### Ejemplo de Autenticación (Supabase)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'usuario@ejemplo.com',
  password: 'password123'
})

// Obtener token
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

// Usar token en peticiones
const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

---

## Endpoints

### 1. Analizar Documento

**Endpoint:** `POST /api/v1/analyze`

**Descripción:** Analiza un documento legal desde una imagen usando OCR y IA.

**Autenticación:** ✅ Requerida

**Content-Type:** `multipart/form-data`

**Parámetros:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `image` | File | ✅ Sí | Archivo de imagen del documento (JPEG, PNG, etc.) |
| `thread_id` | String | ❌ No | ID del thread/conversación. Si no se proporciona, se genera automáticamente con formato `user_{user_id}_{uuid}` |

**Formato del `thread_id`:**

El `thread_id` debe seguir el formato: `user_{user_id}_{uuid}`

- Si no se envía, el backend lo genera automáticamente
- Si se envía sin el prefijo `user_`, el backend lo agrega automáticamente
- Si se envía con un `user_id` diferente al del token, el backend lo corrige

**Request Example (JavaScript/TypeScript):**

```typescript
async function analyzeDocument(imageUri: string, token: string, threadId?: string) {
  // Crear FormData
  const formData = new FormData()
  
  // En React Native, necesitas convertir la URI a un objeto File/Blob
  // Ejemplo con react-native-image-picker o similar:
  const imageFile = {
    uri: imageUri,
    type: 'image/jpeg', // o 'image/png'
    name: 'document.jpg'
  }
  
  formData.append('image', imageFile as any)
  
  if (threadId) {
    formData.append('thread_id', threadId)
  }
  
  const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      // NO incluir 'Content-Type' - el navegador lo hace automáticamente para FormData
    },
    body: formData
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Error al analizar el documento')
  }
  
  return await response.json()
}
```

**Request Example (React Native con axios):**

```typescript
import axios from 'axios'
import FormData from 'form-data'

async function analyzeDocument(imagePath: string, token: string, threadId?: string) {
  const formData = new FormData()
  
  formData.append('image', {
    uri: imagePath,
    type: 'image/jpeg',
    name: 'document.jpg'
  })
  
  if (threadId) {
    formData.append('thread_id', threadId)
  }
  
  const response = await axios.post(
    `${API_BASE_URL}/api/v1/analyze`,
    formData,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    }
  )
  
  return response.data
}
```

**Response Success (200 OK):**

```json
{
  "thread_id": "user_42b56263-5335-49a7-a668-6ad9fc28c2bc_abc123def456",
  "error": false,
  "raw_text": "Texto completo extraído del documento mediante OCR...",
  "doc_type": "Convenio de Pago Especial",
  "simplified_explanation": "• El Convenio de Pago Especial de Enersa es una oportunidad...\n• Para acceder a este beneficio...\n• El convenio es válido para usuarios...",
  "identified_risks": [
    "Es importante destacar que si el usuario incumple con el pago...",
    "La tasa de interés reducida solo se aplica si el usuario mantiene al día...",
    "Los usuarios deben verificar que sus pagos estén reflejados..."
  ],
  "action_items": [
    "Verificar si se cumple con los requisitos para acceder al Convenio...",
    "Revisar la factura para verificar el estado de deuda...",
    "Preparar la documentación necesaria..."
  ],
  "confidence_score": 1.0,
  "language": "es"
}
```

**Response Error (200 OK con error):**

Si el OCR falla o el texto es ilegible, el endpoint retorna `200 OK` pero con `error: true`:

```json
{
  "thread_id": "user_42b56263-5335-49a7-a668-6ad9fc28c2bc_abc123def456",
  "error": true,
  "error_message": "El texto extraído es demasiado corto o ilegible. Por favor, toma una foto más clara del documento.",
  "doc_type": "",
  "simplified_explanation": "",
  "identified_risks": [],
  "action_items": [],
  "confidence_score": 0.0,
  "language": "es"
}
```

**Códigos de Error HTTP:**

- `401 Unauthorized`: Token inválido o expirado
- `500 Internal Server Error`: Error del servidor al procesar el documento
- `503 Service Unavailable`: El grafo no está inicializado (esperar unos segundos)

---

### 2. Obtener Historial

**Endpoint:** `GET /api/v1/history`

**Descripción:** Obtiene el historial de análisis de documentos del usuario autenticado con paginación.

**Autenticación:** ✅ Requerida

**Query Parameters:**

| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `limit` | Integer | ❌ No | 10 | Número máximo de análisis a retornar (1-100) |
| `offset` | Integer | ❌ No | 0 | Número de análisis a omitir para paginación |

**Request Example:**

```typescript
async function getHistory(token: string, limit: number = 10, offset: number = 0) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/history?limit=${limit}&offset=${offset}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  )
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Error al obtener el historial')
  }
  
  return await response.json()
}
```

**Response Success (200 OK):**

```json
{
  "user_id": "42b56263-5335-49a7-a668-6ad9fc28c2bc",
  "analyses": [
    {
      "id": 1,
      "thread_id": "user_42b56263-5335-49a7-a668-6ad9fc28c2bc_abc123def456",
      "user_id": "42b56263-5335-49a7-a668-6ad9fc28c2bc",
      "doc_type": "Convenio de Pago Especial",
      "simplified_explanation": "• El Convenio de Pago Especial...",
      "identified_risks": ["Riesgo 1", "Riesgo 2"],
      "action_items": ["Acción 1", "Acción 2"],
      "confidence_score": 1.0,
      "language": "es",
      "raw_text": "Texto completo del documento...",
      "created_at": "2026-01-21T20:31:25.123456Z",
      "updated_at": "2026-01-21T20:31:25.123456Z"
    },
    {
      "id": 2,
      "thread_id": "user_42b56263-5335-49a7-a668-6ad9fc28c2bc_xyz789ghi012",
      "user_id": "42b56263-5335-49a7-a668-6ad9fc28c2bc",
      "doc_type": "Contrato de Alquiler",
      "simplified_explanation": "• Este contrato establece...",
      "identified_risks": ["Riesgo 1"],
      "action_items": ["Acción 1"],
      "confidence_score": 0.95,
      "language": "es",
      "raw_text": "Texto completo del documento...",
      "created_at": "2026-01-20T15:20:10.123456Z",
      "updated_at": "2026-01-20T15:20:10.123456Z"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0,
  "has_more": true
}
```

**Códigos de Error HTTP:**

- `401 Unauthorized`: Token inválido o expirado
- `500 Internal Server Error`: Error del servidor
- `503 Service Unavailable`: Servicio de base de datos no disponible

---

### 3. Obtener Análisis por Thread ID

**Endpoint:** `GET /api/v1/history/{thread_id}`

**Descripción:** Obtiene un análisis específico por su `thread_id`. Solo retorna el análisis si pertenece al usuario autenticado.

**Autenticación:** ✅ Requerida

**Path Parameters:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `thread_id` | String | ✅ Sí | ID del thread/conversación del análisis |

**Request Example:**

```typescript
async function getAnalysisByThreadId(threadId: string, token: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/history/${threadId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  )
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Error al obtener el análisis')
  }
  
  return await response.json()
}
```

**Response Success (200 OK):**

```json
{
  "user_id": "42b56263-5335-49a7-a668-6ad9fc28c2bc",
  "analysis": {
    "id": 1,
    "thread_id": "user_42b56263-5335-49a7-a668-6ad9fc28c2bc_abc123def456",
    "user_id": "42b56263-5335-49a7-a668-6ad9fc28c2bc",
    "doc_type": "Convenio de Pago Especial",
    "simplified_explanation": "• El Convenio de Pago Especial...",
    "identified_risks": ["Riesgo 1", "Riesgo 2"],
    "action_items": ["Acción 1", "Acción 2"],
    "confidence_score": 1.0,
    "language": "es",
    "raw_text": "Texto completo del documento...",
    "created_at": "2026-01-21T20:31:25.123456Z",
    "updated_at": "2026-01-21T20:31:25.123456Z"
  }
}
```

**Códigos de Error HTTP:**

- `401 Unauthorized`: Token inválido o expirado
- `404 Not Found`: Análisis no encontrado o no tienes permisos para acceder a él
- `500 Internal Server Error`: Error del servidor
- `503 Service Unavailable`: Servicio de base de datos no disponible

---

## Códigos de Error

### Errores HTTP Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| `401` | Token inválido o expirado | Renovar el token con Supabase Auth |
| `404` | Recurso no encontrado | Verificar que el `thread_id` existe y pertenece al usuario |
| `500` | Error interno del servidor | Reintentar la petición o contactar soporte |
| `503` | Servicio no disponible | Esperar unos segundos y reintentar |

### Errores en el Response (error: true)

Cuando el endpoint `/analyze` retorna `200 OK` pero con `error: true`, significa que:

- El OCR no pudo extraer texto suficiente
- El texto es ilegible o tiene mucho ruido
- El documento no es válido

**Solución:** Pedir al usuario que tome una foto más clara del documento.

---

## Ejemplos Completos

### Ejemplo: Cliente API Completo (TypeScript)

```typescript
// api/client.ts

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'

interface AnalyzeResponse {
  thread_id: string
  error: boolean
  error_message?: string
  raw_text?: string
  doc_type?: string
  simplified_explanation?: string
  identified_risks?: string[]
  action_items?: string[]
  confidence_score?: number
  language?: string
}

interface Analysis {
  id: number
  thread_id: string
  user_id: string
  doc_type: string
  simplified_explanation: string
  identified_risks: string[]
  action_items: string[]
  confidence_score: number
  language: string
  raw_text: string
  created_at: string
  updated_at: string
}

interface HistoryResponse {
  user_id: string
  analyses: Analysis[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

class EntiendeTuDerechoAPI {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  setToken(token: string) {
    this.token = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    if (!this.token) {
      throw new Error('Token no configurado. Llama a setToken() primero.')
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return await response.json()
  }

  async analyzeDocument(
    imageFile: File | Blob | { uri: string; type: string; name: string },
    threadId?: string
  ): Promise<AnalyzeResponse> {
    const formData = new FormData()
    
    // Manejar diferentes tipos de archivo
    if (imageFile instanceof File || imageFile instanceof Blob) {
      formData.append('image', imageFile)
    } else {
      // React Native
      formData.append('image', imageFile as any)
    }
    
    if (threadId) {
      formData.append('thread_id', threadId)
    }

    return this.request<AnalyzeResponse>('/api/v1/analyze', {
      method: 'POST',
      body: formData,
      // NO incluir Content-Type - el navegador lo hace automáticamente
    })
  }

  async getHistory(limit: number = 10, offset: number = 0): Promise<HistoryResponse> {
    return this.request<HistoryResponse>(
      `/api/v1/history?limit=${limit}&offset=${offset}`
    )
  }

  async getAnalysisByThreadId(threadId: string): Promise<{ user_id: string; analysis: Analysis }> {
    return this.request<{ user_id: string; analysis: Analysis }>(
      `/api/v1/history/${threadId}`
    )
  }
}

export default EntiendeTuDerechoAPI
```

### Ejemplo: Uso en React Native

```typescript
// App.tsx o componente similar

import { useState, useEffect } from 'react'
import { View, Button, Image, Text } from 'react-native'
import * as ImagePicker from 'expo-image-picker'
import EntiendeTuDerechoAPI from './api/client'
import { useAuth } from './hooks/useAuth' // Hook personalizado para Supabase Auth

export default function DocumentAnalysisScreen() {
  const [api] = useState(() => new EntiendeTuDerechoAPI())
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.access_token) {
      api.setToken(session.access_token)
    }
  }, [session])

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    })

    if (!result.canceled && result.assets[0]) {
      await analyzeDocument(result.assets[0].uri)
    }
  }

  const analyzeDocument = async (imageUri: string) => {
    setLoading(true)
    setResult(null)

    try {
      const imageFile = {
        uri: imageUri,
        type: 'image/jpeg',
        name: 'document.jpg',
      }

      const response = await api.analyzeDocument(imageFile)
      setResult(response)
    } catch (error) {
      console.error('Error:', error)
      alert(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <View>
      <Button title="Seleccionar Documento" onPress={pickImage} disabled={loading} />
      
      {loading && <Text>Analizando documento...</Text>}
      
      {result && (
        <View>
          {result.error ? (
            <Text style={{ color: 'red' }}>{result.error_message}</Text>
          ) : (
            <>
              <Text>Tipo: {result.doc_type}</Text>
              <Text>Confianza: {result.confidence_score}</Text>
              <Text>Resumen: {result.simplified_explanation}</Text>
              <Text>Riesgos: {result.identified_risks?.join(', ')}</Text>
              <Text>Acciones: {result.action_items?.join(', ')}</Text>
            </>
          )}
        </View>
      )}
    </View>
  )
}
```

### Ejemplo: Uso en React Web

```typescript
// DocumentAnalysis.tsx

import { useState } from 'react'
import EntiendeTuDerechoAPI from './api/client'
import { useSupabaseClient } from '@supabase/auth-helpers-react'

export default function DocumentAnalysis() {
  const [api] = useState(() => new EntiendeTuDerechoAPI())
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const supabase = useSupabaseClient()

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Obtener token
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) {
      alert('No estás autenticado')
      return
    }

    api.setToken(session.access_token)
    setLoading(true)

    try {
      const response = await api.analyzeDocument(file)
      setResult(response)
    } catch (error) {
      console.error('Error:', error)
      alert(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        disabled={loading}
      />
      
      {loading && <p>Analizando documento...</p>}
      
      {result && (
        <div>
          {result.error ? (
            <p style={{ color: 'red' }}>{result.error_message}</p>
          ) : (
            <>
              <h3>Tipo: {result.doc_type}</h3>
              <p>Confianza: {result.confidence_score}</p>
              <p>Resumen: {result.simplified_explanation}</p>
              <ul>
                <li>Riesgos: {result.identified_risks?.join(', ')}</li>
                <li>Acciones: {result.action_items?.join(', ')}</li>
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  )
}
```

---

## Notas Importantes

1. **Autenticación Obligatoria**: Todos los endpoints requieren un token válido de Supabase Auth.

2. **Formato de Thread ID**: El `thread_id` debe seguir el formato `user_{user_id}_{uuid}`. El backend lo normaliza automáticamente si no sigue este formato.

3. **CORS**: El backend está configurado para aceptar peticiones desde cualquier origen (`*`). En producción, deberías restringir esto a tu dominio.

4. **Tamaño de Imagen**: Asegúrate de que las imágenes no sean demasiado grandes. El OCR funciona mejor con imágenes claras y de buena calidad.

5. **Manejo de Errores**: Siempre verifica el campo `error` en la respuesta de `/analyze` antes de mostrar los resultados.

6. **Paginación**: Usa los parámetros `limit` y `offset` para implementar paginación en el historial.

---

## Soporte

Para más información o reportar problemas, contacta al equipo de desarrollo.

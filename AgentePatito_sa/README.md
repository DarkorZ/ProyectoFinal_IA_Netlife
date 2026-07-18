# ProyectoFinal_IA_Semillero

Desarrollo del proyecto final del Semillero de Inteligencia Artificial de "IA estamos".

El objetivo es construir una solución con agentes LangChain y Google Gemini, utilizando bases de conocimiento independientes, recuperación semántica con RAG, trazabilidad de fuentes y una arquitectura separada por componentes.

---

## Bloque 1 — Configuración inicial

### 1. Crear el entorno virtual

```bash
python -m venv .venv
```

Activar el entorno virtual en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Actualizar pip y certificados

```bash
python -m pip install --upgrade pip certifi
```

En caso de problemas de certificados SSL:

```powershell
python -m pip install --upgrade pip certifi `
  --trusted-host pypi.org `
  --trusted-host files.pythonhosted.org
```

También se debe comprobar que la fecha y hora del equipo sean correctas, ya que una configuración incorrecta puede generar errores durante la instalación de dependencias.

### 3. Instalar los requerimientos

Se creó el archivo:

```text
requirements.txt
```

Luego se instalaron las dependencias:

```bash
pip install -r requirements.txt
```

Entre las principales librerías utilizadas se encuentran:

* LangChain.
* LangGraph.
* Google Gemini para LangChain.
* ChromaDB.
* Streamlit.
* Python Dotenv.
* Pydantic.
* Pillow.

### 4. Comprobar la instalación

```bash
pip show langchain
pip show langchain-google-genai
pip show langchain-chroma
```

### 5. Configurar variables de entorno

Se creó un archivo `.env` en la raíz del proyecto:

```env
GOOGLE_API_KEY=API_KEY_DE_GOOGLE
```

La clave no se almacena directamente en el código y el archivo `.env` se excluye del repositorio mediante `.gitignore`.

También se creó:

```text
.env.example
```

para mostrar la estructura necesaria sin compartir la credencial real.

### 6. Preparar la estructura del proyecto

Se crearon carpetas independientes para:

```text
data/
src/
src/agents/
src/tools/
tests/
vectorstores/
outputs/
assets/
```

También se utilizaron archivos `.gitkeep` para conservar las carpetas vacías dentro del repositorio.

### 7. Centralizar la configuración

Se creó:

```text
src/config.py
```

Este archivo contiene:

* Rutas principales del proyecto.
* Nombres de los modelos.
* Parámetros de generación.
* Parámetros RAG.
* Rutas de los documentos.
* Rutas de los índices vectoriales.
* Validaciones de configuración.

También se creó:

```text
src/modelos.py
```

Este módulo permite construir de forma centralizada:

* El modelo de chat de Gemini.
* El modelo de embeddings.

### 8. Validar la conexión con Gemini

Se creó:

```text
tests/test_conexion.py
```

La prueba valida:

* La existencia de la API key.
* La existencia de los documentos.
* La conexión con el modelo de chat.
* La generación de embeddings.
* La latencia de cada solicitud.

Durante la prueba se detectó que el modelo configurado inicialmente ya no estaba disponible para usuarios nuevos.

Se actualizó el modelo a:

```python
MODELO_LLM = "gemini-3.5-flash"
```

Finalmente, se obtuvo una conexión correcta tanto con Gemini Chat como con Gemini Embeddings.

---

## Bloque 2 — Preparación de las bases RAG

El Bloque 2 se divide en:

```text
2.1 Cargar y fragmentar los tres documentos
2.2 Generar los tres índices Chroma
2.3 Abrir los índices existentes
2.4 Probar la recuperación semántica
```

### 2.1 Carga y fragmentación

Se creó:

```text
src/indexacion.py
```

Este módulo permite:

* Leer los tres documentos TXT.
* Convertirlos en objetos `Document` de LangChain.
* Dividirlos mediante `RecursiveCharacterTextSplitter`.
* Agregar metadatos de trazabilidad.

Los parámetros utilizados fueron:

```python
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
TOP_K = 3
```

Cada fragmento contiene metadatos como:

```text
source
agent
document_type
chunk_id
characters
```

Se creó la prueba:

```text
tests/test_fragmentacion.py
```

Resultado obtenido:

```text
Catálogo: 3 fragmentos
Políticas: 4 fragmentos
CRM: 3 fragmentos
Total: 10 fragmentos
```

Los tres documentos se fragmentaron correctamente.

### 2.2 Generación de índices Chroma

Se añadieron funciones para:

* Limpiar índices anteriores.
* Generar identificadores únicos para cada fragmento.
* Crear una colección Chroma por documento.
* Persistir los índices localmente.
* Evitar duplicados al reconstruir las bases.

Se creó el script:

```text
generar_indices.py
```

Este script debe ejecutarse cuando:

* Se instala el proyecto por primera vez.
* Se modifica un documento.
* Se cambia la estrategia de chunking.
* Se cambia el modelo de embeddings.

Comando utilizado:

```bash
python generar_indices.py
```

Se generaron tres índices independientes:

```text
vectorstores/
├── catalogo/
├── politicas/
└── crm/
```

Colecciones creadas:

```text
patito_catalogo
patito_politicas
patito_crm
```

Resultado obtenido:

```text
Catálogo: 3 fragmentos almacenados
Políticas: 4 fragmentos almacenados
CRM: 3 fragmentos almacenados
Total: 10 fragmentos
Tiempo total: 2.44 segundos
```

Los tres índices se generaron correctamente.

---

## Estado actual

Hasta este punto se encuentra completado:

```text
✓ Configuración del entorno
✓ Instalación de dependencias
✓ Protección de credenciales
✓ Conexión con Gemini
✓ Conexión con embeddings
✓ Carga de documentos
✓ Fragmentación
✓ Metadatos de trazabilidad
✓ Generación de tres índices Chroma independientes
```

Pendiente dentro del Bloque 2:

```text
2.3 Abrir los índices existentes
2.4 Probar la recuperación semántica
```

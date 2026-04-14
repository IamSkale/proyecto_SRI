# Proyecto Integrador de Sistemas de Recuperación de Información

## Corte 1: Adquisición, Indexación y Recuperación Básica

**Curso:** Sistemas de Recuperación de Información  
**Equipo:** Diego Hernandez Rodriguez C311, Fabian A. Almeida Martinez C311

---

## 1. Dominio Temático Seleccionado

El sistema se ha diseñado específicamente para el dominio de **música y canciones**, abarcando:

- **Canciones** con sus respectivos títulos, artistas, álbumes
- **Letras completas** de algunas canciones en múltiples idiomas
- **Géneros musicales** asociados a cada canción
- **Tags o etiquetas** que describen características de las canciones

## 2. Modelo de Recuperación de Información Implementado

### 2.1 Modelo Seleccionado: Híbrido (BM25 + Similitud Textual)

El sistema implementa un **modelo híbrido de recuperación** que combina:

- **BM25 (Best Matching 25)**: Algoritmo de ranking avanzado para búsqueda en texto
- **Similitud textual** con bonificaciones por coincidencias en título y artista
- **Índice invertido** para búsqueda eficiente de términos

### 2.2 Justificación de la Selección

El modelo híbrido fue seleccionado porque:

| Característica | Ventaja para el dominio musical |
|----------------|--------------------------------|
| BM25 | Maneja documentos de longitud variable (canciones cortas/largas) |
| Similitud textual | Permite encontrar canciones por título o artista aunque no sea exacto |
| Bonificaciones | Da mayor peso a coincidencias en título (más relevantes para el usuario) |
| Multilingüe | Soporta búsquedas en 5 idiomas diferentes |

### 2.3 Componentes del Modelo

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSULTA DEL USUARIO                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PROCESAMIENTO DE LA CONSULTA                    │
│  • Detección de idioma    • Normalización de texto          │
│  • Eliminación de stopwords • Stemming básico               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              BÚSQUEDA EN ÍNDICE INVERTIDO                    │
│         (Filtrado rápido de documentos candidatos)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CÁLCULO DE PUNTUACIÓN                        │
│  • BM25 sobre letra (peso 1.5)                               │
│  • Similitud en título (peso 5.0)                            │
│  • Similitud en artista (peso 3.0)                           │
│  • Coincidencia exacta de frase (peso 8.0)                   │
│  • Palabras en título (peso 2.0 por palabra)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              RANKING Y PRESENTACIÓN DE RESULTADOS            │
│           (Ordenados por puntuación de relevancia)           │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Fórmula de Puntuación

La puntuación final de relevancia se calcula como:

```
Puntuación = (BM25 × 1.5) + (Similitud_título × 5.0) + (Similitud_artista × 3.0) 
           + (Coincidencias_título × 2.0) + (Coincidencias_artista × 1.0)
           + (Frase_exacta_título ? 8.0 : Frase_exacta_artista ? 4.0 : 0)
           + (Primera_palabra_coincide ? 3.0 : 0)
```

**Umbral de relevancia:** Solo se muestran canciones con puntuación ≥ 20.

---

## 3. Fuentes Bibliográficas

Las siguientes fuentes fueron utilizadas para la implementación del modelo de recuperación:

### 3.1 BM25 (Robertson, 2009)

> Robertson, S., & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. Foundations and Trends in Information Retrieval, 3(4), 333-389.

**Aportación al proyecto:** Implementación de la fórmula BM25 para el ranking de documentos, incluyendo los parámetros k1=1.5 y b=0.75 optimizados para textos de longitud variable.

### 3.2 Índice Invertido (Manning et al., 2008)

> Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press.

**Aportación al proyecto:** Construcción del índice invertido y técnicas de procesamiento de texto (tokenización, stopwords, stemming).

### 3.3 Procesamiento Multilingüe (Steinberger, 2012)

> Steinberger, R. (2012). *A survey of methods to ease the development of highly multilingual text mining applications*. Language Resources and Evaluation, 46(2), 155-176.

**Aportación al proyecto:** Estrategias para detección de idioma y normalización de texto multilingüe.

### 3.4 Similitud de Cadenas (Ratcliff & Metzener, 1988)

> Ratcliff, J. W., & Metzener, D. E. (1988). *Pattern Matching: The Gestalt Approach*. Dr. Dobb's Journal.

**Aportación al proyecto:** Implementación del algoritmo SequenceMatcher para calcular similitud entre títulos y consultas.

---

## 4. Estadísticas del Corpus Recopilado

| Métrica | Valor |
|---------|-------|
| **Total de canciones únicas** | 109270 |
| **Canciones con información básica** (título/artista) | 109270 |
| **Canciones con género musical** | 109270 |
| **Canciones con tags** | 109270 |
| **Canciones con letra completa** | 10000 |

---

## 5. Arquitectura del Sistema

### 5.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                           main.py                                │
│                    (Punto de entrada del sistema)                │
└─────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  indexer.py   │       │  searcher.py  │       │   Database/   │
│               │       │               │       │               │
│ • Carga de    │◄─────►│ • Búsqueda    │       │ • CSVs        │
│   datos       │       │   avanzada    │       │ • Letras      │
│ • Índice      │       │ • Ranking     │       │   (.txt)      │
│   invertido   │       │ • Resultados  │       │               │
│ • TF-IDF      │       │               │       │               │
└───────────────┘       └───────────────┘       └───────────────┘
```

### 5.2 Flujo de Datos

1. **Indexación (una sola vez):**
   - Carga de archivos CSV y letras
   - Procesamiento y normalización de texto
   - Construcción de índice invertido
   - Cálculo de TF-IDF
   - Persistencia del índice en `indice_musica.pkl`

2. **Búsqueda (cada consulta):**
   - Procesamiento de la consulta del usuario
   - Filtrado de candidatos mediante índice invertido
   - Cálculo de puntuación de relevancia (BM25 + bonificaciones)
   - Ordenamiento y presentación de resultados

---

## 6. Módulos Implementados en este Corte

### 6.1 Módulo de Adquisición de Datos

**Ubicación:** `indexer.py` - `cargar_datos()`

**Funcionalidades:**
- Lectura de archivos CSV (`id_information.csv`, `id_genres.csv`, `id_tags.csv`)
- Carga de archivos de letras desde carpeta `lyrics/`
- Unificación de toda la información por ID de canción

**Formato de datos de entrada:**

| Archivo | Formato | Columnas |
|---------|---------|----------|
| id_information.csv | TSV | `id\tartista\tcancion\talbum` |
| id_genres.csv | TSV | `id\tgenero` |
| id_tags.csv | TSV | `id\ttag1,tag2,tag3` |
| lyrics/*.txt | Texto plano | Letra completa de la canción |

### 6.2 Módulo de Indexación

**Ubicación:** `indexer.py` - `IndexadorTFIDF`

**Funcionalidades:**
- Construcción de índice invertido (término → lista de documentos)
- Cálculo de frecuencia de documentos (DF)
- Cálculo de TF-IDF y normas de documentos
- Detección de idioma (español, inglés, francés, portugués, italiano)
- Normalización de texto y eliminación de stopwords
- Stemming básico por idioma

### 6.3 Módulo Recuperador

**Ubicación:** `searcher.py` - `buscar_canciones_avanzado()`

**Funcionalidades:**
- Procesamiento de consulta del usuario
- Detección de idioma de la consulta
- Cálculo de puntuación BM25
- Cálculo de similitud textual
- Bonificaciones por coincidencias específicas
- Filtrado por umbral de relevancia (score ≥ 20)

---

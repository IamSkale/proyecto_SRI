import csv
import re
import math
from pathlib import Path
from collections import defaultdict, Counter
import pickle

class ProcesadorTexto:    
    def __init__(self):
        # Stopwords por idioma
        self.stopwords = {
            'es': self._cargar_stopwords_espanol(),
            'en': self._cargar_stopwords_ingles(),
            'fr': self._cargar_stopwords_frances(),
            'pt': self._cargar_stopwords_portugues(),
            'it': self._cargar_stopwords_italiano()
        }
    
    def _cargar_stopwords_espanol(self):
        return {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'a', 'ante', 'bajo', 'cabe', 'con', 'contra', 'de', 'del',
            'desde', 'durante', 'en', 'entre', 'hacia', 'hasta', 'mediante',
            'para', 'por', 'segun', 'sin', 'sobre', 'tras', 'y', 'o', 'u',
            'pero', 'sino', 'aunque', 'no', 'si', 'ya', 'tambien', 'ademas',
            'asi', 'como', 'donde', 'cuando', 'mientras', 'despues', 'antes',
            'ahora', 'luego', 'que', 'quien', 'cual', 'cuyo', 'yo', 'tu',
            'el', 'ella', 'ello', 'nosotros', 'vosotros', 'ellos', 'ellas',
            'me', 'te', 'se', 'le', 'les', 'lo', 'la', 'los', 'las', 'mi',
            'tu', 'su', 'mis', 'tus', 'sus', 'ser', 'estar', 'tener', 'haber',
            'hacer', 'poder', 'decir', 'ir', 'ver', 'dar', 'saber', 'querer',
            'llegar', 'pasar', 'deber', 'poner', 'parecer', 'mas', 'menos',
            'muy', 'mucho', 'poco', 'algo', 'nada', 'todo', 'nadie', 'alguien',
            'cada', 'otro', 'mismo', 'gran', 'buen', 'mal', 'tal', 'tan',
            'como', 'cuanto', 'porque', 'pues', 'entonces'
        }
    
    def _cargar_stopwords_ingles(self):
        return {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
            'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him',
            'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some',
            'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look',
            'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after',
            'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even',
            'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }
    
    def _cargar_stopwords_frances(self):
        return {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'est',
            'sont', 'dans', 'pour', 'par', 'avec', 'sans', 'ou', 'mais',
            'donc', 'or', 'ni', 'car', 'que', 'qui', 'dont', 'quoi', 'ce',
            'ces', 'cet', 'cette', 'mon', 'ton', 'son', 'ma', 'ta', 'sa',
            'mes', 'tes', 'ses', 'notre', 'votre', 'leur', 'nos', 'vos',
            'leurs', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'me', 'te', 'se', 'nous', 'vous', 'se', 'avoir', 'etre', 'faire',
            'dire', 'pouvoir', 'aller', 'voir', 'vouloir', 'venir', 'falloir',
            'devoir', 'croire', 'savoir', 'tenir', 'vivre', 'entendre', 'parler'
        }
    
    def _cargar_stopwords_portugues(self):
        return {
            'a', 'o', 'as', 'os', 'um', 'uma', 'uns', 'umas', 'de', 'do',
            'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas', 'por',
            'para', 'com', 'sem', 'sobre', 'entre', 'depois', 'antes',
            'durante', 'embora', 'porque', 'portanto', 'e', 'ou', 'mas',
            'nem', 'contudo', 'entretanto', 'assim', 'eu', 'tu', 'ele',
            'ela', 'nos', 'vos', 'eles', 'elas', 'me', 'te', 'se', 'lhe',
            'nos', 'vos', 'lhes', 'meu', 'teu', 'seu', 'minha', 'tua',
            'sua', 'nossa', 'vossa', 'isso', 'aquilo', 'este', 'esta',
            'estes', 'estas', 'esse', 'essa', 'esses', 'essas', 'aquele',
            'aquela', 'aqueles', 'aquelas'
        }
    
    def _cargar_stopwords_italiano(self):
        return {
            'il', 'lo', 'la', 'l', 'i', 'gli', 'le', 'un', 'uno', 'una',
            'del', 'dello', 'della', 'dei', 'degli', 'delle', 'e', 'ed',
            'o', 'ma', 'pero', 'perche', 'che', 'chi', 'cui', 'dove',
            'quando', 'come', 'dove', 'quale', 'quanti', 'quante', 'questo',
            'quella', 'questi', 'quelle', 'quegli', 'quelle', 'quel', 'io',
            'tu', 'lui', 'lei', 'noi', 'voi', 'loro', 'mi', 'ti', 'si',
            'ci', 'vi', 'gli', 'le', 'ne', 'lo', 'la', 'li', 'me', 'te',
            'se', 'ce', 've', 'avere', 'essere', 'fare', 'andare', 'venire',
            'potere', 'volere', 'dovere', 'dire', 'sapere', 'stare', 'dare'
        }
    
    def detectar_idioma(self, texto):
        if not texto:
            return 'en'
        
        texto = texto.lower()
        
        # Palabras clave por idioma
        palabras_clave = {
            'es': ['el', 'la', 'los', 'las', 'y', 'o', 'pero', 'porque', 'con', 'sin', 'más', 'muy'],
            'en': ['the', 'and', 'of', 'to', 'in', 'for', 'on', 'with', 'by', 'at', 'this', 'that'],
            'fr': ['le', 'la', 'les', 'et', 'de', 'des', 'pour', 'dans', 'avec', 'sans', 'est', 'sont'],
            'pt': ['a', 'o', 'as', 'os', 'e', 'de', 'do', 'da', 'para', 'com', 'por', 'mais'],
            'it': ['il', 'la', 'le', 'e', 'di', 'del', 'della', 'per', 'con', 'senza', 'che', 'non']
        }
        
        puntaje_idioma = {lang: 0 for lang in palabras_clave}
        palabras_texto = set(texto.split()[:200])
        
        for lang, claves in palabras_clave.items():
            for clave in claves:
                if clave in palabras_texto:
                    puntaje_idioma[lang] += 1
        
        # Si hay empate o puntajes bajos, intentar con caracteres especiales
        max_puntaje = max(puntaje_idioma.values())
        if max_puntaje > 0:
            candidatos = [lang for lang, score in puntaje_idioma.items() if score == max_puntaje]
            return candidatos[0] if candidatos else 'en'
        
        return 'en'
    
    def limpiar_texto(self, texto, idioma=None):
        if not texto:
            return []
        
        if idioma is None:
            idioma = self.detectar_idioma(texto)
        
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Normalizar caracteres especiales
        texto = self._normalizar_caracteres(texto)
        
        # Eliminar caracteres no alfabéticos (excepto espacios)
        texto = re.sub(r'[^a-z\s]', ' ', texto)
        
        # Eliminar números
        texto = re.sub(r'\d+', '', texto)
        
        # Eliminar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        # Tokenizar
        tokens = texto.split()
        
        # Eliminar stopwords según idioma
        stopwords_idioma = self.stopwords.get(idioma, self.stopwords['en'])
        tokens = [token for token in tokens if token not in stopwords_idioma and len(token) > 1]
        
        # Aplicar stemming básico
        tokens = [self._stemming(token, idioma) for token in tokens]
        
        return tokens
    
    def _normalizar_caracteres(self, texto):
        normalizaciones = {
            'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n', 'ý': 'y'
        }
        
        for acento, sin_acento in normalizaciones.items():
            texto = texto.replace(acento, sin_acento)
        
        return texto
    
    def _stemming(self, palabra, idioma):
        if len(palabra) <= 4:
            return palabra
        
        if idioma == 'es':
            return self._stemming_espanol(palabra)
        elif idioma == 'en':
            return self._stemming_ingles(palabra)
        elif idioma == 'fr':
            return self._stemming_frances(palabra)
        elif idioma == 'pt':
            return self._stemming_portugues(palabra)
        elif idioma == 'it':
            return self._stemming_italiano(palabra)
        else:
            return palabra
    
    def _stemming_espanol(self, palabra):
        sufijos = [('ando', 'ar'), ('iendo', 'er'), ('ando', 'ar'), ('iendo', 'ir'),
                   ('ado', 'ar'), ('ido', 'er'), ('ido', 'ir'), ('aba', 'ar'),
                   ('ía', 'er'), ('ía', 'ir'), ('aron', 'ar'), ('ieron', 'er'),
                   ('es', ''), ('ó', ''), ('é', ''), ('s', ''), ('n', ''),
                   ('ción', 'r'), ('sión', 'r'), ('dad', ''), ('mente', '')]
        
        for sufijo, reemplazo in sufijos:
            if palabra.endswith(sufijo):
                raiz = palabra[:-len(sufijo)] + reemplazo
                if len(raiz) >= 3:
                    return raiz
        return palabra
    
    def _stemming_ingles(self, palabra):
        sufijos = [('ing', ''), ('ed', ''), ('ies', 'y'), ('ied', 'y'),
                   ('s', ''), ('es', ''), ('er', ''), ('est', ''),
                   ('tion', 't'), ('sion', 's'), ('ness', ''), ('ity', '')]
        
        for sufijo, reemplazo in sufijos:
            if palabra.endswith(sufijo):
                raiz = palabra[:-len(sufijo)] + reemplazo
                if len(raiz) >= 3:
                    return raiz
        return palabra
    
    def _stemming_frances(self, palabra):
        sufijos = [('ant', ''), ('ent', ''), ('er', ''), ('ir', ''),
                   ('re', ''), ('tion', 't'), ('sion', 's'), ('able', ''),
                   ('ible', ''), ('ment', ''), ('ette', ''), ('ique', '')]
        
        for sufijo, reemplazo in sufijos:
            if palabra.endswith(sufijo):
                raiz = palabra[:-len(sufijo)] + reemplazo
                if len(raiz) >= 3:
                    return raiz
        return palabra
    
    def _stemming_portugues(self, palabra):
        sufijos = [('ando', 'ar'), ('endo', 'er'), ('indo', 'ir'),
                   ('ado', 'ar'), ('ido', 'er'), ('ido', 'ir'),
                   ('ava', 'ar'), ('eva', 'er'), ('iva', 'ir'),
                   ('s', ''), ('mos', ''), ('cao', 'r'), ('vao', 'r')]
        
        for sufijo, reemplazo in sufijos:
            if palabra.endswith(sufijo):
                raiz = palabra[:-len(sufijo)] + reemplazo
                if len(raiz) >= 3:
                    return raiz
        return palabra
    
    def _stemming_italiano(self, palabra):
        sufijos = [('ando', 'ar'), ('endo', 'er'), ('indo', 'ir'),
                   ('ato', 'ar'), ('uto', 'er'), ('ito', 'ir'),
                   ('ava', 'ar'), ('eva', 'er'), ('iva', 'ir'),
                   ('i', ''), ('o', ''), ('e', ''), ('a', ''),
                   ('zione', 'r'), ('sione', 'r')]
        
        for sufijo, reemplazo in sufijos:
            if palabra.endswith(sufijo):
                raiz = palabra[:-len(sufijo)] + reemplazo
                if len(raiz) >= 3:
                    return raiz
        return palabra


class IndexadorTFIDF:    
    def __init__(self, data_folder, lyrics_folder):
        self.data_folder = Path(data_folder)
        self.lyrics_folder = Path(lyrics_folder)
        self.procesador = ProcesadorTexto()
        
        # Estructuras de datos
        self.documentos = {}
        self.indice_invertido = defaultdict(list)
        self.frecuencia_documentos = defaultdict(int)
        self.idf = {}
        self.vocabulario = set()
        self.idiomas_documentos = {}
        
        self.num_documentos = 0
    
    def cargar_datos(self):
        print("📁 Cargando datos...")
        
        canciones = {}
        generos = defaultdict(list)
        tags = defaultdict(list)
        letras = {}
        
        # Cargar id_information.csv
        archivo_info = self.data_folder / 'id_information.csv'
        if archivo_info.exists():
            with open(archivo_info, 'r', encoding='utf-8') as f:
                for linea in f:
                    partes = linea.strip().split('\t')
                    if len(partes) >= 4:
                        id_cancion = partes[0].strip()
                        artista = partes[1].strip()
                        titulo = partes[2].strip()
                        album = partes[3].strip() if len(partes) > 3 else ""
                        
                        canciones[id_cancion] = {
                            'titulo': titulo,
                            'artista': artista,
                            'album': album
                        }
            print(f"  ✅ Cargadas {len(canciones)} canciones")
        else:
            print(f"  ❌ No se encontró {archivo_info}")
        
        # Cargar id_genres.csv
        archivo_genres = self.data_folder / 'id_genres.csv'
        if archivo_genres.exists():
            with open(archivo_genres, 'r', encoding='utf-8') as f:
                for linea in f:
                    partes = linea.strip().split('\t')
                    if len(partes) >= 2:
                        id_cancion = partes[0].strip()
                        genero = partes[1].strip()
                        if id_cancion and genero:
                            generos[id_cancion].append(genero)
            print(f"  ✅ Cargados géneros para {len(generos)} canciones")
        else:
            print(f"  ❌ No se encontró {archivo_genres}")
        
        # Cargar id_tags.csv
        archivo_tags = self.data_folder / 'id_tags.csv'
        if archivo_tags.exists():
            with open(archivo_tags, 'r', encoding='utf-8') as f:
                for linea in f:
                    partes = linea.strip().split('\t')
                    if len(partes) >= 2:
                        id_cancion = partes[0].strip()
                        tags_str = partes[1].strip()
                        if tags_str:
                            lista_tags = [tag.strip() for tag in tags_str.split(',')]
                            tags[id_cancion].extend(lista_tags)
            print(f"  ✅ Cargados tags para {len(tags)} canciones")
        else:
            print(f"  ❌ No se encontró {archivo_tags}")
        
        # Cargar letras
        archivos_letras = list(self.lyrics_folder.glob('*.txt'))
        for archivo in archivos_letras:
            id_cancion = archivo.stem
            with open(archivo, 'r', encoding='utf-8') as f:
                letras[id_cancion] = f.read()
        print(f"  ✅ Cargadas {len(letras)} letras")
        
        # Unificar todo
        todos_ids = set(canciones.keys()) | set(generos.keys()) | set(tags.keys()) | set(letras.keys())
        
        for id_cancion in todos_ids:
            self.documentos[id_cancion] = {
                'id': id_cancion,
                'titulo': canciones.get(id_cancion, {}).get('titulo', ''),
                'artista': canciones.get(id_cancion, {}).get('artista', ''),
                'album': canciones.get(id_cancion, {}).get('album', ''),
                'generos': generos.get(id_cancion, []),
                'tags': tags.get(id_cancion, []),
                'letra': letras.get(id_cancion, '')
            }
        
        self.num_documentos = len(self.documentos)
        print(f"\n📊 Total documentos: {self.num_documentos}")
        
        return self.documentos
    
    def procesar_documentos(self):
        print("\n🔧 Procesando documentos (esto puede tomar un momento)...")
        
        tf_documentos = {}
        
        for doc_id, doc in self.documentos.items():
            # Crear texto completo
            texto_completo = f"{doc['titulo']} {doc['artista']} {doc['letra']}"
            if doc['generos']:
                texto_completo += " " + " ".join(doc['generos'])
            if doc['tags']:
                texto_completo += " " + " ".join(doc['tags'])
            
            # Detectar idioma del documento
            idioma = self.procesador.detectar_idioma(texto_completo)
            self.idiomas_documentos[doc_id] = idioma
            
            # Limpiar y tokenizar
            tokens = self.procesador.limpiar_texto(texto_completo, idioma)
            
            # Calcular TF
            tf = Counter(tokens)
            tf_documentos[doc_id] = tf
            
            # Actualizar índice invertido
            for termino, freq in tf.items():
                self.indice_invertido[termino].append((doc_id, freq))
                self.vocabulario.add(termino)
        
        # Calcular frecuencia de documentos (DF)
        for termino, posting_list in self.indice_invertido.items():
            self.frecuencia_documentos[termino] = len(posting_list)
        
        # Calcular IDF
        print("📊 Calculando IDF...")
        for termino in self.vocabulario:
            df = self.frecuencia_documentos[termino]
            self.idf[termino] = math.log(self.num_documentos / (df + 1))
        
        print(f"  ✅ Vocabulario: {len(self.vocabulario)} términos únicos")
        print(f"  ✅ Documentos procesados: {self.num_documentos}")
    
    def obtener_documento(self, doc_id):
        return self.documentos.get(doc_id)
    
    def obtener_info_completa(self):
        return self.documentos
    
    def guardar_indice(self, archivo_salida='indice_musica.pkl'):
        print(f"\n💾 Guardando índice en {archivo_salida}...")
        
        datos = {
            'documentos': self.documentos,
            'indice_invertido': dict(self.indice_invertido),
            'frecuencia_documentos': dict(self.frecuencia_documentos),
            'idf': self.idf,
            'vocabulario': list(self.vocabulario),
            'num_documentos': self.num_documentos,
            'idiomas_documentos': self.idiomas_documentos
        }
        
        with open(archivo_salida, 'wb') as f:
            pickle.dump(datos, f)
        
        print(f"  ✅ Índice guardado")
    
    def cargar_indice(self, archivo='indice_musica.pkl'):
        print(f"📂 Cargando índice desde {archivo}...")
        
        with open(archivo, 'rb') as f:
            datos = pickle.load(f)
        
        self.documentos = datos['documentos']
        self.indice_invertido = datos['indice_invertido']
        self.frecuencia_documentos = datos['frecuencia_documentos']
        self.idf = datos['idf']
        self.vocabulario = set(datos['vocabulario'])
        self.num_documentos = datos['num_documentos']
        self.idiomas_documentos = datos.get('idiomas_documentos', {})
        
        print(f"  ✅ Índice cargado: {self.num_documentos} documentos, {len(self.vocabulario)} términos")
    
    def ejecutar_indexacion(self, archivo_salida='indice_musica.pkl'):
        print("\n" + "="*60)
        print("🚀 INICIANDO INDEXACIÓN MULTILINGÜE")
        print("="*60)
        
        self.cargar_datos()
        self.procesar_documentos()
        self.guardar_indice(archivo_salida)
        
        print("\n✅ INDEXACIÓN COMPLETADA")
        print("="*60)
        
        return self

def cargar_todo(data_folder, lyrics_folder):
    indexador = IndexadorTFIDF(data_folder, lyrics_folder)
    indexador.cargar_datos()
    return indexador.obtener_info_completa()
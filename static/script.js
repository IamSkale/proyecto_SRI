async function buscarCanciones() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    
    if (!query) {
        mostrarMensaje('Por favor, ingresa un término de búsqueda', 'warning');
        return;
    }
    
    const usarGenius = document.getElementById('searchGeniusCheckbox').checked;
    const geniusToken = usarGenius ? document.getElementById('geniusTokenInput').value.trim() : '';

    // Limpiar resultados anteriores y mostrar loading
    const container = document.getElementById('resultsContainer');
    const answerContainer = document.getElementById('ragAnswerContainer');
    container.innerHTML = '';
    answerContainer.innerHTML = '';
    mostrarLoading(true);
    
    try {
        const response = await fetch('/buscar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query, usar_genius: usarGenius, genius_token: geniusToken })
        });
        
        if (!response.ok) {
            throw new Error('Error en la búsqueda');
        }
        
        const resultados = await response.json();
        mostrarResultados(resultados);
        
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('Error al buscar canciones. Intenta de nuevo.', 'error');
    } finally {
        mostrarLoading(false);
    }
}

async function buscarRAG() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();

    if (!query) {
        mostrarMensaje('Por favor, ingresa un término de búsqueda', 'warning');
        return;
    }

    // Limpiar resultados anteriores y mostrar loading
    const resultsContainer = document.getElementById('resultsContainer');
    const answerContainer = document.getElementById('ragAnswerContainer');
    resultsContainer.innerHTML = '';
    answerContainer.innerHTML = '';
    mostrarLoading(true);

    try {
        const response = await fetch('/rag', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Error en la búsqueda RAG');
        }

        mostrarResultadosRAG(data);
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('Error al realizar búsqueda RAG. Intenta de nuevo.', 'error');
    } finally {
        mostrarLoading(false);
    }
}

function mostrarResultadosRAG(data) {
    const answerContainer = document.getElementById('ragAnswerContainer');
    const resultsContainer = document.getElementById('resultsContainer');
    const answer = data.answer || '';
    const documentos = data.documents || [];

    answerContainer.innerHTML = `
        <div class="rag-answer-card">
            <h2>Respuesta RAG</h2>
            <p>${escapeHtml(answer).replace(/\n/g, '<br>')}</p>
        </div>
    `;

    if (!documentos.length) {
        resultsContainer.innerHTML = `<div class="no-results">No se recuperaron documentos relevantes.</div>`;
        return;
    }

    resultsContainer.innerHTML = `
        <div class="rag-documents-title">Documentos recuperados</div>
        ${documentos.map((doc, index) => `
            <div class="song-card rag-doc-card">
                <div class="song-header">
                    <div>
                        <h3 class="song-title">${escapeHtml(doc.titulo || 'Sin título')}</h3>
                        <p class="song-artist">${escapeHtml(doc.artista || 'Desconocido')}</p>
                    </div>
                    <span class="song-score">${doc.score ? doc.score.toFixed(3) : '0.00'}</span>
                </div>
                <div class="song-metadata">
                    ${doc.generos && doc.generos.length ? `<div class="song-detail"><strong>Géneros:</strong> ${escapeHtml(doc.generos.join(', '))}</div>` : ''}
                    <div class="song-detail"><strong>Contexto:</strong><div class="lyrics">${escapeHtml(doc.contexto || '').replace(/\n/g, '<br>')}</div></div>
                </div>
            </div>
        `).join('')}
    `;
}

function mostrarResultados(canciones) {
    const container = document.getElementById('resultsContainer');
    
    if (!canciones || canciones.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                🎵 No se encontraron canciones para tu búsqueda
            </div>
        `;
        return;
    }
    
    container.innerHTML = canciones.map((cancion, index) => `
        <div class="song-card">
            <div class="song-header" onclick="toggleSongDetails(${index})">
                <div>
                    <h3 class="song-title">${escapeHtml(cancion.titulo)}</h3>
                    <p class="song-artist">${escapeHtml(cancion.artista)}</p>
                </div>
                <span class="song-toggle">▼</span>
            </div>
            <div class="song-metadata">
                <div class="song-detail">
                    <strong>💿 Álbum:</strong> ${escapeHtml(cancion.album || 'N/A')}
                </div>
                ${cancion.generos && cancion.generos.length > 0 ? `
                <div class="song-detail">
                    <strong>🏷️ Géneros:</strong> ${escapeHtml(cancion.generos.join(', '))}
                </div>
                ` : ''}
                ${cancion.snippet ? `
                <div class="song-detail song-snippet">
                    <strong>📝 Vista previa:</strong>
                    <div class="lyrics">${formatLyrics(cancion.snippet)}</div>
                </div>
                ` : ''}
            </div>
            <div class="song-lyrics" id="lyrics-${index}">
                ${cancion.letra ? `
                <div class="song-detail">
                    <strong>📝 Letra completa:</strong>
                    <div class="lyrics">${formatLyrics(cancion.letra)}</div>
                </div>
                ` : `
                <div class="song-detail no-lyrics">
                    <em>No hay letra completa disponible.</em>
                </div>
                `}
            </div>
        </div>
    `).join('');
}

function formatLyrics(text) {
    return escapeHtml(text).replace(/\n/g, '<br>');
}

function toggleSongDetails(index) {
    const card = document.querySelectorAll('.song-card')[index];
    const lyrics = document.getElementById(`lyrics-${index}`);

    card.classList.toggle('expanded');
    if (lyrics) {
        lyrics.classList.toggle('visible');
    }
}

function mostrarLoading(mostrar) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (mostrar) {
        loadingIndicator.classList.remove('hidden');
    } else {
        loadingIndicator.classList.add('hidden');
    }
}

function toggleGeniusToken() {
    const container = document.getElementById('geniusTokenContainer');
    const checked = document.getElementById('searchGeniusCheckbox').checked;
    if (checked) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
}

function mostrarMensaje(mensaje, tipo) {
    // Puedes implementar notificaciones aquí
    console.log(`${tipo}: ${mensaje}`);
    alert(mensaje);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Permitir buscar con Enter
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        buscarCanciones();
    }
});
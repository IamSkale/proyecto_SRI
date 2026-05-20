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
    container.innerHTML = '';
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
        <div class="song-card" onclick="toggleSongDetails(${index})">
            <div class="song-header">
                <div>
                    <h3 class="song-title">${escapeHtml(cancion.titulo)}</h3>
                    <p class="song-artist">${escapeHtml(cancion.artista)}</p>
                </div>
                <span class="song-toggle">▼</span>
            </div>
            <div class="song-details" id="details-${index}">
                <div class="song-detail">
                    <strong>💿 Álbum:</strong> ${escapeHtml(cancion.album || 'N/A')}
                </div>
                ${cancion.generos && cancion.generos.length > 0 ? `
                <div class="song-detail">
                    <strong>🏷️ Géneros:</strong> ${escapeHtml(cancion.generos.join(', '))}
                </div>
                ` : ''}
                ${cancion.tags && cancion.tags.length > 0 ? `
                <div class="song-detail">
                    <strong>🔖 Tags:</strong> ${escapeHtml(cancion.tags.join(', '))}
                </div>
                ` : ''}
                ${cancion.snippet ? `
                <div class="song-detail">
                    <strong>📝 Letra:</strong>
                    <div class="lyrics">${formatLyrics(cancion.snippet)}</div>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function formatLyrics(text) {
    return escapeHtml(text).replace(/\n/g, '<br>');
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

function toggleSongDetails(index) {
    const card = document.querySelectorAll('.song-card')[index];
    const details = document.getElementById(`details-${index}`);
    
    card.classList.toggle('expanded');
}

// Permitir buscar con Enter
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        buscarCanciones();
    }
});
// Глобальное состояние приложения
const appState = {
    selected: {
        domrf: null,
        avito: null,
        domclick: null
    },
    data: {
        domrf: [],
        avito: [],
        domclick: []
    }
};

// Утилиты
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Загрузка несопоставленных записей
async function loadData() {
    const searchQuery = document.getElementById('searchInput').value;
    
    try {
        const response = await fetch(`/api/manual-matching/unmatched/?search=${encodeURIComponent(searchQuery)}`);
        const result = await response.json();
        
        if (result.success) {
            appState.data = result.data;
            
            // Обновляем статистику
            document.getElementById('statDomrf').textContent = result.totals.total_domrf;
            document.getElementById('statAvito').textContent = result.totals.total_avito;
            document.getElementById('statDomclick').textContent = result.totals.total_domclick;
            
            // Обновляем счетчики в заголовках
            document.getElementById('badgeDomrf').textContent = result.totals.domrf;
            document.getElementById('badgeAvito').textContent = result.totals.avito;
            document.getElementById('badgeDomclick').textContent = result.totals.domclick;
            
            // Рендерим списки
            renderList('domrf', result.data.domrf);
            renderList('avito', result.data.avito);
            renderList('domclick', result.data.domclick);
        } else {
            showToast('Ошибка загрузки данных: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error loading data:', error);
        showToast('Ошибка подключения к серверу', 'error');
    }
}

// Рендер списка записей
function renderList(source, items) {
    const container = document.getElementById(`${source}List`);
    
    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3>Нет данных</h3>
                <p>Все записи уже сопоставлены или нет результатов по запросу</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="record-card" data-id="${item._id}" data-source="${source}" onclick="selectRecord('${source}', '${item._id}')">
            <div class="record-name">${escapeHtml(item.name)}</div>
            <div class="record-details">
                ${item.address ? `<span>📍 ${escapeHtml(item.address)}</span>` : ''}
                ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" class="record-url" onclick="event.stopPropagation()">🔗 Открыть источник</a>` : ''}
            </div>
        </div>
    `).join('');
}

// Выбор записи
function selectRecord(source, id) {
    // Убираем предыдущее выделение
    const previousSelected = document.querySelector(`#${source}List .record-card.selected`);
    if (previousSelected) {
        previousSelected.classList.remove('selected');
    }
    
    // Если кликнули на уже выбранную запись - снимаем выделение
    if (appState.selected[source] === id) {
        appState.selected[source] = null;
        updateSelectedDisplay();
        return;
    }
    
    // Выбираем новую запись
    appState.selected[source] = id;
    const card = document.querySelector(`#${source}List .record-card[data-id="${id}"]`);
    if (card) {
        card.classList.add('selected');
    }
    
    updateSelectedDisplay();
}

// Обновление отображения выбранных записей
function updateSelectedDisplay() {
    // Обновляем информацию о выбранных записях
    ['domrf', 'avito', 'domclick'].forEach(source => {
        const selectedId = appState.selected[source];
        const displayElement = document.getElementById(`selected${source.charAt(0).toUpperCase() + source.slice(1)}`);
        
        if (selectedId) {
            const item = appState.data[source].find(i => i._id === selectedId);
            if (item) {
                displayElement.textContent = item.name;
                displayElement.style.color = 'var(--success-color)';
            }
        } else {
            displayElement.textContent = 'Не выбрано';
            displayElement.style.color = 'var(--text-secondary)';
        }
    });
    
    // Включаем/отключаем кнопку сохранения (минимум один источник: DomRF, Avito или DomClick)
    const saveBtn = document.getElementById('saveBtn');
    const canSave = appState.selected.domrf || appState.selected.avito || appState.selected.domclick;
    saveBtn.disabled = !canSave;
}

// Очистка выбора
function clearSelection() {
    appState.selected = {
        domrf: null,
        avito: null,
        domclick: null
    };
    
    document.querySelectorAll('.record-card.selected').forEach(card => {
        card.classList.remove('selected');
    });
    
    updateSelectedDisplay();
}

// Сохранение сопоставления
async function saveMatch() {
    if (!appState.selected.domrf && !appState.selected.avito && !appState.selected.domclick) {
        showToast('Необходимо выбрать хотя бы одну запись из DomRF, Avito или DomClick', 'error');
        return;
    }
    
    const saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<div class="spinner"></div> Сохранение...';
    
    try {
        const response = await fetch('/api/manual-matching/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                domrf_id: appState.selected.domrf,
                avito_id: appState.selected.avito,
                domclick_id: appState.selected.domclick,
                created_at: new Date().toISOString()
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Сопоставление успешно сохранено!', 'success');
            
            // Перезагружаем данные
            await loadData();
            await loadUnifiedRecords();
            
            // Очищаем выбор
            clearSelection();
            
            // Показываем модальное окно для рейтинга
            showRatingModal(result.unified_id);
        } else {
            showToast('Ошибка: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error saving match:', error);
        showToast('Ошибка сохранения данных', 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '✓ Объединить';
    }
}

// Загрузка объединенных записей
async function loadUnifiedRecords() {
    try {
        const response = await fetch('/api/manual-matching/unified/');
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('statUnified').textContent = result.pagination.total;
            renderUnifiedTable(result.data);
        } else {
            showToast('Ошибка загрузки объединенных записей: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error loading unified records:', error);
        showToast('Ошибка загрузки объединенных записей', 'error');
    }
}

// Рендер таблицы объединенных записей
function renderUnifiedTable(records) {
    const tbody = document.getElementById('unifiedTableBody');
    
    if (!records || records.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <p>Пока нет объединенных записей</p>
                    <p style="font-size: 12px; margin-top: 10px;">Выберите записи из источников и нажмите "Объединить"</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = records.map(record => `
        <tr>
            <td>${escapeHtml(record.domrf_name)}</td>
            <td>${escapeHtml(record.avito_name)}</td>
            <td>${escapeHtml(record.domclick_name)}</td>
            <td>
                <span class="source-badge ${record.source}">${record.source === 'manual' ? '👤 Ручное' : '🤖 Авто'}</span>
            </td>
        </tr>
    `).join('');
}

// Экранирование HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Дебаунс для поиска
let searchTimeout;
document.getElementById('searchInput')?.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadData();
    }, 500);
});

// ========== МОДАЛЬНОЕ ОКНО РЕЙТИНГА ==========

function showRatingModal(unifiedId) {
    const modal = document.createElement('div');
    modal.className = 'rating-modal';
    modal.innerHTML = `
        <div class="rating-modal-content">
            <div class="rating-modal-header">
                <h3>Оцените объект</h3>
                <button class="rating-modal-close" onclick="closeRatingModal()">&times;</button>
            </div>
            <div class="rating-modal-body">
                <p>Пожалуйста, оцените качество данного объекта по шкале от 1 до 5:</p>
                
                <div class="rating-stars">
                    <input type="radio" id="star5" name="rating" value="5">
                    <label for="star5" class="star">★</label>
                    
                    <input type="radio" id="star4" name="rating" value="4">
                    <label for="star4" class="star">★</label>
                    
                    <input type="radio" id="star3" name="rating" value="3">
                    <label for="star3" class="star">★</label>
                    
                    <input type="radio" id="star2" name="rating" value="2">
                    <label for="star2" class="star">★</label>
                    
                    <input type="radio" id="star1" name="rating" value="1">
                    <label for="star1" class="star">★</label>
                </div>
                
                <div class="rating-description" id="ratingDescription" style="display: none;">
                    <label for="description">Опишите причину низкой оценки (необязательно):</label>
                    <textarea id="description" placeholder="Например: плохое качество строительства, проблемы с документами..."></textarea>
                </div>
            </div>
            <div class="rating-modal-footer">
                <button class="btn btn-secondary" onclick="closeRatingModal()">Пропустить</button>
                <button class="btn btn-primary" onclick="saveRating('${unifiedId}')">Сохранить оценку</button>
            </div>
        </div>
    `;
    
    // Добавляем стили для модального окна
    const style = document.createElement('style');
    style.textContent = `
        .rating-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .rating-modal-content {
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .rating-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .rating-modal-header h3 {
            margin: 0;
            color: #333;
        }
        
        .rating-modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
        
        .rating-stars {
            display: flex;
            gap: 8px;
            margin: 20px 0;
            justify-content: center;
        }
        
        .rating-stars input[type="radio"] {
            display: none;
        }
        
        .rating-stars .star {
            font-size: 32px;
            color: #ddd;
            cursor: pointer;
            transition: color 0.2s;
        }
        
        .rating-stars input[type="radio"]:checked ~ .star,
        .rating-stars .star:hover {
            color: #ffd700;
        }
        
        .rating-stars input[type="radio"]:checked ~ .star {
            color: #ffd700;
        }
        
        .rating-description {
            margin-top: 20px;
        }
        
        .rating-description label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .rating-description textarea {
            width: 100%;
            min-height: 80px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            resize: vertical;
        }
        
        .rating-modal-footer {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 24px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #666;
        }
        
        .btn-primary {
            background: #007bff;
            color: white;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    // Обработчик изменения рейтинга
    const ratingInputs = modal.querySelectorAll('input[name="rating"]');
    const descriptionDiv = modal.querySelector('#ratingDescription');
    
    ratingInputs.forEach(input => {
        input.addEventListener('change', function() {
            const rating = parseInt(this.value);
            if (rating < 3) {
                descriptionDiv.style.display = 'block';
            } else {
                descriptionDiv.style.display = 'none';
            }
        });
    });
}

function closeRatingModal() {
    const modal = document.querySelector('.rating-modal');
    if (modal) {
        modal.remove();
    }
}

async function saveRating(unifiedId) {
    const rating = document.querySelector('input[name="rating"]:checked');
    const description = document.querySelector('#description');
    
    if (!rating) {
        showToast('Пожалуйста, выберите оценку', 'error');
        return;
    }
    
    const ratingValue = parseInt(rating.value);
    const descriptionValue = description ? description.value.trim() : '';
    
    // Если рейтинг меньше 3, но описание пустое - предупреждаем
        if (ratingValue <= 3 && !descriptionValue) {
            if (!confirm('Вы поставили низкую оценку. Рекомендуется указать причину. Продолжить без описания?')) {
                return;
            }
        }
    
    try {
        const response = await fetch(`/api/manual-matching/unified/${unifiedId}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                rating: ratingValue,
                rating_description: descriptionValue
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Оценка сохранена!', 'success');
            closeRatingModal();
        } else {
            showToast('Ошибка сохранения оценки: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error saving rating:', error);
        showToast('Ошибка сохранения оценки', 'error');
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


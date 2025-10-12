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
    
    // Включаем/отключаем кнопку сохранения
    const saveBtn = document.getElementById('saveBtn');
    const canSave = appState.selected.domrf && (appState.selected.avito || appState.selected.domclick);
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
    if (!appState.selected.domrf) {
        showToast('Необходимо выбрать запись из DomRF', 'error');
        return;
    }
    
    if (!appState.selected.avito && !appState.selected.domclick) {
        showToast('Необходимо выбрать хотя бы одну запись из Avito или DomClick', 'error');
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


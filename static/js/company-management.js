// Company Management JavaScript

// Глобальные переменные
let currentModal = null;

// Утилиты
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function closeModal() {
    if (currentModal) {
        currentModal.remove();
        currentModal = null;
    }
}

// Обработчики событий
document.addEventListener('DOMContentLoaded', function() {
    loadCompanyInfo();
    loadBranchOffices();
    loadEmployees();
    loadEmployeeReviews();
});

// ========== ИНФОРМАЦИЯ О КОМПАНИИ ==========
async function loadCompanyInfo() {
    try {
        console.log('Загрузка информации о компании...');
        const response = await fetch('/api/company-info/?admin=true');
        console.log('Ответ получен:', response.status);
        const data = await response.json();
        console.log('Данные:', data);
        const list = document.getElementById('company-info-list');
        
        if (data.success && data.items && data.items.length > 0) {
            list.innerHTML = data.items.map(item => `
                <div class="item-card">
                    <div class="item-content">
                        <h3>${item.company_name || 'Информация о компании'}</h3>
                        <p><strong>Основатель:</strong> ${item.founder_name || 'Не указан'}</p>
                        <p><strong>Должность:</strong> ${item.founder_position || 'Не указана'}</p>
                        <p><strong>Статус:</strong> 
                            <span class="status ${item.is_active ? 'active' : 'inactive'}">
                                ${item.is_active ? 'Активна' : 'Неактивна'}
                            </span>
                        </p>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-secondary" onclick="editCompanyInfo('${item._id}')">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-sm ${item.is_active ? 'btn-warning' : 'btn-success'}" 
                                onclick="toggleCompanyInfo('${item._id}', ${item.is_active})">
                            <i class="fas fa-${item.is_active ? 'eye-slash' : 'eye'}"></i> 
                            ${item.is_active ? 'Деактивировать' : 'Активировать'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteCompanyInfo('${item._id}', '${item.company_name}')">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-info-circle"></i>
                    <p>Информация о компании не найдена</p>
                    <button class="btn btn-primary" onclick="openCreateCompanyInfoModal()">
                        <i class="fas fa-plus"></i> Добавить информацию
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки информации о компании:', error);
        document.getElementById('company-info-list').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Ошибка загрузки данных: ${error.message}</p>
            </div>
        `;
    }
}

async function toggleCompanyInfo(id, currentStatus) {
    try {
        const response = await fetch(`/api/company-info/${id}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Статус обновлен', 'success');
            loadCompanyInfo();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка обновления статуса', 'error');
    }
}

async function deleteCompanyInfo(id, name) {
    if (!confirm(`Удалить информацию о компании "${name}"?`)) return;
    
    try {
        const response = await fetch(`/api/company-info/${id}/`, {method: 'DELETE'});
        const data = await response.json();
        
        if (data.success) {
            showToast('Информация о компании удалена', 'success');
            loadCompanyInfo();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления информации о компании', 'error');
    }
}

// ========== ОФИСЫ ПРОДАЖ ==========
async function loadBranchOffices() {
    try {
        const response = await fetch('/api/branch-offices/?admin=true');
        const data = await response.json();
        const list = document.getElementById('offices-list');
        
        if (data.success && data.items && data.items.length > 0) {
            list.innerHTML = data.items.map(item => `
                <div class="item-card">
                    <div class="item-content">
                        <h3>${item.name}</h3>
                        <p><strong>Адрес:</strong> ${item.address || 'Не указан'}</p>
                        <p><strong>Телефон:</strong> ${item.phone || 'Не указан'}</p>
                        <p><strong>Email:</strong> ${item.email || 'Не указан'}</p>
                        <p><strong>Город:</strong> ${item.city || 'Не указан'}</p>
                        <p><strong>Статус:</strong> 
                            <span class="status ${item.is_active ? 'active' : 'inactive'}">
                                ${item.is_active ? 'Активен' : 'Неактивен'}
                            </span>
                            ${item.is_head_office ? '<span class="badge badge-primary">Головной офис</span>' : ''}
                        </p>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-secondary" onclick="editBranchOffice('${item._id}')">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-sm ${item.is_active ? 'btn-warning' : 'btn-success'}" 
                                onclick="toggleBranchOffice('${item._id}', ${item.is_active})">
                            <i class="fas fa-${item.is_active ? 'eye-slash' : 'eye'}"></i> 
                            ${item.is_active ? 'Деактивировать' : 'Активировать'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteBranchOffice('${item._id}', '${item.name}')">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-store"></i>
                    <p>Офисы продаж не найдены</p>
                    <button class="btn btn-primary" onclick="openCreateBranchOfficeModal()">
                        <i class="fas fa-plus"></i> Добавить офис
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки офисов:', error);
        document.getElementById('offices-list').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Ошибка загрузки данных</p>
            </div>
        `;
    }
}

async function toggleBranchOffice(id, currentStatus) {
    try {
        const response = await fetch(`/api/branch-offices/${id}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Статус обновлен', 'success');
            loadBranchOffices();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка обновления статуса', 'error');
    }
}

async function deleteBranchOffice(id, name) {
    if (!confirm(`Удалить офис "${name}"?`)) return;
    
    try {
        const response = await fetch(`/api/branch-offices/${id}/`, {method: 'DELETE'});
        const data = await response.json();
        
        if (data.success) {
            showToast('Офис удален', 'success');
            loadBranchOffices();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления офиса', 'error');
    }
}

// ========== СОТРУДНИКИ ==========
async function loadEmployees() {
    try {
        const response = await fetch('/api/employees/?admin=true');
        const data = await response.json();
        const list = document.getElementById('employees-list');
        
        if (data.success && data.items && data.items.length > 0) {
            list.innerHTML = data.items.map(item => `
                <div class="item-card">
                    <div class="item-content">
                        <h3>${item.full_name}</h3>
                        <p><strong>Должность:</strong> ${item.position || 'Не указана'}</p>
                        <p><strong>Телефон:</strong> ${item.phone || 'Не указан'}</p>
                        <p><strong>Email:</strong> ${item.email || 'Не указан'}</p>
                        <p><strong>Опыт:</strong> ${item.experience_years || 0} лет</p>
                        <p><strong>Специализация:</strong> ${item.specialization || 'Не указана'}</p>
                        <p><strong>Статус:</strong> 
                            <span class="status ${item.is_active ? 'active' : 'inactive'}">
                                ${item.is_active ? 'Активен' : 'Неактивен'}
                            </span>
                        </p>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-secondary" onclick="editEmployee('${item._id}')">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-sm ${item.is_active ? 'btn-warning' : 'btn-success'}" 
                                onclick="toggleEmployee('${item._id}', ${item.is_active})">
                            <i class="fas fa-${item.is_active ? 'eye-slash' : 'eye'}"></i> 
                            ${item.is_active ? 'Деактивировать' : 'Активировать'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteEmployee('${item._id}', '${item.full_name}')">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <p>Сотрудники не найдены</p>
                    <button class="btn btn-primary" onclick="openCreateEmployeeModal()">
                        <i class="fas fa-plus"></i> Добавить сотрудника
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки сотрудников:', error);
        document.getElementById('employees-list').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Ошибка загрузки данных</p>
            </div>
        `;
    }
}

async function toggleEmployee(id, currentStatus) {
    try {
        const response = await fetch(`/api/employees/${id}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Статус обновлен', 'success');
            loadEmployees();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка обновления статуса', 'error');
    }
}

async function deleteEmployee(id, name) {
    if (!confirm(`Удалить сотрудника "${name}"?`)) return;
    
    try {
        const response = await fetch(`/api/employees/${id}/`, {method: 'DELETE'});
        const data = await response.json();
        
        if (data.success) {
            showToast('Сотрудник удален', 'success');
            loadEmployees();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления сотрудника', 'error');
    }
}

// ========== МОДАЛЬНЫЕ ОКНА ==========
function openCreateCompanyInfoModal() {
    const html = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Добавить информацию о компании</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="createCompanyInfoForm">
            <div class="form-group">
              <label class="form-label">Название компании</label>
              <input class="form-input" name="company_name" required>
            </div>
            <div class="form-group">
              <label class="form-label">Имя основателя</label>
              <input class="form-input" name="founder_name" required>
            </div>
            <div class="form-group">
              <label class="form-label">Должность основателя</label>
              <input class="form-input" name="founder_position" required>
            </div>
            <div class="form-group">
              <label class="form-label">Цитата</label>
              <textarea class="form-input" name="quote" rows="4" placeholder="Цитата от основателя компании..."></textarea>
            </div>
            <div class="form-group">
              <label class="form-label"><input type="checkbox" name="is_active" checked> Активна</label>
            </div>
            <div class="form-group">
              <label class="form-label">Главное изображение</label>
              <input class="form-input" name="main_image" type="file" accept="image/*">
            </div>
            <div class="form-group">
              <label class="form-label">Галерея изображений</label>
              <input class="form-input" name="images" type="file" accept="image/*" multiple>
            </div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitCreateCompanyInfo()">Создать</button>
        </div>
      </div>
    </div>`;
    currentModal = document.createElement('div');
    currentModal.innerHTML = html;
    document.body.appendChild(currentModal);
}

function openCreateBranchOfficeModal() {
    // Модалка создания офиса (совместима с текущими стилями)
    const html = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Создать офис</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="createOfficeForm">
            <div class="form-group">
              <label class="form-label">Название</label>
              <input class="form-input" name="name" required>
            </div>
            <div class="form-group">
              <label class="form-label">Slug</label>
              <input class="form-input" name="slug" placeholder="автоматически">
            </div>
            <div class="form-group">
              <label class="form-label">Город</label>
              <input class="form-input" name="city">
            </div>
            <div class="form-group">
              <label class="form-label">Адрес</label>
              <input class="form-input" name="address">
            </div>
            <div class="form-group">
              <label class="form-label">Телефон</label>
              <input class="form-input" name="phone">
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input class="form-input" name="email" type="email">
            </div>
            <div class="form-group">
              <label class="form-label">Режим работы</label>
              <input class="form-input" name="schedule" placeholder="Пн-Пт: 9-18, Сб: 10-16">
            </div>
            <div class="form-group">
              <label class="form-label">Широта (lat)</label>
              <input class="form-input" name="latitude" placeholder="55.123">
            </div>
            <div class="form-group">
              <label class="form-label">Долгота (lng)</label>
              <input class="form-input" name="longitude" placeholder="56.789">
            </div>
            <div class="form-group">
              <label class="form-label"><input type="checkbox" name="is_head_office"> Головной офис</label>
            </div>
            <div class="form-group">
              <label class="form-label">Главное изображение</label>
              <input class="form-input" name="main_image" type="file" accept="image/*">
            </div>
            <div class="form-group">
              <label class="form-label">Изображения</label>
              <input class="form-input" name="images" type="file" accept="image/*" multiple>
            </div>
            <div class="form-group">
              <label class="form-label">Видео (YouTube/Rutube ссылки, каждое с новой строки)</label>
              <textarea class="form-input" name="video_urls" rows="3" placeholder="https://www.youtube.com/watch?v=...&#10;https://rutube.ru/video/..."></textarea>
            </div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitCreateOffice()">Создать</button>
        </div>
      </div>
    </div>`;
    currentModal = document.createElement('div');
    currentModal.innerHTML = html;
    document.body.appendChild(currentModal);
}

function openCreateEmployeeModal() {
    const html = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Добавить сотрудника</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="createEmployeeForm">
            <div class="form-group">
              <label class="form-label">ФИО</label>
              <input class="form-input" name="full_name" required>
            </div>
            <div class="form-group">
              <label class="form-label">Должность</label>
              <input class="form-input" name="position" required>
            </div>
            <div class="form-group">
              <label class="form-label">Телефон</label>
              <input class="form-input" name="phone" placeholder="+7">
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input class="form-input" name="email" type="email">
            </div>
            <div class="form-group">
              <label class="form-label">Опыт работы (лет)</label>
              <input class="form-input" name="experience_years" type="number" min="0">
            </div>
            <div class="form-group">
              <label class="form-label">Специализация</label>
              <input class="form-input" name="specialization" placeholder="Например: жилая недвижимость">
            </div>
            <div class="form-group">
              <label class="form-label">Описание</label>
              <textarea class="form-input" name="bio" rows="4" placeholder="Краткая информация о сотруднике..."></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Достижения (через запятую)</label>
              <input class="form-input" name="achievements" placeholder="Лучший агент 2023, Продажа года">
            </div>
            <div class="form-group">
              <label class="form-label"><input type="checkbox" name="is_active" checked> Активен</label>
            </div>
            <div class="form-group">
              <label class="form-label">Фото сотрудника</label>
              <input class="form-input" name="images" type="file" accept="image/*" multiple>
            </div>
            <div class="form-group">
              <label class="form-label">Видео (YouTube/Rutube ссылки, каждое с новой строки)</label>
              <textarea class="form-input" name="video_urls" rows="3" placeholder="https://www.youtube.com/watch?v=...&#10;https://rutube.ru/video/..."></textarea>
            </div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitCreateEmployee()">Создать</button>
        </div>
      </div>
    </div>`;
    currentModal = document.createElement('div');
    currentModal.innerHTML = html;
    document.body.appendChild(currentModal);
}

function editCompanyInfo(id) {
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Редактировать информацию о компании</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="editCompanyInfoForm">
            <input type="hidden" name="_id" value="${id}">
            <div class="form-group"><label class="form-label">Название компании</label><input class="form-input" name="company_name"></div>
            <div class="form-group"><label class="form-label">Имя основателя</label><input class="form-input" name="founder_name"></div>
            <div class="form-group"><label class="form-label">Должность основателя</label><input class="form-input" name="founder_position"></div>
            <div class="form-group"><label class="form-label">Цитата</label><textarea class="form-input" name="quote" rows="4"></textarea></div>
            <div class="form-group"><label class="form-label"><input type="checkbox" name="is_active"> Активна</label></div>
            <div class="form-group"><label class="form-label">Главное изображение</label><input class="form-input" name="main_image" type="file" accept="image/*"></div>
            <div class="form-group"><label class="form-label">Галерея изображений</label><input class="form-input" name="images" type="file" accept="image/*" multiple></div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitEditCompanyInfo()">Сохранить</button>
        </div>
      </div>
    </div>`;
    currentModal = wrapper;
    document.body.appendChild(currentModal);
    
    // Загружаем данные компании
    fetch(`/api/company-info/${id}/get/`)
      .then(r => r.json())
      .then(data => {
        if (!data.success) { showToast(data.error || 'Ошибка загрузки', 'error'); return; }
        const item = data.item;
        const form = document.getElementById('editCompanyInfoForm');
        form.company_name.value = item.company_name || '';
        form.founder_name.value = item.founder_name || '';
        form.founder_position.value = item.founder_position || '';
        form.quote.value = item.quote || '';
        form.is_active.checked = !!item.is_active;
      })
      .catch(() => showToast('Ошибка сети', 'error'));
}

function editBranchOffice(id) {
    // Открываем модалку и подгружаем данные
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Редактировать офис</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="editOfficeForm">
            <input type="hidden" name="_id" value="${id}">
            <div class="form-group"><label class="form-label">Название</label><input class="form-input" name="name"></div>
            <div class="form-group"><label class="form-label">Slug</label><input class="form-input" name="slug"></div>
            <div class="form-group"><label class="form-label">Город</label><input class="form-input" name="city"></div>
            <div class="form-group"><label class="form-label">Адрес</label><input class="form-input" name="address"></div>
            <div class="form-group"><label class="form-label">Телефон</label><input class="form-input" name="phone"></div>
            <div class="form-group"><label class="form-label">Email</label><input class="form-input" name="email" type="email"></div>
            <div class="form-group"><label class="form-label">Режим работы</label><input class="form-input" name="schedule"></div>
            <div class="form-group"><label class="form-label">Широта (lat)</label><input class="form-input" name="latitude"></div>
            <div class="form-group"><label class="form-label">Долгота (lng)</label><input class="form-input" name="longitude"></div>
            <div class="form-group"><label class="form-label"><input type="checkbox" name="is_head_office"> Головной офис</label></div>
            <div class="form-group"><label class="form-label">Главное изображение</label><input class="form-input" name="main_image" type="file" accept="image/*"></div>
            <div class="form-group"><label class="form-label">Изображения</label><input class="form-input" name="images" type="file" accept="image/*" multiple></div>
            <div class="form-group"><label class="form-label">Видео (YouTube/Rutube ссылки, каждое с новой строки)</label><textarea class="form-input" name="video_urls" rows="3" placeholder="https://www.youtube.com/watch?v=...&#10;https://rutube.ru/video/..."></textarea></div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitEditOffice()">Сохранить</button>
        </div>
      </div>
    </div>`;
    currentModal = wrapper;
    document.body.appendChild(currentModal);
    // Загружаем данные офиса
    fetch(`/api/branch-offices/${id}/get/`)
      .then(r => r.json())
      .then(data => {
        if (!data.success) { showToast(data.error || 'Ошибка загрузки', 'error'); return; }
        const item = data.item;
        const form = document.getElementById('editOfficeForm');
        form.name.value = item.name || '';
        form.slug.value = item.slug || '';
        form.city.value = item.city || '';
        form.address.value = item.address || '';
        form.phone.value = item.phone || '';
        form.email.value = item.email || '';
        form.schedule.value = item.schedule || '';
        form.latitude.value = (item.latitude ?? '').toString();
        form.longitude.value = (item.longitude ?? '').toString();
        form.is_head_office.checked = !!item.is_head_office;
        form.video_urls.value = (item.videos || []).join('\n');
      })
      .catch(() => showToast('Ошибка сети', 'error'));
}

async function submitCreateOffice() {
    const form = document.getElementById('createOfficeForm');
    const formData = new FormData(form);
    try {
        const response = await fetch('/api/branch-offices/create/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast('Офис создан', 'success');
            closeModal();
            loadBranchOffices();
        } else {
            showToast(data.error || 'Ошибка создания', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

function editEmployee(id) {
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Редактировать сотрудника</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="editEmployeeForm">
            <input type="hidden" name="_id" value="${id}">
            <div class="form-group"><label class="form-label">ФИО</label><input class="form-input" name="full_name"></div>
            <div class="form-group"><label class="form-label">Должность</label><input class="form-input" name="position"></div>
            <div class="form-group"><label class="form-label">Телефон</label><input class="form-input" name="phone"></div>
            <div class="form-group"><label class="form-label">Email</label><input class="form-input" name="email" type="email"></div>
            <div class="form-group"><label class="form-label">Опыт работы (лет)</label><input class="form-input" name="experience_years" type="number"></div>
            <div class="form-group"><label class="form-label">Специализация</label><input class="form-input" name="specialization"></div>
            <div class="form-group"><label class="form-label">Описание</label><textarea class="form-input" name="bio" rows="4"></textarea></div>
            <div class="form-group"><label class="form-label">Достижения (через запятую)</label><input class="form-input" name="achievements"></div>
            <div class="form-group"><label class="form-label"><input type="checkbox" name="is_active"> Активен</label></div>
            <div class="form-group"><label class="form-label">Фото сотрудника</label><input class="form-input" name="images" type="file" accept="image/*" multiple></div>
            <div class="form-group"><label class="form-label">Видео (YouTube/Rutube ссылки, каждое с новой строки)</label><textarea class="form-input" name="video_urls" rows="3" placeholder="https://www.youtube.com/watch?v=...&#10;https://rutube.ru/video/..."></textarea></div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitEditEmployee()">Сохранить</button>
        </div>
      </div>
    </div>`;
    currentModal = wrapper;
    document.body.appendChild(currentModal);
    
    // Загружаем данные сотрудника
    fetch(`/api/employees/${id}/get/`)
      .then(r => r.json())
      .then(data => {
        if (!data.success) { showToast(data.error || 'Ошибка загрузки', 'error'); return; }
        const item = data.item;
        const form = document.getElementById('editEmployeeForm');
        form.full_name.value = item.full_name || '';
        form.position.value = item.position || '';
        form.phone.value = item.phone || '';
        form.email.value = item.email || '';
        form.experience_years.value = item.experience_years || 0;
        form.specialization.value = item.specialization || '';
        form.bio.value = item.bio || '';
        form.achievements.value = (item.achievements || []).join(', ');
        form.is_active.checked = !!item.is_active;
        form.video_urls.value = (item.videos || []).join('\n');
      })
      .catch(() => showToast('Ошибка сети', 'error'));
}

async function submitEditOffice() {
    const form = document.getElementById('editOfficeForm');
    const id = form.querySelector('input[name="_id"]').value;
    const formData = new FormData(form);
    try {
        const response = await fetch(`/api/branch-offices/${id}/update/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast('Изменения сохранены', 'success');
            closeModal();
            loadBranchOffices();
        } else {
            showToast(data.error || 'Ошибка сохранения', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function submitCreateCompanyInfo() {
    const form = document.getElementById('createCompanyInfoForm');
    const formData = new FormData(form);
    try {
        const response = await fetch('/api/company-info/create/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast('Информация о компании создана', 'success');
            closeModal();
            loadCompanyInfo();
        } else {
            showToast(data.error || 'Ошибка создания', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function submitEditCompanyInfo() {
    const form = document.getElementById('editCompanyInfoForm');
    const id = form.querySelector('input[name="_id"]').value;
    const formData = new FormData(form);
    try {
        const response = await fetch(`/api/company-info/${id}/update/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast('Изменения сохранены', 'success');
            closeModal();
            loadCompanyInfo();
        } else {
            showToast(data.error || 'Ошибка сохранения', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function submitCreateEmployee() {
    const form = document.getElementById('createEmployeeForm');
    const formData = new FormData(form);
    try {
        const response = await fetch('/api/employees/create/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast('Сотрудник создан', 'success');
            closeModal();
            loadEmployees();
        } else {
            showToast(data.error || 'Ошибка создания', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function submitEditEmployee() {
    const form = document.getElementById('editEmployeeForm');
    const id = form.querySelector('input[name="_id"]').value;
    const formData = new FormData(form);
    try {
        const response = await fetch(`/api/employees/${id}/update/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showToast('Изменения сохранены', 'success');
            closeModal();
            loadEmployees();
        } else {
            showToast(data.error || 'Ошибка сохранения', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

// ========== УТИЛИТЫ ==========
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

// Закрытие модального окна по клику вне его
document.addEventListener('click', function(event) {
    if (currentModal && event.target === currentModal) {
        closeModal();
    }
});

// Закрытие модального окна по Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && currentModal) {
        closeModal();
    }
});

// ========== ОТЗЫВЫ СОТРУДНИКОВ ==========
async function loadEmployeeReviews() {
    try {
        const response = await fetch('/api/employee-reviews/');
        const data = await response.json();
        const list = document.getElementById('reviews-list');
        
        if (data.success && data.reviews && data.reviews.length > 0) {
            list.innerHTML = data.reviews.map(review => `
                <div class="item-card">
                    <div class="item-content">
                        <h3>${review.name || 'Аноним'}</h3>
                        <p><strong>Сотрудник:</strong> ${review.employee_name} ${review.employee_position ? `(${review.employee_position})` : ''}</p>
                        <p><strong>Email:</strong> ${review.email || 'Не указан'}</p>
                        <p><strong>Телефон:</strong> ${review.phone || 'Не указан'}</p>
                        <p><strong>Рейтинг:</strong> ${'★'.repeat(review.rating)}${'☆'.repeat(5-review.rating)} (${review.rating}/5)</p>
                        <p><strong>Отзыв:</strong> ${review.text}</p>
                        <p><strong>Дата:</strong> ${new Date(review.created_at).toLocaleDateString('ru-RU')}</p>
                        <p><strong>Статус:</strong> 
                            <span class="status ${review.is_published ? 'active' : 'inactive'}">
                                ${review.is_published ? 'Опубликован' : 'На модерации'}
                            </span>
                        </p>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-secondary" onclick="editEmployeeReview('${review._id}')">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteEmployeeReview('${review._id}', '${review.name}')">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                        <button class="btn btn-sm ${review.is_published ? 'btn-warning' : 'btn-success'}" 
                                onclick="toggleEmployeeReview('${review._id}', ${review.is_published})">
                            <i class="fas fa-${review.is_published ? 'eye-slash' : 'eye'}"></i> 
                            ${review.is_published ? 'Скрыть' : 'Опубликовать'}
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>Отзывы не найдены</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки отзывов:', error);
        document.getElementById('reviews-list').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Ошибка загрузки данных</p>
            </div>
        `;
    }
}

async function toggleEmployeeReview(reviewId, currentStatus) {
    try {
        const response = await fetch(`/api/employee-reviews/${reviewId}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadEmployeeReviews();
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        showToast('Ошибка обновления статуса отзыва', 'error');
    }
}

async function editEmployeeReview(reviewId) {
    // Получаем данные отзыва
    try {
        const response = await fetch('/api/employee-reviews/');
        const data = await response.json();
        
        if (data.success && data.reviews) {
            const review = data.reviews.find(r => r._id === reviewId);
            if (review) {
                openEditReviewModal(review);
            } else {
                showToast('Отзыв не найден', 'error');
            }
        } else {
            showToast('Ошибка загрузки данных', 'error');
        }
    } catch (error) {
        showToast('Ошибка загрузки отзыва', 'error');
    }
}

function openEditReviewModal(review) {
    const html = `
    <div class="modal active">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Редактировать отзыв</h3>
          <button class="close-modal" onclick="closeModal()">×</button>
        </div>
        <div class="modal-body">
          <form id="editReviewForm">
            <input type="hidden" name="_id" value="${review._id}">
            <div class="form-group">
              <label class="form-label">Имя автора</label>
              <input class="form-input" name="name" value="${review.name || ''}" required>
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input class="form-input" name="email" type="email" value="${review.email || ''}">
            </div>
            <div class="form-group">
              <label class="form-label">Телефон</label>
              <input class="form-input" name="phone" value="${review.phone || ''}">
            </div>
            <div class="form-group">
              <label class="form-label">Рейтинг</label>
              <select class="form-input" name="rating" required>
                <option value="1" ${review.rating == 1 ? 'selected' : ''}>1 звезда</option>
                <option value="2" ${review.rating == 2 ? 'selected' : ''}>2 звезды</option>
                <option value="3" ${review.rating == 3 ? 'selected' : ''}>3 звезды</option>
                <option value="4" ${review.rating == 4 ? 'selected' : ''}>4 звезды</option>
                <option value="5" ${review.rating == 5 ? 'selected' : ''}>5 звезд</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Текст отзыва</label>
              <textarea class="form-input" name="text" rows="4" required>${review.text || ''}</textarea>
            </div>
            <div class="form-group">
              <label class="form-label">
                <input type="checkbox" name="is_published" ${review.is_published ? 'checked' : ''}> 
                Опубликован
              </label>
            </div>
          </form>
        </div>
        <div class="modal-footer" style="display:flex; gap:8px; justify-content:flex-end;">
          <button class="btn" onclick="closeModal()">Отмена</button>
          <button class="btn btn-primary" onclick="submitEditReview()">Сохранить</button>
        </div>
      </div>
    </div>`;
    
    currentModal = document.createElement('div');
    currentModal.innerHTML = html;
    document.body.appendChild(currentModal);
}

async function submitEditReview() {
    const form = document.getElementById('editReviewForm');
    const formData = new FormData(form);
    const reviewId = form.querySelector('input[name="_id"]').value;
    
    try {
        const response = await fetch(`/api/employee-reviews/${reviewId}/update/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Отзыв обновлен', 'success');
            closeModal();
            loadEmployeeReviews();
        } else {
            showToast(data.error || 'Ошибка обновления', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function deleteEmployeeReview(reviewId, reviewName) {
    if (!confirm(`Удалить отзыв от "${reviewName}"?`)) return;
    
    try {
        const response = await fetch(`/api/employee-reviews/${reviewId}/delete/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        const data = await response.json();
        
        if (data.success) {
            showToast('Отзыв удален', 'success');
            loadEmployeeReviews();
        } else {
            showToast(data.error || 'Ошибка удаления', 'error');
        }
    } catch (error) {
        showToast('Ошибка удаления отзыва', 'error');
    }
}

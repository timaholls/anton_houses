/**
 * Управление избранным через localStorage
 */

// Ключ для localStorage
const FAVORITES_STORAGE_KEY = 'century21_favorites';

/**
 * Получить все избранное из localStorage
 */
function getFavorites() {
    try {
        const stored = localStorage.getItem(FAVORITES_STORAGE_KEY);
        if (stored) {
            return JSON.parse(stored);
        }
    } catch (e) {
        console.error('Ошибка чтения избранного:', e);
    }
    return {
        complexes: [],
        apartments: [],
        updated_at: new Date().toISOString()
    };
}

/**
 * Сохранить избранное в localStorage
 */
function saveFavorites(favorites) {
    try {
        favorites.updated_at = new Date().toISOString();
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(favorites));
        updateFavoritesCount();
        return true;
    } catch (e) {
        console.error('Ошибка сохранения избранного:', e);
        return false;
    }
}

/**
 * Добавить ЖК в избранное
 */
function addComplexToFavorites(complexId) {
    if (!complexId) return false;
    
    const favorites = getFavorites();
    const idStr = String(complexId);
    
    if (!favorites.complexes.includes(idStr)) {
        favorites.complexes.push(idStr);
        return saveFavorites(favorites);
    }
    return false;
}

/**
 * Удалить ЖК из избранного
 */
function removeComplexFromFavorites(complexId) {
    if (!complexId) return false;
    
    const favorites = getFavorites();
    const idStr = String(complexId);
    
    const index = favorites.complexes.indexOf(idStr);
    if (index > -1) {
        favorites.complexes.splice(index, 1);
        return saveFavorites(favorites);
    }
    return false;
}

/**
 * Проверить, находится ли ЖК в избранном
 */
function isComplexInFavorites(complexId) {
    if (!complexId) return false;
    
    const favorites = getFavorites();
    const idStr = String(complexId);
    return favorites.complexes.includes(idStr);
}

/**
 * Добавить квартиру в избранное
 */
function addApartmentToFavorites(complexId, apartmentId) {
    console.log('🔍 [FAVORITES] addApartmentToFavorites вызвана:', { complexId, apartmentId, complexIdType: typeof complexId, apartmentIdType: typeof apartmentId });
    
    if (!complexId || !apartmentId) {
        console.warn('❌ [FAVORITES] addApartmentToFavorites: отсутствуют параметры', { complexId, apartmentId });
        return false;
    }
    
    const favorites = getFavorites();
    const idStr = `${complexId}_${apartmentId}`;
    console.log('📝 [FAVORITES] Формируем ID для сохранения:', idStr);
    console.log('📋 [FAVORITES] Текущие избранные квартиры:', favorites.apartments);
    
    if (!favorites.apartments.includes(idStr)) {
        favorites.apartments.push(idStr);
        const saved = saveFavorites(favorites);
        console.log('✅ [FAVORITES] Квартира добавлена в избранное:', { idStr, saved, totalApartments: favorites.apartments.length });
        return saved;
    } else {
        console.log('⚠️ [FAVORITES] Квартира уже в избранном:', idStr);
    }
    return false;
}

/**
 * Удалить квартиру из избранного
 */
function removeApartmentFromFavorites(complexId, apartmentId) {
    if (!complexId || !apartmentId) return false;
    
    const favorites = getFavorites();
    const idStr = `${complexId}_${apartmentId}`;
    
    const index = favorites.apartments.indexOf(idStr);
    if (index > -1) {
        favorites.apartments.splice(index, 1);
        return saveFavorites(favorites);
    }
    return false;
}

/**
 * Проверить, находится ли квартира в избранном
 */
function isApartmentInFavorites(complexId, apartmentId) {
    if (!complexId || !apartmentId) return false;
    
    const favorites = getFavorites();
    const idStr = `${complexId}_${apartmentId}`;
    return favorites.apartments.includes(idStr);
}

/**
 * Переключить состояние ЖК в избранном
 */
function toggleComplexFavorite(complexId) {
    if (isComplexInFavorites(complexId)) {
        removeComplexFromFavorites(complexId);
        return false;
    } else {
        addComplexToFavorites(complexId);
        return true;
    }
}

/**
 * Переключить состояние квартиры в избранном
 */
function toggleApartmentFavorite(complexId, apartmentId) {
    if (isApartmentInFavorites(complexId, apartmentId)) {
        removeApartmentFromFavorites(complexId, apartmentId);
        return false;
    } else {
        addApartmentToFavorites(complexId, apartmentId);
        return true;
    }
}

/**
 * Обновить счетчик избранного в шапке
 */
function updateFavoritesCount() {
    const favorites = getFavorites();
    const totalCount = favorites.complexes.length + favorites.apartments.length;
    
    const countElement = document.getElementById('favorites-count');
    if (countElement) {
        countElement.textContent = totalCount;
        if (totalCount > 0) {
            countElement.style.display = 'inline-block';
        } else {
            countElement.style.display = 'none';
        }
    }
    
    // Обновляем счетчик в мобильном меню
    const mobileCountElement = document.getElementById('favorites-count-mobile');
    if (mobileCountElement) {
        mobileCountElement.textContent = ` (${totalCount})`;
        if (totalCount > 0) {
            mobileCountElement.style.display = 'inline';
        } else {
            mobileCountElement.style.display = 'none';
        }
    }
    
    // Обновить плавающую кнопку избранного
    updateFavoritesFloatingButton();
}

/**
 * Обновить плавающую кнопку избранного
 */
function updateFavoritesFloatingButton() {
    const favorites = getFavorites();
    const totalCount = favorites.complexes.length + favorites.apartments.length;
    
    const buttonContainer = document.getElementById('favorites-button-container');
    const badgeElement = document.getElementById('favorites-badge-floating');
    
    if (buttonContainer) {
        if (totalCount > 0) {
            buttonContainer.style.display = 'block';
            if (badgeElement) {
                badgeElement.textContent = totalCount;
            }
        } else {
            buttonContainer.style.display = 'none';
        }
    }
}

/**
 * Обновить иконку избранного для элемента
 */
function updateFavoriteIcon(element, isFavorite) {
    if (!element) return;
    
    const icon = element.querySelector('i');
    if (icon) {
        if (isFavorite) {
            icon.classList.remove('far');
            icon.classList.add('fas');
            element.classList.add('favorite-active');
        } else {
            icon.classList.remove('fas');
            icon.classList.add('far');
            element.classList.remove('favorite-active');
        }
    }
}

/**
 * Инициализация избранного при загрузке страницы
 */
function initFavorites() {
    // Обновляем счетчик в шапке
    updateFavoritesCount();
    
    // Обновляем все кнопки избранного на странице
    document.querySelectorAll('[data-favorite-complex-id]').forEach(btn => {
        const complexId = btn.getAttribute('data-favorite-complex-id');
        const isFavorite = isComplexInFavorites(complexId);
        updateFavoriteIcon(btn, isFavorite);
    });
    
    document.querySelectorAll('[data-favorite-apartment-id]').forEach(btn => {
        const apartmentId = btn.getAttribute('data-favorite-apartment-id');
        const complexId = btn.getAttribute('data-favorite-complex-id');
        const isFavorite = isApartmentInFavorites(complexId, apartmentId);
        updateFavoriteIcon(btn, isFavorite);
    });
}

// Глобальная функция для обработки клика на кнопку избранного ЖК
window.toggleComplexFavoriteHandler = function(complexId, button) {
    const isFavorite = toggleComplexFavorite(complexId);
    updateFavoriteIcon(button, isFavorite);
    
    // Показываем уведомление
    if (typeof showFavoriteNotification === 'function') {
        if (isFavorite) {
            showFavoriteNotification('Добавлено в избранное');
        } else {
            showFavoriteNotification('Удалено из избранного');
        }
    }
};

// Глобальная функция для обработки клика на кнопку избранного квартиры
window.toggleApartmentFavoriteHandler = function(complexId, apartmentId, button) {
    const isFavorite = toggleApartmentFavorite(complexId, apartmentId);
    updateFavoriteIcon(button, isFavorite);
    
    // Показываем уведомление
    if (typeof showFavoriteNotification === 'function') {
        if (isFavorite) {
            showFavoriteNotification('Квартира добавлена в избранное');
        } else {
            showFavoriteNotification('Квартира удалена из избранного');
        }
    }
};

// Инициализация при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initFavorites();
        updateFavoritesFloatingButton();
    });
} else {
    initFavorites();
    updateFavoritesFloatingButton();
}


/**
 * Система отслеживания действий пользователя на сайте
 * Сохраняет историю действий в sessionStorage и передает при отправке формы
 */

(function() {
    'use strict';

    const STORAGE_KEY = 'user_activity_tracking';
    const MAX_ACTIONS = 50; // Максимальное количество действий для хранения

    /**
     * Инициализация системы отслеживания
     */
    function initTracking() {
        // Инициализируем хранилище, если его нет
        if (!sessionStorage.getItem(STORAGE_KEY)) {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
                actions: [],
                startTime: new Date().toISOString(),
                visitedPages: []
            }));
        }

        // Отслеживаем переходы между страницами
        trackPageView();
        
        // Отслеживаем клики по важным элементам
        trackImportantClicks();
    }

    /**
     * Отслеживание просмотра страницы
     */
    function trackPageView() {
        const currentPath = window.location.pathname;
        const pageTitle = document.title;
        
        // Определяем тип страницы
        let pageType = 'other';
        let pageData = {};
        
        if (currentPath.includes('/mortgage')) {
            pageType = 'mortgage';
        } else if (currentPath.includes('/catalog')) {
            pageType = 'catalog';
        } else if (currentPath.includes('/complexes') || currentPath.match(/\/detail\/\d+/)) {
            pageType = 'complex_detail';
            // Пытаемся получить ID ЖК из URL или данных на странице
            const match = currentPath.match(/\/detail\/(\d+)/);
            if (match) {
                pageData.complex_id = match[1];
            }
            // Пытаемся получить название ЖК
            const complexNameEl = document.querySelector('h1, .complex-name, .detail-title');
            if (complexNameEl) {
                pageData.complex_name = complexNameEl.textContent.trim();
            }
        } else if (currentPath.includes('/apartment/') || currentPath.match(/\/apartments\/\d+/)) {
            pageType = 'apartment_detail';
            const match = currentPath.match(/\/apartments?\/(\d+)/);
            if (match) {
                pageData.apartment_id = match[1];
            }
        } else if (currentPath.includes('/future-complexes')) {
            pageType = 'future_complexes';
        } else if (currentPath.match(/\/future-complexes\/\d+/)) {
            pageType = 'future_complex_detail';
            const match = currentPath.match(/\/future-complexes\/(\d+)/);
            if (match) {
                pageData.complex_id = match[1];
            }
        } else if (currentPath.includes('/offers')) {
            pageType = 'offers';
        } else if (currentPath.includes('/services')) {
            pageType = 'services';
        } else if (currentPath === '/' || currentPath === '') {
            pageType = 'home';
        }

        addAction({
            type: 'view_page',
            page_type: pageType,
            page_path: currentPath,
            page_title: pageTitle,
            data: pageData,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Отслеживание кликов по важным элементам
     */
    function trackImportantClicks() {
        // Отслеживаем клики по кнопкам бронирования
        document.addEventListener('click', function(e) {
            const target = e.target.closest('button, a');
            if (!target) return;

            // Кнопки бронирования
            if (target.classList.contains('book-apartment-btn') || 
                target.onclick && target.onclick.toString().includes('openBookingModal')) {
                const apartmentId = getApartmentIdFromPage();
                if (apartmentId) {
                    addAction({
                        type: 'click_booking',
                        apartment_id: apartmentId,
                        timestamp: new Date().toISOString()
                    });
                }
            }

            // Кнопки "Оставить заявку", "Подать заявку"
            if (target.classList.contains('anchor-feedback-btn') || 
                target.textContent.includes('заявк') || 
                target.textContent.includes('Заявк')) {
                addAction({
                    type: 'click_feedback_button',
                    button_text: target.textContent.trim(),
                    timestamp: new Date().toISOString()
                });
            }

            // Клики по карточкам ЖК
            if (target.closest('.future-complex-card, .complex-card, .home-property-card')) {
                const card = target.closest('.future-complex-card, .complex-card, .home-property-card');
                const complexName = card.querySelector('h2, h3, .complex-name, .card-title');
                if (complexName) {
                    addAction({
                        type: 'click_complex_card',
                        complex_name: complexName.textContent.trim(),
                        timestamp: new Date().toISOString()
                    });
                }
            }
        });
    }

    /**
     * Получить ID квартиры со страницы
     */
    function getApartmentIdFromPage() {
        // Пытаемся найти ID в различных местах
        const urlMatch = window.location.pathname.match(/\/apartments?\/(\d+)/);
        if (urlMatch) return urlMatch[1];
        
        const dataId = document.querySelector('[data-apartment-id]');
        if (dataId) return dataId.getAttribute('data-apartment-id');
        
        return null;
    }

    /**
     * Отслеживание просмотра ЖК
     */
    function trackComplexView(complexId, complexName) {
        addAction({
            type: 'view_complex',
            complex_id: complexId,
            complex_name: complexName,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Отслеживание просмотра квартиры
     */
    function trackApartmentView(apartmentId, apartmentData) {
        addAction({
            type: 'view_apartment',
            apartment_id: apartmentId,
            rooms: apartmentData.rooms,
            area: apartmentData.area,
            price: apartmentData.price,
            complex_name: apartmentData.complex_name,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Отслеживание выбора ипотечной программы
     */
    function trackMortgageProgram(programName, programRate) {
        addAction({
            type: 'view_mortgage_program',
            program_name: programName,
            program_rate: programRate,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Отслеживание фильтров в каталоге
     */
    function trackCatalogFilters(filters) {
        addAction({
            type: 'filter_catalog',
            filters: filters,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Добавить действие в историю
     */
    function addAction(action) {
        try {
            const storage = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{"actions":[]}');
            
            if (!storage.actions) {
                storage.actions = [];
            }

            // Добавляем действие
            storage.actions.push(action);

            // Ограничиваем количество действий
            if (storage.actions.length > MAX_ACTIONS) {
                storage.actions = storage.actions.slice(-MAX_ACTIONS);
            }

            // Обновляем список посещенных страниц
            if (action.type === 'view_page' && action.page_path) {
                if (!storage.visitedPages) {
                    storage.visitedPages = [];
                }
                const pageInfo = {
                    path: action.page_path,
                    type: action.page_type,
                    title: action.page_title,
                    timestamp: action.timestamp
                };
                // Добавляем только если такой страницы еще нет в списке
                const exists = storage.visitedPages.some(p => p.path === action.page_path);
                if (!exists) {
                    storage.visitedPages.push(pageInfo);
                }
            }

            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(storage));
        } catch (e) {
            console.error('Ошибка сохранения действия:', e);
        }
    }

    /**
     * Получить всю историю действий
     */
    function getActivityHistory() {
        try {
            return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{"actions":[]}');
        } catch (e) {
            return { actions: [], visitedPages: [] };
        }
    }

    /**
     * Сформировать текстовое описание активности пользователя
     */
    function generateActivitySummary() {
        const history = getActivityHistory();
        const actions = history.actions || [];
        const parts = [];

        // Собираем информацию о просмотренных страницах
        const pageTypes = new Set();
        const complexes = [];
        const apartments = [];
        const mortgagePrograms = [];
        const filters = [];

        actions.forEach(action => {
            switch (action.type) {
                case 'view_page':
                    if (action.page_type === 'mortgage') {
                        pageTypes.add('ипотеку');
                    } else if (action.page_type === 'catalog') {
                        pageTypes.add('каталог');
                    } else if (action.page_type === 'future_complexes') {
                        pageTypes.add('новостройки');
                    }
                    break;
                case 'view_complex':
                    if (action.complex_name && !complexes.includes(action.complex_name)) {
                        complexes.push(action.complex_name);
                    }
                    break;
                case 'view_apartment':
                    if (action.complex_name && !complexes.includes(action.complex_name)) {
                        complexes.push(action.complex_name);
                    }
                    if (action.rooms) {
                        const roomText = action.rooms === 1 ? 'однокомнатную' : 
                                        action.rooms === 2 ? 'двухкомнатную' : 
                                        action.rooms === 3 ? 'трехкомнатную' : 
                                        action.rooms === 4 ? 'четырехкомнатную' : 
                                        `${action.rooms}-комнатную`;
                        if (!apartments.includes(roomText)) {
                            apartments.push(roomText);
                        }
                    }
                    break;
                case 'view_mortgage_program':
                    if (action.program_name && !mortgagePrograms.includes(action.program_name)) {
                        mortgagePrograms.push(action.program_name);
                    }
                    break;
                case 'filter_catalog':
                    if (action.filters) {
                        if (action.filters.rooms && !filters.some(f => f.type === 'rooms')) {
                            const rooms = action.filters.rooms;
                            const roomText = rooms === 1 ? 'однокомнатные' : 
                                          rooms === 2 ? 'двухкомнатные' : 
                                          rooms === 3 ? 'трехкомнатные' : 
                                          rooms === 4 ? 'четырехкомнатные' : 
                                          `${rooms}-комнатные`;
                            filters.push({ type: 'rooms', text: roomText });
                        }
                    }
                    break;
            }
        });

        // Формируем текст
        if (pageTypes.size > 0) {
            const pagesList = Array.from(pageTypes).join(', ');
            parts.push(`Интересовался ${pagesList}`);
        }

        if (mortgagePrograms.length > 0) {
            parts.push(`смотрел ипотечную программу "${mortgagePrograms[0]}"`);
        }

        if (complexes.length > 0) {
            parts.push(`просматривал ЖК "${complexes[0]}"`);
        }

        if (apartments.length > 0) {
            parts.push(`смотрел ${apartments.join(', ')} квартиры`);
        } else if (filters.length > 0) {
            const roomsFilter = filters.find(f => f.type === 'rooms');
            if (roomsFilter) {
                parts.push(`смотрел ${roomsFilter.text} квартиры`);
            }
        }

        return parts.length > 0 ? parts.join(', ') : 'Просматривал сайт';
    }

    /**
     * Очистить историю (можно вызвать после успешной отправки формы)
     */
    function clearActivityHistory() {
        sessionStorage.removeItem(STORAGE_KEY);
    }

    // Экспортируем функции для использования в других скриптах
    window.UserTracking = {
        trackComplexView: trackComplexView,
        trackApartmentView: trackApartmentView,
        trackMortgageProgram: trackMortgageProgram,
        trackCatalogFilters: trackCatalogFilters,
        getActivityHistory: getActivityHistory,
        generateActivitySummary: generateActivitySummary,
        clearActivityHistory: clearActivityHistory
    };

    // Инициализация при загрузке страницы
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTracking);
    } else {
        initTracking();
    }

})();


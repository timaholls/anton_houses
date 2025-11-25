// Модальное окно подписки
(function() {
    'use strict';
    
    const STORAGE_KEY_LAST_SHOWN = 'subscription_modal_last_shown';
    const STORAGE_KEY_SUBSCRIBED = 'subscription_modal_subscribed';
    const STORAGE_KEY_DISMISSED = 'subscription_modal_dismissed';
    const INTERVAL_MS = 5 * 60 * 1000; // 5 минут
    
    const overlay = document.getElementById('subscription-modal-overlay');
    const modal = document.getElementById('subscription-modal');
    const closeBtn = document.getElementById('subscription-modal-close');
    const form = document.getElementById('subscription-modal-form');
    const submitBtn = document.getElementById('subscription-modal-button');
    const messageDiv = document.getElementById('subscription-modal-message');
    
    if (!overlay || !modal || !form) {
        return; // Элементы не найдены
    }
    
    // Проверка, нужно ли показывать модальное окно
    function shouldShowModal() {
        // Если пользователь уже подписался, не показываем
        if (localStorage.getItem(STORAGE_KEY_SUBSCRIBED) === 'true') {
            return false;
        }
        
        // Если пользователь закрыл модальное окно, проверяем интервал
        const lastShown = localStorage.getItem(STORAGE_KEY_LAST_SHOWN);
        if (lastShown) {
            const lastShownTime = parseInt(lastShown, 10);
            const now = Date.now();
            const timeSinceLastShown = now - lastShownTime;
            
            // Показываем, если прошло больше 5 минут
            return timeSinceLastShown >= INTERVAL_MS;
        }
        
        // Если никогда не показывали, показываем
        return true;
    }
    
    // Показать модальное окно
    function showModal() {
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        localStorage.setItem(STORAGE_KEY_LAST_SHOWN, Date.now().toString());
    }
    
    // Скрыть модальное окно
    function hideModal() {
        overlay.classList.remove('active');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        localStorage.setItem(STORAGE_KEY_DISMISSED, Date.now().toString());
    }
    
    // Закрытие по клику на overlay (фон)
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            hideModal();
        }
    });
    
    // Закрытие по кнопке закрытия
    if (closeBtn) {
        closeBtn.addEventListener('click', hideModal);
    }
    
    // Закрытие по Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
            hideModal();
        }
    });
    
    // Обработка отправки формы
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            name: formData.get('name').trim(),
            email: formData.get('email').trim().toLowerCase(),
            subscribe_to_projects: formData.get('subscribe_to_projects') === 'on',
            subscribe_to_promotions: formData.get('subscribe_to_promotions') === 'on'
        };
        
        // Валидация
        if (!data.email || !data.email.includes('@')) {
            showMessage('Пожалуйста, введите корректный email адрес', 'error');
            return;
        }
        
        if (!data.subscribe_to_projects && !data.subscribe_to_promotions) {
            showMessage('Пожалуйста, выберите хотя бы один тип уведомлений', 'error');
            return;
        }
        
        // Отправка данных
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span>Подписываем...</span><i class="fas fa-spinner fa-spin"></i>';
        
        try {
            const response = await fetch('/api/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showMessage(result.message || 'Подписка успешно оформлена!', 'success');
                form.reset();
                // Автоматически отмечаем чекбоксы
                document.getElementById('subscription-modal-projects').checked = true;
                document.getElementById('subscription-modal-promotions').checked = true;
                
                // Сохраняем, что пользователь подписался
                localStorage.setItem(STORAGE_KEY_SUBSCRIBED, 'true');
                
                // Закрываем модальное окно через 2 секунды
                setTimeout(() => {
                    hideModal();
                }, 2000);
            } else {
                showMessage(result.error || 'Произошла ошибка при подписке', 'error');
            }
        } catch (error) {
            console.error('Ошибка подписки:', error);
            showMessage('Произошла ошибка при отправке запроса', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
    
    // Показать сообщение
    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `subscription-modal-message ${type}`;
        messageDiv.style.display = 'block';
        
        // Скрываем сообщение через 5 секунд (кроме успешного)
        if (type !== 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    }
    
    // Получить CSRF токен из cookie
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
    
    // Инициализация: показать модальное окно при загрузке страницы
    function init() {
        // Небольшая задержка для лучшего UX
        setTimeout(() => {
            if (shouldShowModal()) {
                showModal();
            }
        }, 1000);
    }
    
    // Запуск при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Проверка каждые 5 минут (если модальное окно не показано)
    setInterval(() => {
        if (!overlay.classList.contains('active') && shouldShowModal()) {
            showModal();
        }
    }, INTERVAL_MS);
    
})();


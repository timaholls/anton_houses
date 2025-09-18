// Основной JavaScript файл
document.addEventListener('DOMContentLoaded', function() {
    
    // Обработка кнопки избранного
    const favoritesBtn = document.querySelector('.favorites-btn');
    if (favoritesBtn) {
        favoritesBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            const icon = this.querySelector('i');
            if (this.classList.contains('active')) {
                icon.classList.remove('far');
                icon.classList.add('fas');
                icon.style.color = '#e74c3c';
            } else {
                icon.classList.remove('fas');
                icon.classList.add('far');
                icon.style.color = '';
            }
        });
    }

    // Обработка кнопки входа
    const loginBtn = document.querySelector('.login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            // Здесь можно добавить логику для открытия модального окна входа
            console.log('Кнопка входа нажата');
        });
    }

    // Плавная прокрутка для навигационных ссылок (исключая кнопки выпадающего меню)
    const navLinks = document.querySelectorAll('.nav-link:not(.dropdown-toggle)');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href.startsWith('#') && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Анимация появления элементов при загрузке страницы
    const headerElements = document.querySelectorAll('.header-left, .main-nav, .header-right');
    headerElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(-20px)';
        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Обработка изменения размера окна
    window.addEventListener('resize', function() {
        // Здесь можно добавить логику для адаптивного поведения
        console.log('Размер окна изменен');
    });

    // Добавление активного состояния для текущей страницы
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Обработчик кнопки чата
    const chatButton = document.getElementById('chat-button');
    const chatModal = document.getElementById('chat-modal');
    const chatClose = document.getElementById('chat-close');
    
    if (chatButton && chatModal) {
        // Открытие/закрытие чата
        chatButton.addEventListener('click', function() {
            chatModal.classList.toggle('active');
        });
        
        // Закрытие чата по кнопке X
        if (chatClose) {
            chatClose.addEventListener('click', function() {
                chatModal.classList.remove('active');
            });
        }
        
        // Закрытие чата по клику вне окна
        document.addEventListener('click', function(e) {
            if (!chatModal.contains(e.target) && !chatButton.contains(e.target)) {
                chatModal.classList.remove('active');
            }
        });
        
        // Обработчики кнопок быстрых действий (пока заглушки)
        const quickActionBtns = document.querySelectorAll('.quick-action-btn');
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const action = this.getAttribute('data-action');
                console.log('Нажата кнопка:', action);
                // Здесь будет функционал для каждой кнопки
            });
        });
    }
}); 
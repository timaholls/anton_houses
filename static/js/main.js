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
        
        // Закрытие чата по клику вне окна (но не при клике внутри чата)
        document.addEventListener('click', function(e) {
            // Не закрываем, если клик был внутри модального окна чата
            if (chatModal.contains(e.target) || chatButton.contains(e.target)) {
                return;
            }
            // Не закрываем, если это клик по кнопкам или input внутри чата
            if (e.target.closest('.quick-action-btn') || 
                e.target.closest('.chat-input-inline') ||
                e.target.closest('.user-message-input')) {
                return;
            }
            chatModal.classList.remove('active');
        });
        
        // Обработчики кнопок быстрых действий теперь в chat-bot.js
    }

    // Mobile off-canvas menu
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const mobileDrawer = document.getElementById('mobile-drawer');
    const mobileClose = document.querySelector('.mobile-menu-close');
    const mobileBackdrop = document.getElementById('mobile-drawer-backdrop');
    const headerRow = document.querySelector('.header-row');

    function lockScroll(lock) {
        document.body.style.overflow = lock ? 'hidden' : '';
    }

    function setToggleState(expanded) {
        if (mobileToggle) {
            mobileToggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        }
    }

    function openMobile(){
        if (!mobileDrawer) return;
        mobileDrawer.classList.add('open');
        mobileDrawer.setAttribute('aria-hidden', 'false');
        lockScroll(true);
        setToggleState(true);
        if (mobileBackdrop) mobileBackdrop.classList.add('visible');
    }

    function closeMobile(){
        if (!mobileDrawer) return;
        mobileDrawer.classList.remove('open');
        mobileDrawer.setAttribute('aria-hidden', 'true');
        lockScroll(false);
        setToggleState(false);
        if (mobileBackdrop) mobileBackdrop.classList.remove('visible');
    }

    if (mobileToggle) mobileToggle.addEventListener('click', openMobile);
    if (mobileClose) mobileClose.addEventListener('click', closeMobile);
    if (mobileDrawer) mobileDrawer.addEventListener('click', function(e){
        if (e.target === mobileDrawer) closeMobile();
    });
    if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobile);

    function updateHeaderMode() {
        if (!headerRow) return;
        // На узких экранах всегда используем мобильное меню (CSS media query)
        if (window.innerWidth <= 1200) {
            document.body.classList.remove('force-mobile-nav');
            return;
        }
        // На широких экранах проверяем, помещается ли контент
        const mainNav = document.querySelector('.main-nav');
        if (!mainNav) {
            document.body.classList.remove('force-mobile-nav');
            return;
        }
        // Проверяем, не переносится ли навигация
        const navRect = mainNav.getBoundingClientRect();
        const headerRect = headerRow.getBoundingClientRect();
        const needsForce = navRect.width > headerRect.width * 0.6 || 
                          mainNav.scrollHeight > mainNav.clientHeight;
        document.body.classList.toggle('force-mobile-nav', needsForce);
    }

    updateHeaderMode();
    let headerResizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(headerResizeTimer);
        headerResizeTimer = setTimeout(updateHeaderMode, 120);
    });
}); 
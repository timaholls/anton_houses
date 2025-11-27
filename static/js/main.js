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
    const pageMain = document.querySelector('main');
    const pageFooter = document.querySelector('footer');

    function setPageInert(isInert) {
        [pageMain, pageFooter].forEach(el => {
            if (!el) return;
            if (isInert) {
                el.setAttribute('inert', '');
            } else {
                el.removeAttribute('inert');
            }
        });
    }

    function openMobile(){ 
        if (mobileDrawer){ 
            mobileDrawer.classList.add('open'); 
            mobileDrawer.setAttribute('aria-hidden', 'false');
            mobileDrawer.setAttribute('aria-modal', 'true');
            mobileDrawer.setAttribute('tabindex', '-1');
            document.body.style.overflow='hidden';
            setPageInert(true);
            requestAnimationFrame(() => mobileDrawer.focus());
        } 
        if (mobileToggle) {
            mobileToggle.setAttribute('aria-expanded', 'true');
        }
        if (mobileBackdrop) {
            mobileBackdrop.classList.add('open');
            mobileBackdrop.setAttribute('aria-hidden', 'false');
        }
    }
    function closeMobile(){ 
        if (mobileDrawer){ 
            mobileDrawer.classList.remove('open'); 
            mobileDrawer.setAttribute('aria-hidden', 'true');
            mobileDrawer.removeAttribute('aria-modal');
            document.body.style.overflow='';
            setPageInert(false);
            if (mobileDrawer.contains(document.activeElement) && mobileToggle) {
                mobileToggle.focus();
            }
        } 
        if (mobileToggle) {
            mobileToggle.setAttribute('aria-expanded', 'false');
        }
        if (mobileBackdrop) {
            mobileBackdrop.classList.remove('open');
            mobileBackdrop.setAttribute('aria-hidden', 'true');
        }
    }
    if (mobileToggle) mobileToggle.addEventListener('click', openMobile);
    if (mobileClose) mobileClose.addEventListener('click', closeMobile);
    if (mobileDrawer) mobileDrawer.addEventListener('click', function(e){ if (e.target === mobileDrawer) closeMobile(); });
    if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobile);

    // Проверка переполнения навигации на десктопе
    function checkNavOverflow() {
        const headerRow = document.querySelector('.header-row');
        const mainNav = document.querySelector('.main-nav');
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        const mainHeader = document.querySelector('.main-header');
        
        if (!headerRow || !mainNav || !mainHeader) return;
        
        // Проверяем только на десктопе (ширина > 768px)
        if (window.innerWidth > 768) {
            // Временно убираем класс переполнения и показываем навигацию для измерения
            const hadOverflow = headerRow.classList.contains('nav-overflow');
            headerRow.classList.remove('nav-overflow');
            mainHeader.classList.remove('nav-overflow-active');
            if (mobileToggle) mobileToggle.style.display = 'none';
            mainNav.style.display = 'flex';
            
            // Ждем один кадр для применения стилей
            requestAnimationFrame(() => {
                const headerRowWidth = headerRow.offsetWidth;
                const headerLeft = document.querySelector('.header-left');
                const headerRight = document.querySelector('.header-right');
                
                if (headerLeft && headerRight) {
                    const leftWidth = headerLeft.offsetWidth;
                    const rightWidth = headerRight.offsetWidth;
                    const navWidth = mainNav.scrollWidth;
                    const gaps = 32 * 3; // Примерные отступы между элементами
                    const availableWidth = headerRowWidth - leftWidth - rightWidth - gaps;
                    
                    // Если навигация не помещается, показываем бургер и скрываем меню
                    if (navWidth > availableWidth) {
                        headerRow.classList.add('nav-overflow');
                        mainHeader.classList.add('nav-overflow-active');
                        if (mobileToggle) mobileToggle.style.display = 'inline-flex';
                        mainNav.style.display = 'none';
                    } else {
                        // Навигация помещается, оставляем как есть
                        mainNav.style.display = '';
                    }
                }
            });
        } else {
            // На мобильных устройствах логика уже работает через CSS
            headerRow.classList.remove('nav-overflow');
            if (mainHeader) mainHeader.classList.remove('nav-overflow-active');
        }
    }
    
    // Проверяем при загрузке и изменении размера окна
    checkNavOverflow();
    window.addEventListener('resize', checkNavOverflow);
    
    // Также проверяем после полной загрузки страницы
    window.addEventListener('load', checkNavOverflow);
}); 
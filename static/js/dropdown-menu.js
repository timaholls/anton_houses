// JavaScript для выпадающего меню
document.addEventListener('DOMContentLoaded', function() {
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        // Добавляем обработчик клика для всех устройств
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Закрываем все другие выпадающие меню
            dropdowns.forEach(otherDropdown => {
                if (otherDropdown !== dropdown) {
                    otherDropdown.querySelector('.dropdown-menu').classList.remove('show');
                    otherDropdown.querySelector('.dropdown-toggle i').style.transform = 'rotate(0deg)';
                }
            });
            
            // Переключаем текущее меню
            menu.classList.toggle('show');
            const icon = toggle.querySelector('i');
            if (menu.classList.contains('show')) {
                icon.style.transform = 'rotate(180deg)';
            } else {
                icon.style.transform = 'rotate(0deg)';
            }
        });
        
        // Закрываем меню при клике вне его
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target)) {
                menu.classList.remove('show');
                const icon = toggle.querySelector('i');
                icon.style.transform = 'rotate(0deg)';
            }
        });
    });
    
    // Обработка изменения размера окна
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            // На десктопе убираем класс show
            dropdowns.forEach(dropdown => {
                const menu = dropdown.querySelector('.dropdown-menu');
                const icon = dropdown.querySelector('.dropdown-toggle i');
                menu.classList.remove('show');
                icon.style.transform = 'rotate(0deg)';
            });
        }
    });
    
    // Добавляем обработчик для предотвращения закрытия при клике на элементы меню
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('dropdown-item')) {
            // Не закрываем меню при клике на пункты меню
            e.stopPropagation();
        }
    });
});

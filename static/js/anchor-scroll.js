// Простой скрипт для прокрутки к форме обратной связи
document.addEventListener('DOMContentLoaded', function() {
    // Находим все кнопки с якорными ссылками к кнопке отправки
    const buttons = document.querySelectorAll('a[href="#feedback-submit-btn"]');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Ищем кнопку отправки формы по уникальному ID
            const submitButton = document.getElementById('feedback-submit-btn');
            
            if (submitButton) {
                // Получаем абсолютную позицию элемента относительно документа
                const rect = submitButton.getBoundingClientRect();
                const elementTop = rect.top + window.pageYOffset;
                
                // Добавляем отступ для фиксированного заголовка (примерно 80px)
                const headerOffset = 80;
                
                // Прокручиваем с учетом заголовка
                window.scrollTo({
                    top: elementTop - headerOffset,
                    behavior: 'smooth'
                });
            } else {
                // Попробуем найти форму по ID
                const form = document.getElementById('feedback-form');
                if (form) {
                    const rect = form.getBoundingClientRect();
                    const formTop = rect.top + window.pageYOffset;
                    window.scrollTo({
                        top: formTop - 80,
                        behavior: 'smooth'
                    });
                } else {
                    // Попробуем найти любую форму обратной связи
                    const feedbackSection = document.querySelector('.feedback-section, .feedback-wrapper, form');
                    if (feedbackSection) {
                        const rect = feedbackSection.getBoundingClientRect();
                        const sectionTop = rect.top + window.pageYOffset;
                        window.scrollTo({
                            top: sectionTop - 80,
                            behavior: 'smooth'
                        });
                    }
                }
            }
        });
    });
});

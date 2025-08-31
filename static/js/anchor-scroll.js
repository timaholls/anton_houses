// Простой скрипт для прокрутки к форме обратной связи
document.addEventListener('DOMContentLoaded', function() {
    // Находим все кнопки с якорными ссылками к кнопке отправки
    const buttons = document.querySelectorAll('a[href="#feedback-submit-btn"]');
    
    console.log('Найдено кнопок:', buttons.length);
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Кнопка нажата!');
            
            // Ищем кнопку отправки формы по уникальному ID
            const submitButton = document.getElementById('feedback-submit-btn');
            console.log('Кнопка отправки найдена:', submitButton);
            
            if (submitButton) {
                // Получаем абсолютную позицию элемента относительно документа
                const rect = submitButton.getBoundingClientRect();
                const elementTop = rect.top + window.pageYOffset;
                console.log('Позиция элемента:', elementTop);
                console.log('Текущая прокрутка:', window.pageYOffset);
                
                // Добавляем отступ для фиксированного заголовка (примерно 80px)
                const headerOffset = 80;
                
                // Прокручиваем с учетом заголовка
                window.scrollTo({
                    top: elementTop - headerOffset,
                    behavior: 'smooth'
                });
                console.log('Прокрутка выполнена к позиции:', elementTop - headerOffset);
            } else {
                console.log('Кнопка отправки не найдена, ищем альтернативы...');
                
                // Попробуем найти форму по ID
                const form = document.getElementById('feedback-form');
                if (form) {
                    console.log('Форма найдена по ID');
                    const rect = form.getBoundingClientRect();
                    const formTop = rect.top + window.pageYOffset;
                    window.scrollTo({
                        top: formTop - 80,
                        behavior: 'smooth'
                    });
                } else {
                    console.log('Форма по ID не найдена, ищем по классу');
                    
                    // Попробуем найти любую форму обратной связи
                    const feedbackSection = document.querySelector('.feedback-section, .feedback-wrapper, form');
                    if (feedbackSection) {
                        console.log('Секция обратной связи найдена');
                        const rect = feedbackSection.getBoundingClientRect();
                        const sectionTop = rect.top + window.pageYOffset;
                        window.scrollTo({
                            top: sectionTop - 80,
                            behavior: 'smooth'
                        });
                    } else {
                        console.log('Ничего не найдено!');
                    }
                }
            }
        });
    });
});

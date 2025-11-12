// Скрипт для прокрутки к форме обратной связи с показом скрытых элементов
document.addEventListener('DOMContentLoaded', function() {
    
    // Функция для показа формы обратной связи
    function showFeedbackForm() {
        const formElements = document.querySelectorAll('.feedback-header, .feedback-form');
        formElements.forEach(el => {
            if (el) {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }
        });
    }
    
    // Функция прокрутки к форме
    function scrollToFeedback(target, offset = 100) {
        if (target) {
            // Сначала показываем форму
            showFeedbackForm();
            
            // Затем прокручиваем
            const rect = target.getBoundingClientRect();
            const elementTop = rect.top + window.pageYOffset;
            
            window.scrollTo({
                top: elementTop - offset,
                behavior: 'smooth'
            });
            
            // Дополнительная проверка после прокрутки
            setTimeout(() => {
                showFeedbackForm();
            }, 600);
        }
    }
    
    // Обработчик для всех якорных ссылок к форме обратной связи
    const feedbackAnchors = document.querySelectorAll('a[href="#feedback-title"], a[href="#feedback-form"], a[href="#feedback-submit-btn"], .anchor-feedback-btn');
    
    feedbackAnchors.forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Пробуем найти целевой элемент
            const feedbackTitle = document.getElementById('feedback-title');
            const feedbackForm = document.getElementById('feedback-form');
            const submitButton = document.getElementById('feedback-submit-btn');
            
            const target = feedbackTitle || feedbackForm || submitButton;
            
            if (target) {
                scrollToFeedback(target, 100);
            } else {
                // Fallback: ищем секцию формы
                const feedbackSection = document.querySelector('.feedback-section, .feedback-wrapper');
                if (feedbackSection) {
                    scrollToFeedback(feedbackSection, 100);
                }
            }
        });
    });
    
    // Обработчик для прямых переходов по якорю при загрузке страницы
    if (window.location.hash) {
        const hash = window.location.hash;
        if (hash === '#feedback-title' || hash === '#feedback-form' || hash === '#feedback-submit-btn') {
            setTimeout(() => {
                showFeedbackForm();
                const target = document.querySelector(hash);
                if (target) {
                    scrollToFeedback(target, 100);
                }
            }, 300);
        }
    }
});

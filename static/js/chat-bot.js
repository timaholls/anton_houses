/**
 * Чат-бот для сайта недвижимости
 * Обрабатывает заявки: продать, купить, задать вопрос, позвонить
 */

class ChatBot {
    constructor() {
        this.chatBody = document.querySelector('.chat-body');
        this.currentState = null;
        this.formData = {};
        this.phoneNumber = '';
        
        this.init();
    }
    
    init() {
        // Обработчики кнопок быстрых действий
        const quickActionBtns = document.querySelectorAll('.quick-action-btn');
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.getAttribute('data-action');
                if (action === 'call') {
                    // Для звонка ничего не делаем, уже есть href
                    return;
                }
                e.preventDefault();
                this.handleAction(action);
            });
        });
    }
    
    handleAction(action) {
        this.resetForm();
        
        switch(action) {
            case 'sell':
                this.startSellFlow();
                break;
            case 'buy':
                this.startBuyFlow();
                break;
            case 'question':
                this.startQuestionFlow();
                break;
        }
    }
    
    resetForm() {
        this.formData = {};
        this.currentState = null;
        this.phoneNumber = '';
    }
    
    // ========== Продать ==========
    startSellFlow() {
        this.currentState = 'sell_type';
        this.formData.type = 'sell';
        this.showBotMessage('Что вы хотите продать?', [
            { text: 'Квартиру', value: 'apartment' },
            { text: 'Дом', value: 'house' }
        ]);
    }
    
    handleSellType(type) {
        this.formData.propertyType = type;
        
        if (type === 'apartment') {
            this.currentState = 'sell_rooms';
            this.showBotMessage('Сколько комнат в квартире?', [
                { text: 'Студия', value: 'studio' },
                { text: '1 комната', value: '1' },
                { text: '2 комнаты', value: '2' },
                { text: '3 комнаты', value: '3' },
                { text: '4+ комнаты', value: '4+' }
            ]);
        } else {
            // Для дома сразу запрашиваем номер
            this.currentState = 'sell_phone';
            this.showBotMessage('Укажите ваш номер телефона для связи:');
        }
    }
    
    handleSellRooms(rooms) {
        this.formData.rooms = rooms;
        this.currentState = 'sell_phone';
        this.showBotMessage('Укажите ваш номер телефона для связи:');
    }
    
    // ========== Купить ==========
    startBuyFlow() {
        this.currentState = 'buy_type';
        this.formData.type = 'buy';
        this.showBotMessage('Что вы хотите купить?', [
            { text: 'Квартиру', value: 'apartment' },
            { text: 'Дом', value: 'house' }
        ]);
    }
    
    handleBuyType(type) {
        this.formData.propertyType = type;
        
        if (type === 'apartment') {
            this.currentState = 'buy_rooms';
            this.showBotMessage('Сколько комнат вас интересует?', [
                { text: 'Студия', value: 'studio' },
                { text: '1 комната', value: '1' },
                { text: '2 комнаты', value: '2' },
                { text: '3 комнаты', value: '3' },
                { text: '4+ комнаты', value: '4+' }
            ]);
        } else {
            this.currentState = 'buy_phone';
            this.showBotMessage('Укажите ваш номер телефона для связи:');
        }
    }
    
    handleBuyRooms(rooms) {
        this.formData.rooms = rooms;
        this.currentState = 'buy_phone';
        this.showBotMessage('Укажите ваш номер телефона для связи:');
    }
    
    // ========== Задать вопрос ==========
    startQuestionFlow() {
        this.currentState = 'question_text';
        this.formData.type = 'question';
        this.showBotMessage('Напишите ваш вопрос:');
    }
    
    handleQuestionText(question) {
        this.formData.question = question;
        this.currentState = 'question_phone';
        this.showBotMessage('Укажите ваш номер телефона для связи:');
    }
    
    // ========== Отображение сообщений ==========
    renderButtons(buttons) {
        return `
            <div class="quick-actions">
                ${buttons.map(btn => `
                    <button class="quick-action-btn bot-button" data-value="${btn.value}">
                        ${btn.text}
                    </button>
                `).join('')}
            </div>
        `;
    }
    
    handleButtonClick(value) {
        switch(this.currentState) {
            case 'sell_type':
                this.handleSellType(value);
                break;
            case 'sell_rooms':
                this.handleSellRooms(value);
                break;
            case 'buy_type':
                this.handleBuyType(value);
                break;
            case 'buy_rooms':
                this.handleBuyRooms(value);
                break;
        }
    }
    
    // ========== Поля ввода ==========
    showPhoneInput() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message-input';
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="chat-input-inline">
                    <input type="tel" class="chat-inline-input" placeholder="+7 (999) 999-99-99" id="phone-input">
                    <button class="chat-send-inline-btn" id="send-btn">
                        <i class="fas fa-paper-plane"></i>
                        Отправить заявку
                    </button>
                </div>
            </div>
        `;
        
        this.chatBody.appendChild(messageDiv);
        this.scrollToBottom();
        
        const phoneInput = document.getElementById('phone-input');
        const sendBtn = document.getElementById('send-btn');
        
        // Маска телефона
        phoneInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.startsWith('8')) {
                value = '7' + value.substring(1);
            }
            if (value.startsWith('7')) {
                value = '+' + value;
            }
            if (value.length > 1) {
                value = value.substring(0, 12);
            }
            e.target.value = this.formatPhone(value);
        });
        
        phoneInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendBtn.click();
            }
        });
        
        sendBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const phone = phoneInput.value.replace(/\D/g, '');
            if (phone.length >= 11) {
                this.phoneNumber = phone.startsWith('7') ? '+' + phone : '+7' + phone.substring(1);
                this.formData.phone = this.phoneNumber;
                
                // Немедленно удаляем форму перед отправкой
                const inputMessage = messageDiv;
                if (inputMessage) {
                    inputMessage.remove();
                }
                
                this.handleSubmit();
            } else {
                this.showBotMessage('Пожалуйста, введите корректный номер телефона');
            }
        });
        
        phoneInput.focus();
    }
    
    showQuestionInput() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message-input';
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="chat-input-inline">
                    <textarea class="chat-inline-textarea" placeholder="Ваш вопрос..." id="question-input" rows="3"></textarea>
                    <button class="chat-send-inline-btn" id="send-question-btn">
                        <i class="fas fa-paper-plane"></i>
                        Далее
                    </button>
                </div>
            </div>
        `;
        
        this.chatBody.appendChild(messageDiv);
        this.scrollToBottom();
        
        const questionInput = document.getElementById('question-input');
        const sendBtn = document.getElementById('send-question-btn');
        
        sendBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const question = questionInput.value.trim();
            if (question.length > 0) {
                this.handleQuestionText(question);
                messageDiv.remove();
            } else {
                this.showBotMessage('Пожалуйста, введите ваш вопрос');
            }
        });
        
        questionInput.focus();
    }
    
    // Перехватываем изменение состояния для показа полей ввода
    showBotMessage(text, buttons = null) {
        // Удаляем все старые input поля перед показом нового сообщения
        const oldInputs = this.chatBody.querySelectorAll('.user-message-input');
        oldInputs.forEach(input => input.remove());
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message support-message';
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <img src="/media/logo/icon_site.png" alt="Поддержка C21">
            </div>
            <div class="message-content">
                <div class="message-author">Поддержка C21</div>
                <div class="message-text">${text}</div>
                ${buttons ? this.renderButtons(buttons) : ''}
            </div>
        `;
        
        this.chatBody.appendChild(messageDiv);
        this.scrollToBottom();
        
        if (buttons) {
            // Добавляем обработчики для кнопок
            setTimeout(() => {
                messageDiv.querySelectorAll('.bot-button').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.handleButtonClick(btn.dataset.value);
                    });
                });
            }, 100);
        } else {
            // Если нет кнопок, проверяем, нужен ли input (только если состояние установлено)
            if (this.currentState === 'question_text') {
                setTimeout(() => this.showQuestionInput(), 300);
            } else if (this.currentState && this.currentState.endsWith('_phone')) {
                setTimeout(() => this.showPhoneInput(), 300);
            }
            // Если currentState === null, не показываем input (финальное сообщение)
        }
    }
    
    // ========== Отправка заявки ==========
    async handleSubmit() {
        try {
            // Дополнительно удаляем все input поля на случай, если они еще есть
            const inputMessages = this.chatBody.querySelectorAll('.user-message-input');
            inputMessages.forEach(input => input.remove());
            
            // Также удаляем любые input поля по их id
            const phoneInput = document.getElementById('phone-input');
            const questionInput = document.getElementById('question-input');
            if (phoneInput && phoneInput.closest('.user-message-input')) {
                phoneInput.closest('.user-message-input').remove();
            }
            if (questionInput && questionInput.closest('.user-message-input')) {
                questionInput.closest('.user-message-input').remove();
            }
            
            // Показываем сообщение пользователя с номером
            this.showUserMessage(this.phoneNumber);
            
            // Отправляем на сервер
            const response = await fetch('/api/chat-request/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(this.formData)
            });
            
            const result = await response.json();
            
            // Сбрасываем состояние, чтобы форма не показывалась снова
            this.currentState = null;
            
            if (result.success) {
                // Показываем финальное сообщение от бота (без кнопок и input)
                this.showBotMessage('Спасибо за вашу заявку! Мы свяжемся с вами в ближайшее время.', null);
            } else {
                this.showBotMessage('Произошла ошибка при отправке заявки. Попробуйте позже или позвоните нам.', null);
            }
            
        } catch (error) {
            console.error('Ошибка отправки заявки:', error);
            // Убедимся, что форма удалена даже при ошибке
            const inputMessages = this.chatBody.querySelectorAll('.user-message-input');
            inputMessages.forEach(input => input.remove());
            this.showBotMessage('Произошла ошибка при отправке заявки. Попробуйте позже или позвоните нам.', null);
        }
    }
    
    showUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${text}</div>
            </div>
        `;
        
        this.chatBody.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    resetChat() {
        // Очищаем чат и показываем начальные кнопки
        const messages = this.chatBody.querySelectorAll('.chat-message');
        messages.forEach(msg => {
            if (!msg.classList.contains('support-message') || !msg.querySelector('.quick-actions')) {
                msg.remove();
            }
        });
        
        this.resetForm();
        
        // Убираем все input поля
        const inputs = this.chatBody.querySelectorAll('.user-message-input');
        inputs.forEach(input => input.remove());
    }
    
    // ========== Утилиты ==========
    formatPhone(value) {
        if (!value) return '';
        let phone = value.replace(/\D/g, '');
        if (phone.startsWith('8')) phone = '7' + phone.substring(1);
        if (!phone.startsWith('7')) phone = '7' + phone;
        
        let formatted = '+7';
        if (phone.length > 1) formatted += ' (' + phone.substring(1, 4);
        if (phone.length >= 5) formatted += ') ' + phone.substring(4, 7);
        if (phone.length >= 8) formatted += '-' + phone.substring(7, 9);
        if (phone.length >= 10) formatted += '-' + phone.substring(9, 11);
        
        return formatted;
    }
    
    getCookie(name) {
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
    
    scrollToBottom() {
        this.chatBody.scrollTop = this.chatBody.scrollHeight;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.chatBot = new ChatBot();
});


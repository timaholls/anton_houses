"""
API функции для управления подписками на обновления будущих проектов и акций
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from ..services.mongo_service import get_mongo_connection

# Настройки для отправки email
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@century21-ufa.ru')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
APP_PASSWORD = os.getenv('APP_PASSWORD', '')


@csrf_exempt
@require_http_methods(["POST"])
def subscribe_to_updates(request):
    """Подписаться на обновления будущих проектов и акций"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        email = (payload.get('email') or '').strip().lower()
        name = (payload.get('name') or '').strip()
        subscribe_to_projects = payload.get('subscribe_to_projects', True)
        subscribe_to_promotions = payload.get('subscribe_to_promotions', True)
        
        if not email:
            return JsonResponse({
                'success': False, 
                'error': 'Email обязателен'
            }, status=400)
        
        # Валидация email
        if '@' not in email or '.' not in email.split('@')[1]:
            return JsonResponse({
                'success': False, 
                'error': 'Некорректный email'
            }, status=400)
        
        db = get_mongo_connection()
        subscriptions = db['subscriptions']
        
        # Проверяем, есть ли уже подписка с таким email
        existing = subscriptions.find_one({'email': email})
        
        if existing:
            # Обновляем существующую подписку
            subscriptions.update_one(
                {'email': email},
                {
                    '$set': {
                        'name': name,
                        'subscribe_to_projects': subscribe_to_projects,
                        'subscribe_to_promotions': subscribe_to_promotions,
                        'updated_at': datetime.utcnow(),
                        'is_active': True
                    }
                }
            )
            message = 'Подписка обновлена'
        else:
            # Создаем новую подписку
            subscription = {
                'email': email,
                'name': name,
                'subscribe_to_projects': subscribe_to_projects,
                'subscribe_to_promotions': subscribe_to_promotions,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            subscriptions.insert_one(subscription)
            message = 'Подписка успешно оформлена'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def unsubscribe_from_updates(request):
    """Отписаться от обновлений"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        email = (payload.get('email') or '').strip().lower()
        
        if not email:
            return JsonResponse({
                'success': False, 
                'error': 'Email обязателен'
            }, status=400)
        
        db = get_mongo_connection()
        subscriptions = db['subscriptions']
        
        # Деактивируем подписку
        result = subscriptions.update_one(
            {'email': email},
            {
                '$set': {
                    'is_active': False,
                    'unsubscribed_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'Подписка отменена'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Подписка не найдена'
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def send_notification_email(subscribers, subject, message, project_name=None, promotion_title=None, project_data=None, promotion_data=None):
    """Отправить уведомления подписчикам"""
    if not APP_PASSWORD:
        print("APP_PASSWORD не настроен, пропускаем отправку email")
        return
    
    try:
        for subscriber in subscribers:
            email = subscriber['email']
            name = subscriber.get('name', '')
            
            # Персонализируем сообщение
            greeting = f"Здравствуйте, {name}!" if name else "Здравствуйте!"
            
            if project_name and project_data:
                email_subject = f"🏗️ Новый будущий проект: {project_name}"
                email_body = create_project_email_template(greeting, project_name, project_data)
            elif promotion_title and promotion_data:
                email_subject = f"🎟️ Новая акция: {promotion_title}"
                email_body = create_promotion_email_template(greeting, promotion_title, promotion_data)
            else:
                email_subject = subject
                email_body = f"""
{greeting}

{message}

С уважением,
Команда CENTURY 21
                """
            
            # Отправляем email
            print(f"Attempting to send email to {email}...")
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = email_subject
            
            msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
            server.quit()
            print(f"Сообщение отправлено на {email}")
            
    except Exception as e:
        print(f"Ошибка отправки email: {e}")


def create_project_email_template(greeting, project_name, project_data):
    """Создать шаблон письма для нового проекта"""
    city = project_data.get('city', 'Уфа')
    district = project_data.get('district', '')
    developer = project_data.get('developer', '')
    delivery_date = project_data.get('delivery_date', '')
    house_class = project_data.get('house_class', '')
    
    # Форматируем дату
    if delivery_date and isinstance(delivery_date, datetime):
        delivery_str = delivery_date.strftime('%d.%m.%Y')
    elif delivery_date:
        delivery_str = str(delivery_date)
    else:
        delivery_str = 'Уточняется'
    
    location = f"{city}" + (f", {district}" if district else "")
    
    return f"""
{greeting}

🏗️ Мы рады сообщить о новом будущем проекте!

📋 НАЗВАНИЕ: {project_name}
📍 МЕСТОПОЛОЖЕНИЕ: {location}
🏢 ЗАСТРОЙЩИК: {developer if developer else 'Уточняется'}
📅 СРОК СДАЧИ: {delivery_str}
🏠 КЛАСС ДОМА: {house_class if house_class else 'Уточняется'}

Этот проект станет отличным выбором для тех, кто ищет современное жилье в развивающемся районе города.

🔍 Следите за обновлениями на нашем сайте и в социальных сетях!

С уважением,
Команда CENTURY 21
📧 Email: {SENDER_EMAIL}
🌐 Сайт: century21-ufa.ru

---
Если вы больше не хотите получать уведомления о новых проектах, 
вы можете отписаться, перейдя по ссылке: /unsubscribe/
"""


def create_promotion_email_template(greeting, promotion_title, promotion_data):
    """Создать шаблон письма для новой акции"""
    description = promotion_data.get('description', '')
    starts_at = promotion_data.get('starts_at', '')
    ends_at = promotion_data.get('ends_at', '')
    
    # Форматируем даты
    if starts_at and isinstance(starts_at, datetime):
        start_str = starts_at.strftime('%d.%m.%Y')
    elif starts_at:
        start_str = str(starts_at)
    else:
        start_str = 'Уже действует'
    
    if ends_at and isinstance(ends_at, datetime):
        end_str = ends_at.strftime('%d.%m.%Y')
    elif ends_at:
        end_str = str(ends_at)
    else:
        end_str = 'Ограниченное время'
    
    return f"""
{greeting}

🎟️ У нас новая акция!

📋 НАЗВАНИЕ: {promotion_title}
📝 ОПИСАНИЕ: {description if description else 'Подробности уточняйте у наших специалистов'}
📅 ПЕРИОД ДЕЙСТВИЯ: {start_str} - {end_str}

Не упустите возможность воспользоваться выгодным предложением!

🔍 Подробности акции и условия участия уточняйте у наших специалистов.

С уважением,
Команда CENTURY 21
📧 Email: {SENDER_EMAIL}
🌐 Сайт: century21-ufa.ru

---
Если вы больше не хотите получать уведомления об акциях, 
вы можете отписаться, перейдя по ссылке: /unsubscribe/
"""


def notify_new_future_project(project_data):
    """Уведомить подписчиков о новом будущем проекте"""
    try:
        db = get_mongo_connection()
        subscriptions = db['subscriptions']
        
        # Получаем активных подписчиков на проекты
        subscribers = list(subscriptions.find({
            'is_active': True,
            'subscribe_to_projects': True
        }))
        
        if subscribers:
            # Извлекаем название из нового формата unified_houses
            project_name = 'Новый проект'
            if isinstance(project_data, dict):
                # Проверяем новый формат (development.name)
                dev = project_data.get('development', {})
                if dev and dev.get('name'):
                    project_name = dev['name']
                # Fallback на старый формат (name в корне)
                elif project_data.get('name'):
                    project_name = project_data['name']
            
            send_notification_email(
                subscribers, 
                "Новый будущий проект", 
                "", 
                project_name=project_name,
                project_data=project_data
            )
            
    except Exception as e:
        print(f"Ошибка уведомления о новом проекте: {e}")


def notify_new_promotion(promotion_data):
    """Уведомить подписчиков о новой акции"""
    try:
        db = get_mongo_connection()
        subscriptions = db['subscriptions']
        
        # Получаем активных подписчиков на акции
        subscribers = list(subscriptions.find({
            'is_active': True,
            'subscribe_to_promotions': True
        }))
        
        if subscribers:
            promotion_title = promotion_data.get('title', 'Новая акция')
            
            send_notification_email(
                subscribers, 
                "Новая акция", 
                "", 
                promotion_title=promotion_title,
                promotion_data=promotion_data
            )
            
    except Exception as e:
        print(f"Ошибка уведомления о новой акции: {e}")


@require_http_methods(["GET"])
def get_subscription_stats(request):
    """Получить статистику подписок (для админов)"""
    try:
        db = get_mongo_connection()
        subscriptions = db['subscriptions']
        
        total_subscriptions = subscriptions.count_documents({})
        active_subscriptions = subscriptions.count_documents({'is_active': True})
        project_subscribers = subscriptions.count_documents({
            'is_active': True,
            'subscribe_to_projects': True
        })
        promotion_subscribers = subscriptions.count_documents({
            'is_active': True,
            'subscribe_to_promotions': True
        })
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'project_subscribers': project_subscribers,
                'promotion_subscribers': promotion_subscribers
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

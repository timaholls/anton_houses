from django import template
import re

register = template.Library()


@register.filter(name='get_item')
def get_item(mapping, key):
    """Безопасно получить значение из dict по ключу с пробелами/русскими буквами."""
    if isinstance(mapping, dict):
        return mapping.get(key)
    return None


@register.filter(name='has_key')
def has_key(mapping, key):
    """Проверка наличия ключа в dict в шаблоне."""
    if isinstance(mapping, dict):
        return key in mapping
    return False


@register.filter(name='format_article_content')
def format_article_content(text):
    """Форматирует текст статьи с Markdown-подобным синтаксисом."""
    if not text:
        return ""
    
    # Если текст уже содержит HTML теги, возвращаем как есть
    if '<p>' in text or '<div>' in text or '<h' in text:
        return text
    
    # Разбиваем на строки
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            # Пустая строка - новый абзац
            formatted_lines.append('</p><p>')
        elif re.match(r'^\d+\.\s+', line):
            # Нумерованный список - заголовок
            formatted_lines.append(f'<h3>{line}</h3>')
        elif line.startswith('**') and line.endswith('**'):
            # Жирный текст
            formatted_lines.append(f'<strong>{line[2:-2]}</strong>')
        elif line.startswith('*') and line.endswith('*'):
            # Курсив
            formatted_lines.append(f'<em>{line[1:-1]}</em>')
        else:
            # Обычный текст
            formatted_lines.append(line)
    
    # Объединяем и оборачиваем в параграфы
    result = '<p>' + '</p><p>'.join(formatted_lines) + '</p>'
    
    # Очищаем пустые параграфы
    result = re.sub(r'<p></p>', '', result)
    result = re.sub(r'<p>\s*</p>', '', result)
    
    return result



from django import template

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



# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from django.core.management.base import BaseCommand
from django.conf import settings

from main.models import ResidentialComplex, SecondaryProperty


NOMINATIM_ENDPOINT = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'anton_houses-geocoder/1.0 (+https://example.com)'
CACHE_FILE = Path(settings.BASE_DIR) / 'geocode_cache.json'


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_cache(cache: dict):
    try:
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def build_address(city: str, district: str = '', street: str = '') -> str:
    parts = []
    if city:
        parts.append(city)
    if district:
        parts.append(district)
    if street:
        parts.append(street)
    # страна для повышения точности
    parts.append('Россия')
    return ', '.join([p for p in parts if p])


def geocode(query: str, timeout=8) -> tuple | None:
    params = {
        'q': query,
        'format': 'json',
        'addressdetails': 0,
        'limit': 1,
    }
    url = f"{NOMINATIM_ENDPOINT}?{urlencode(params)}"
    req = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data:
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                return lat, lon
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError):
        return None
    return None


class Command(BaseCommand):
    help = 'Автогеокодирование объектов (ResidentialComplex и SecondaryProperty) через Nominatim OSM с кэшем и лимитом.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=200, help='Максимум объектов для обработки за запуск')
        parser.add_argument('--delay', type=float, default=1.0, help='Пауза между запросами (сек)')
        parser.add_argument('--timeout', type=int, default=8, help='Таймаут запроса (сек)')
        parser.add_argument('--dry-run', action='store_true', help='Только показать, без сохранения')
        parser.add_argument('--reset-cache', action='store_true', help='Игнорировать кэш и перезаписать его')

    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        timeout = options['timeout']
        dry_run = options['dry_run']
        reset_cache = options['reset_cache']

        cache = {} if reset_cache else load_cache()
        processed = 0
        updated = 0

        def process_qs(qs, model_name):
            nonlocal processed, updated, cache
            for obj in qs:
                if processed >= limit:
                    break

                addr = build_address(obj.city, getattr(obj, 'district', ''), getattr(obj, 'street', ''))
                processed += 1

                if addr in cache:
                    coords = cache[addr]
                else:
                    coords = geocode(addr, timeout=timeout)
                    # fallback: город + Россия, если улица/район не дали результата
                    if not coords and obj.city:
                        simple_addr = build_address(obj.city)
                        coords = geocode(simple_addr, timeout=timeout)
                    cache[addr] = coords
                    save_cache(cache)
                    time.sleep(delay)

                if not coords:
                    self.stdout.write(self.style.WARNING(f'{model_name}#{obj.id}: не удалось геокодировать "{addr}"'))
                    continue

                lat, lon = coords
                if not dry_run:
                    obj.latitude = lat
                    obj.longitude = lon
                    obj.save(update_fields=['latitude', 'longitude'])
                    updated += 1
                self.stdout.write(f'{model_name}#{obj.id}: {lat:.6f}, {lon:.6f} — {addr}')

        # Очередность: сперва объекты без координат
        rc_qs = ResidentialComplex.objects.filter(latitude__isnull=True)[:limit]
        sp_qs = SecondaryProperty.objects.filter(latitude__isnull=True)[:max(0, limit - rc_qs.count())]

        self.stdout.write(self.style.NOTICE('Геокодирование ResidentialComplex...'))
        process_qs(rc_qs, 'RC')
        self.stdout.write(self.style.NOTICE('Геокодирование SecondaryProperty...'))
        process_qs(sp_qs, 'SP')

        self.stdout.write(self.style.SUCCESS(f'Готово. Обработано: {processed}, обновлено: {updated}, кэш: {len(cache)} записей')) 
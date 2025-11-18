#!/usr/bin/env python
"""Скрипт для поиска документов, у которых в _source_ids только avito"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from bson import ObjectId
from main.services.mongo_service import get_mongo_connection

db = get_mongo_connection()
col = db['unified_houses']

# Находим документы, где есть только avito (domrf и domclick = null)
filter_query = {
    '_source_ids.avito': {'$ne': None},
    '_source_ids.domrf': None,
    '_source_ids.domclick': None
}

cursor = col.find(filter_query, {'_id': 1, '_source_ids': 1})

ids = []
for doc in cursor:
    doc_id = str(doc['_id'])
    avito_id = doc.get('_source_ids', {}).get('avito', '')
    ids.append((doc_id, avito_id))

print(f"\nНайдено документов с только avito: {len(ids)}\n")
print("ID unified_houses -> ID avito:")
print("-" * 60)
for unified_id, avito_id in ids:
    print(f"{unified_id} -> {avito_id}")

print("\n" + "-" * 60)
print(f"Всего: {len(ids)}")


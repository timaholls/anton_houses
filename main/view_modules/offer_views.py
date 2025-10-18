"""Views для акций и спецпредложений"""
from django.shortcuts import render
from bson import ObjectId
from ..services.mongo_service import get_mongo_connection, get_special_offers_from_mongo
from ..s3_service import PLACEHOLDER_IMAGE_URL


def all_offers(request):
    """Страница всех акций (Mongo promotions; fallback SQL)."""
    def build_all_offers():
        try:
            db = get_mongo_connection()
            promotions = db['promotions']
            unified = db['unified_houses']
            q = {'is_active': True}
            adapters = []
            for p in promotions.find(q).sort('created_at', -1):
                class _Img: pass
                class _MainImg: pass
                class _RC: pass
                class _Offer: pass
                offer = _Offer()
                offer.id = str(p.get('_id'))
                offer.title = p.get('title', '')
                offer.description = p.get('description', '')
                offer.expires_at = p.get('expires_at')
                rc = _RC()
                comp = unified.find_one({'_id': p.get('complex_id')}) if isinstance(p.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(p.get('complex_id')))})
                rc.name = (comp.get('development', {}) or {}).get('name') if comp else ''
                rc.id = str(comp.get('_id')) if comp and comp.get('_id') else ''
                offer.residential_complex = rc
                photos = []
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        photos = comp.get('development', {}).get('photos', []) or []
                    else:
                        photos = (comp.get('domclick', {}) or {}).get('development', {}).get('photos', []) or []
                m = _MainImg(); i = _Img(); i.url = photos[0] if photos else PLACEHOLDER_IMAGE_URL; m.image = i
                offer.get_main_image = m
                adapters.append(offer)
            return adapters
        except Exception:
            from django.utils import timezone
            return get_special_offers_from_mongo()

    offers = build_all_offers()

    context = {
        'offers': offers,
    }
    return render(request, 'main/all_offers.html', context)


def offer_detail(request, offer_id):
    """Детальная страница акции (Mongo promotions со спадением на SQL)."""
    def build_offer_and_others(offer_id_str):
        try:
            db = get_mongo_connection()
            promotions = db['promotions']
            unified = db['unified_houses']
            p = promotions.find_one({'_id': ObjectId(str(offer_id_str))})
            if not p:
                raise Exception('not found')
            class _Img: pass
            class _MainImg: pass
            class _RC: pass
            class _Offer: pass
            def adapt(doc):
                comp = unified.find_one({'_id': doc.get('complex_id')}) if isinstance(doc.get('complex_id'), ObjectId) else unified.find_one({'_id': ObjectId(str(doc.get('complex_id')))})
                offer = _Offer()
                offer.id = str(doc.get('_id'))
                offer.title = doc.get('title', '')
                offer.description = doc.get('description', '')
                offer.expires_at = doc.get('expires_at')
                rc = _RC(); rc.name = (comp.get('development', {}) or {}).get('name') if comp else ''
                rc.id = str(comp.get('_id')) if comp and comp.get('_id') else ''
                offer.residential_complex = rc
                photos = []
                if comp:
                    if 'development' in comp and 'avito' not in comp:
                        photos = comp.get('development', {}).get('photos', []) or []
                    else:
                        photos = (comp.get('domclick', {}) or {}).get('development', {}).get('photos', []) or []
                m=_MainImg(); i=_Img(); i.url = ('/media/' + photos[0]) if photos else PLACEHOLDER_IMAGE_URL; m.image=i
                offer.get_main_image = m
                return offer
            offer = adapt(p)
            others = [adapt(doc) for doc in promotions.find({'_id': {'$ne': p['_id']}, 'is_active': True}).sort('created_at', -1).limit(8)]
            return offer, others
        except Exception:
            # Для числовых ID возвращаем 404, так как все данные теперь в MongoDB
            raise Exception('Offer not found - use MongoDB ID')

    offer, other_offers = build_offer_and_others(offer_id)
    return render(request, 'main/offer_detail.html', {'offer': offer, 'other_offers': other_offers})


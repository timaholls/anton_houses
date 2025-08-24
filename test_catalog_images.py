#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anton_houses.settings')
django.setup()

from main.models import ResidentialComplex, SecondaryProperty, Gallery

def test_residential_complex_images():
    """Test image loading for residential complexes"""
    print("=== Testing Residential Complex Images ===")
    
    complexes = ResidentialComplex.objects.all()[:3]
    for complex in complexes:
        print(f"\nComplex: {complex.name}")
        
        # Test get_catalog_images method
        catalog_images = complex.get_catalog_images()
        print(f"  Catalog images count: {len(catalog_images)}")
        
        for i, img in enumerate(catalog_images):
            if img.image:
                print(f"  Image {i+1}: {img.image.url}")
            else:
                print(f"  Image {i+1}: No image file")
        
        # Test individual image access
        if catalog_images:
            print(f"  Main image: {catalog_images[0].image.url if catalog_images[0].image else 'None'}")
            if len(catalog_images) > 1:
                print(f"  Image 2: {catalog_images[1].image.url if catalog_images[1].image else 'None'}")
            if len(catalog_images) > 2:
                print(f"  Image 3: {catalog_images[2].image.url if catalog_images[2].image else 'None'}")
            if len(catalog_images) > 3:
                print(f"  Image 4: {catalog_images[3].image.url if catalog_images[3].image else 'None'}")

def test_secondary_property_images():
    """Test image loading for secondary properties"""
    print("\n=== Testing Secondary Property Images ===")
    
    properties = SecondaryProperty.objects.all()[:3]
    for prop in properties:
        print(f"\nProperty: {prop.name}")
        
        # Test get_catalog_images method
        catalog_images = prop.get_catalog_images()
        print(f"  Catalog images count: {len(catalog_images)}")
        
        for i, img in enumerate(catalog_images):
            if img.image:
                print(f"  Image {i+1}: {img.image.url}")
            else:
                print(f"  Image {i+1}: No image file")
        
        # Test individual image access
        if catalog_images:
            print(f"  Main image: {catalog_images[0].image.url if catalog_images[0].image else 'None'}")
            if len(catalog_images) > 1:
                print(f"  Image 2: {catalog_images[1].image.url if catalog_images[1].image else 'None'}")
            if len(catalog_images) > 2:
                print(f"  Image 3: {catalog_images[2].image.url if catalog_images[2].image else 'None'}")
            if len(catalog_images) > 3:
                print(f"  Image 4: {catalog_images[3].image.url if catalog_images[3].image else 'None'}")

def test_gallery_data():
    """Test Gallery data for both categories"""
    print("\n=== Testing Gallery Data ===")
    
    # Test residential complex gallery
    residential_gallery = Gallery.objects.filter(category='residential_complex', is_active=True)
    print(f"Residential complex gallery items: {residential_gallery.count()}")
    
    # Test secondary property gallery
    secondary_gallery = Gallery.objects.filter(category='secondary_property', is_active=True)
    print(f"Secondary property gallery items: {secondary_gallery.count()}")
    
    # Show some examples
    print("\nResidential complex gallery examples:")
    for item in residential_gallery[:3]:
        print(f"  - {item.title} (Object ID: {item.object_id}, Main: {item.is_main})")
    
    print("\nSecondary property gallery examples:")
    for item in secondary_gallery[:3]:
        print(f"  - {item.title} (Object ID: {item.object_id}, Main: {item.is_main})")

if __name__ == "__main__":
    test_residential_complex_images()
    test_secondary_property_images()
    test_gallery_data()

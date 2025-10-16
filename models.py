from mongoengine import connect, disconnect
from app import Category, Product, ProductImage, ProductSpecification, ProductVariant
from datetime import datetime
import random

def setup_database():
    """Setup database connection"""
    disconnect()  # Disconnect any existing connections
    connect(
    db="ecommerce",
    host="localhost",
    port=27017
)
    print("Connected to MongoDB database: ecommerce_db")

def clear_existing_data():
    """Clear existing categories and products"""
    Category.objects.delete()
    Product.objects.delete()
    print("Cleared existing data")

def create_categories():
    """Create main categories and subcategories"""
    
    # Main Categories
    electronics = Category(
        name="Electronics",
        slug="electronics",
        description="Latest electronic gadgets, devices, and accessories",
        image_url="https://images.unsplash.com/photo-1498049794561-7780e7231661?w=300",
        is_active=True,
        display_order=1
    )
    electronics.save()

    fashion = Category(
        name="Fashion",
        slug="fashion",
        description="Trendy clothing, shoes, and accessories for everyone",
        image_url="https://images.unsplash.com/photo-1445205170230-053b83016050?w=300",
        is_active=True,
        display_order=2
    )
    fashion.save()

    mobiles = Category(
        name="Mobile Phones",
        slug="mobile-phones",
        description="Smartphones, feature phones, and mobile accessories",
        image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300",
        is_active=True,
        display_order=3
    )
    mobiles.save()

    # Electronics Subcategories
    laptop_category = Category(
        name="Laptops",
        slug="laptops",
        description="Powerful laptops for work, gaming, and creativity",
        parent_category=electronics,
        image_url="https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=300",
        is_active=True,
        display_order=1
    )
    laptop_category.save()

    tv_category = Category(
        name="Televisions",
        slug="televisions",
        description="Smart TVs, 4K displays, and home entertainment systems",
        parent_category=electronics,
        image_url="https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=300",
        is_active=True,
        display_order=2
    )
    tv_category.save()

    # Fashion Subcategories
    mens_fashion = Category(
        name="Men's Fashion",
        slug="mens-fashion",
        description="Clothing, shoes, and accessories for men",
        parent_category=fashion,
        image_url="https://images.unsplash.com/photo-1617137968427-85924c800a22?w=300",
        is_active=True,
        display_order=1
    )
    mens_fashion.save()

    womens_fashion = Category(
        name="Women's Fashion",
        slug="womens-fashion",
        description="Clothing, shoes, and accessories for women",
        parent_category=fashion,
        image_url="https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=300",
        is_active=True,
        display_order=2
    )
    womens_fashion.save()

    return {
        'electronics': electronics,
        'fashion': fashion,
        'mobiles': mobiles,
        'laptops': laptop_category,
        'tvs': tv_category,
        'mens_fashion': mens_fashion,
        'womens_fashion': womens_fashion
    }

def create_electronics_products(categories):
    """Create electronics products"""
    
    # Laptop Products
    macbook_pro = Product(
        name="Apple MacBook Pro 16-inch",
        slug="apple-macbook-pro-16-inch",
        description="The most powerful MacBook Pro ever with M2 Max chip, 16-inch Liquid Retina XDR display, and up to 96GB of unified memory.",
        short_description="16-inch MacBook Pro with M2 Max chip",
        sku="MBP16M2-2023",
        category=categories['laptops'],
        brand="Apple",
        tags=["laptop", "macbook", "apple", "premium", "work"],
        price=2499.99,
        sale_price=2299.99,
        cost_price=1800.00,
        stock_quantity=25,
        weight=2.15,
        dimensions={"length": 35.57, "width": 24.81, "height": 1.68, "unit": "cm"},
        shipping_class="standard",
        is_active=True,
        is_featured=True,
        is_digital=False,
        published_at=datetime.utcnow()
    )
    
    macbook_pro.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400",
            alt_text="Apple MacBook Pro 16-inch Front View",
            is_primary=True,
            display_order=1
        ),
        ProductImage(
            url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400",
            alt_text="Apple MacBook Pro Keyboard",
            is_primary=False,
            display_order=2
        )
    ]
    
    macbook_pro.specifications = [
        ProductSpecification(key="Processor", value="Apple M2 Max 12-core"),
        ProductSpecification(key="Memory", value="32GB Unified Memory"),
        ProductSpecification(key="Storage", value="1TB SSD"),
        ProductSpecification(key="Display", value="16.2-inch Liquid Retina XDR"),
        ProductSpecification(key="Battery", value="Up to 22 hours")
    ]
    macbook_pro.save()

    # Gaming Laptop
    gaming_laptop = Product(
        name="ASUS ROG Strix G15 Gaming Laptop",
        slug="asus-rog-strix-g15-gaming-laptop",
        description="High-performance gaming laptop with AMD Ryzen 9 processor, NVIDIA GeForce RTX 4070, and 165Hz display.",
        short_description="Powerful gaming laptop for serious gamers",
        sku="ASUS-ROG-G15-2023",
        category=categories['laptops'],
        brand="ASUS",
        tags=["gaming", "laptop", "gaming-laptop", "rtx", "amd"],
        price=1799.99,
        cost_price=1400.00,
        stock_quantity=15,
        weight=2.30,
        dimensions={"length": 35.4, "width": 25.9, "height": 2.26, "unit": "cm"},
        is_active=True,
        is_featured=False
    )
    
    gaming_laptop.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400",
            alt_text="ASUS ROG Strix Gaming Laptop",
            is_primary=True,
            display_order=1
        )
    ]
    
    gaming_laptop.specifications = [
        ProductSpecification(key="Processor", value="AMD Ryzen 9 7945HX"),
        ProductSpecification(key="Graphics", value="NVIDIA GeForce RTX 4070 8GB"),
        ProductSpecification(key="RAM", value="16GB DDR5"),
        ProductSpecification(key="Storage", value="1TB NVMe SSD"),
        ProductSpecification(key="Display", value="15.6-inch QHD 165Hz")
    ]
    gaming_laptop.save()

    # TV Products
    samsung_tv = Product(
        name="Samsung 65-inch QLED 4K Smart TV",
        slug="samsung-65-inch-qled-4k-smart-tv",
        description="Immersive 65-inch QLED 4K TV with Quantum HDR, Smart TV capabilities, and Alexa built-in.",
        short_description="65-inch Samsung QLED 4K Smart TV",
        sku="SAMSUNG-Q65-2023",
        category=categories['tvs'],
        brand="Samsung",
        tags=["tv", "television", "4k", "smart-tv", "qled"],
        price=1199.99,
        sale_price=999.99,
        cost_price=800.00,
        stock_quantity=30,
        weight=23.5,
        dimensions={"length": 145.1, "width": 83.4, "height": 30.5, "unit": "cm"},
        is_active=True,
        is_featured=True
    )
    
    samsung_tv.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400",
            alt_text="Samsung 65-inch QLED TV",
            is_primary=True,
            display_order=1
        )
    ]
    
    samsung_tv.specifications = [
        ProductSpecification(key="Screen Size", value="65 inches"),
        ProductSpecification(key="Resolution", value="4K Ultra HD (3840x2160)"),
        ProductSpecification(key="Display Technology", value="QLED"),
        ProductSpecification(key="Smart Platform", value="Tizen"),
        ProductSpecification(key="HDR", value="Quantum HDR")
    ]
    samsung_tv.save()

def create_fashion_products(categories):
    """Create fashion products"""
    
    # Men's Fashion
    mens_jacket = Product(
        name="Men's Waterproof Winter Jacket",
        slug="mens-waterproof-winter-jacket",
        description="Premium waterproof and windproof winter jacket with thermal insulation. Perfect for cold weather conditions.",
        short_description="Waterproof winter jacket for men",
        sku="MJ-WINTER-001",
        category=categories['mens_fashion'],
        brand="OutdoorGear",
        tags=["jacket", "winter", "waterproof", "men", "outdoor"],
        price=129.99,
        sale_price=99.99,
        cost_price=65.00,
        stock_quantity=45,
        weight=0.85,
        dimensions={"length": 60, "width": 45, "height": 10, "unit": "cm"},
        is_active=True,
        is_featured=True
    )
    
    mens_jacket.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400",
            alt_text="Men's Winter Jacket Front",
            is_primary=True,
            display_order=1
        )
    ]
    
    mens_jacket.specifications = [
        ProductSpecification(key="Material", value="Nylon with Polyester lining"),
        ProductSpecification(key="Waterproof", value="Yes (5000mm rating)"),
        ProductSpecification(key="Insulation", value="Thermal synthetic"),
        ProductSpecification(key="Pockets", value="4 (2 chest, 2 hand)"),
        ProductSpecification(key="Hood", value="Adjustable with fur trim")
    ]
    
    # Add variants for sizes
    mens_jacket.has_variants = True
    mens_jacket.variants = [
        ProductVariant(
            sku="MJ-WINTER-001-S",
            size="S",
            color="Black",
            stock_quantity=15,
            price_adjustment=0
        ),
        ProductVariant(
            sku="MJ-WINTER-001-M",
            size="M",
            color="Black",
            stock_quantity=20,
            price_adjustment=0
        ),
        ProductVariant(
            sku="MJ-WINTER-001-L",
            size="L",
            color="Black",
            stock_quantity=10,
            price_adjustment=0
        )
    ]
    mens_jacket.save()

    # Women's Fashion
    womens_dress = Product(
        name="Women's Summer Floral Dress",
        slug="womens-summer-floral-dress",
        description="Elegant floral print summer dress made from breathable cotton. Perfect for warm weather and casual occasions.",
        short_description="Floral summer dress for women",
        sku="WD-FLORAL-001",
        category=categories['womens_fashion'],
        brand="FashionStyle",
        tags=["dress", "summer", "floral", "women", "casual"],
        price=59.99,
        cost_price=35.00,
        stock_quantity=60,
        weight=0.35,
        dimensions={"length": 55, "width": 40, "height": 5, "unit": "cm"},
        is_active=True,
        is_featured=False
    )
    
    womens_dress.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400",
            alt_text="Women's Floral Summer Dress",
            is_primary=True,
            display_order=1
        )
    ]
    
    womens_dress.specifications = [
        ProductSpecification(key="Material", value="100% Cotton"),
        ProductSpecification(key="Care", value="Machine washable"),
        ProductSpecification(key="Length", value="Knee-length"),
        ProductSpecification(key="Style", value="A-line with floral print")
    ]
    
    womens_dress.has_variants = True
    womens_dress.variants = [
        ProductVariant(
            sku="WD-FLORAL-001-XS",
            size="XS",
            color="Multicolor Floral",
            stock_quantity=20,
            price_adjustment=0
        ),
        ProductVariant(
            sku="WD-FLORAL-001-S",
            size="S",
            color="Multicolor Floral",
            stock_quantity=25,
            price_adjustment=0
        ),
        ProductVariant(
            sku="WD-FLORAL-001-M",
            size="M",
            color="Multicolor Floral",
            stock_quantity=15,
            price_adjustment=0
        )
    ]
    womens_dress.save()

    # Sneakers
    running_shoes = Product(
        name="Running Shoes with Cushioning",
        slug="running-shoes-with-cushioning",
        description="Professional running shoes with advanced cushioning technology, breathable mesh, and durable rubber outsole.",
        short_description="Comfortable running shoes for athletes",
        sku="RS-PRO-2023",
        category=categories['mens_fashion'],
        brand="RunFast",
        tags=["shoes", "sneakers", "running", "sports", "athletic"],
        price=89.99,
        sale_price=79.99,
        cost_price=45.00,
        stock_quantity=75,
        weight=0.65,
        dimensions={"length": 32, "width": 22, "height": 12, "unit": "cm"},
        is_active=True,
        is_featured=True
    )
    
    running_shoes.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
            alt_text="Running Shoes Side View",
            is_primary=True,
            display_order=1
        )
    ]
    
    running_shoes.specifications = [
        ProductSpecification(key="Material", value="Breathable mesh with synthetic overlays"),
        ProductSpecification(key="Cushioning", value="Advanced foam technology"),
        ProductSpecification(key="Outsole", value="Durable rubber with traction pattern"),
        ProductSpecification(key="Closure", value="Lace-up"),
        ProductSpecification(key="Best For", value="Running, Training, Gym")
    ]
    
    running_shoes.has_variants = True
    running_shoes.variants = [
        ProductVariant(
            sku="RS-PRO-2023-8",
            size="8",
            color="Blue/Black",
            stock_quantity=25,
            price_adjustment=0
        ),
        ProductVariant(
            sku="RS-PRO-2023-9",
            size="9",
            color="Blue/Black",
            stock_quantity=30,
            price_adjustment=0
        ),
        ProductVariant(
            sku="RS-PRO-2023-10",
            size="10",
            color="Blue/Black",
            stock_quantity=20,
            price_adjustment=0
        )
    ]
    running_shoes.save()

def create_mobile_products(categories):
    """Create mobile phone products"""
    
    # Flagship Smartphone
    flagship_phone = Product(
        name="Samsung Galaxy S24 Ultra",
        slug="samsung-galaxy-s24-ultra",
        description="Flagship smartphone with advanced camera system, S Pen, and powerful Snapdragon processor. Featuring a stunning 6.8-inch Dynamic AMOLED display.",
        short_description="Premium Android smartphone with S Pen",
        sku="SGS24U-512GB",
        category=categories['mobiles'],
        brand="Samsung",
        tags=["smartphone", "android", "flagship", "camera", "5g"],
        price=1199.99,
        cost_price=850.00,
        stock_quantity=35,
        weight=0.232,
        dimensions={"length": 16.3, "width": 7.8, "height": 0.88, "unit": "cm"},
        is_active=True,
        is_featured=True
    )
    
    flagship_phone.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            alt_text="Samsung Galaxy S24 Ultra Front",
            is_primary=True,
            display_order=1
        )
    ]
    
    flagship_phone.specifications = [
        ProductSpecification(key="Display", value="6.8-inch Dynamic AMOLED 2X"),
        ProductSpecification(key="Processor", value="Snapdragon 8 Gen 3"),
        ProductSpecification(key="Storage", value="512GB"),
        ProductSpecification(key="RAM", value="12GB"),
        ProductSpecification(key="Camera", value="200MP + 12MP + 10MP + 10MP"),
        ProductSpecification(key="Battery", value="5000mAh")
    ]
    
    flagship_phone.has_variants = True
    flagship_phone.variants = [
        ProductVariant(
            sku="SGS24U-256GB-BLK",
            size="256GB",
            color="Phantom Black",
            stock_quantity=15,
            price_adjustment=-100.00
        ),
        ProductVariant(
            sku="SGS24U-512GB-BLK",
            size="512GB",
            color="Phantom Black",
            stock_quantity=12,
            price_adjustment=0
        ),
        ProductVariant(
            sku="SGS24U-512GB-GRY",
            size="512GB",
            color="Titanium Gray",
            stock_quantity=8,
            price_adjustment=0
        )
    ]
    flagship_phone.save()

    # Budget Smartphone
    budget_phone = Product(
        name="Google Pixel 7a",
        slug="google-pixel-7a",
        description="Affordable smartphone with excellent camera quality, clean Android experience, and reliable performance.",
        short_description="Budget-friendly smartphone with great camera",
        sku="GPIXEL7A-128GB",
        category=categories['mobiles'],
        brand="Google",
        tags=["smartphone", "android", "budget", "camera", "pixel"],
        price=449.99,
        sale_price=399.99,
        cost_price=300.00,
        stock_quantity=50,
        weight=0.193,
        dimensions={"length": 15.2, "width": 7.1, "height": 0.89, "unit": "cm"},
        is_active=True,
        is_featured=False
    )
    
    budget_phone.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=400",
            alt_text="Google Pixel 7a Smartphone",
            is_primary=True,
            display_order=1
        )
    ]
    
    budget_phone.specifications = [
        ProductSpecification(key="Display", value="6.1-inch OLED"),
        ProductSpecification(key="Processor", value="Google Tensor G2"),
        ProductSpecification(key="Storage", value="128GB"),
        ProductSpecification(key="RAM", value="8GB"),
        ProductSpecification(key="Camera", value="64MP + 13MP"),
        ProductSpecification(key="Battery", value="4385mAh")
    ]
    
    budget_phone.has_variants = True
    budget_phone.variants = [
        ProductVariant(
            sku="GPIXEL7A-128GB-BLK",
            size="128GB",
            color="Charcoal",
            stock_quantity=25,
            price_adjustment=0
        ),
        ProductVariant(
            sku="GPIXEL7A-128GB-SNW",
            size="128GB",
            color="Snow",
            stock_quantity=15,
            price_adjustment=0
        ),
        ProductVariant(
            sku="GPIXEL7A-128GB-SEA",
            size="128GB",
            color="Sea",
            stock_quantity=10,
            price_adjustment=0
        )
    ]
    budget_phone.save()

    # Gaming Phone
    gaming_phone = Product(
        name="ASUS ROG Phone 8",
        slug="asus-rog-phone-8",
        description="Dedicated gaming smartphone with 165Hz display, advanced cooling system, and gaming-optimized features.",
        short_description="Professional gaming smartphone",
        sku="ROG-PHONE8-512GB",
        category=categories['mobiles'],
        brand="ASUS",
        tags=["gaming", "smartphone", "gaming-phone", "high-refresh", "performance"],
        price=999.99,
        cost_price=700.00,
        stock_quantity=20,
        weight=0.239,
        dimensions={"length": 17.3, "width": 7.7, "height": 1.04, "unit": "cm"},
        is_active=True,
        is_featured=True
    )
    
    gaming_phone.images = [
        ProductImage(
            url="https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400",
            alt_text="ASUS ROG Phone 8 Gaming Phone",
            is_primary=True,
            display_order=1
        )
    ]
    
    gaming_phone.specifications = [
        ProductSpecification(key="Display", value="6.78-inch AMOLED 165Hz"),
        ProductSpecification(key="Processor", value="Snapdragon 8 Gen 3"),
        ProductSpecification(key="Storage", value="512GB UFS 4.0"),
        ProductSpecification(key="RAM", value="16GB LPDDR5X"),
        ProductSpecification(key="Cooling", value="AeroActive Cooler 8 compatible"),
        ProductSpecification(key="Battery", value="6000mAh with 65W charging")
    ]
    
    gaming_phone.has_variants = True
    gaming_phone.variants = [
        ProductVariant(
            sku="ROG-PHONE8-256GB-BLK",
            size="256GB",
            color="Phantom Black",
            stock_quantity=8,
            price_adjustment=-100.00
        ),
        ProductVariant(
            sku="ROG-PHONE8-512GB-BLK",
            size="512GB",
            color="Phantom Black",
            stock_quantity=7,
            price_adjustment=0
        ),
        ProductVariant(
            sku="ROG-PHONE8-512GB-RED",
            size="512GB",
            color="Storm Red",
            stock_quantity=5,
            price_adjustment=0
        )
    ]
    gaming_phone.save()

def add_sample_reviews():
    """Add sample reviews to some products"""
    products = Product.objects()
    
    review_comments = [
        "Excellent product! Exceeded my expectations.",
        "Good value for money, would recommend.",
        "Fast shipping and great quality.",
        "Perfect for my needs, very satisfied.",
        "Amazing features and build quality.",
        "Better than I expected, great purchase!",
        "Good product but could be improved.",
        "Works exactly as described, very happy.",
        "High quality and durable product.",
        "Impressive performance and design."
    ]
    
    for product in products:
        # Add 3-8 random reviews for each product
        num_reviews = random.randint(3, 8)
        for i in range(num_reviews):
            rating = random.randint(3, 5)  # Mostly positive reviews
            comment = random.choice(review_comments)
            
            # Create a mock user reference (in real app, this would be actual User objects)
            from mongoengine import ReferenceField
            # For demo purposes, we'll skip actual user references
            # product.add_review(user_id, rating, comment)
            
            # Instead, we'll manually create review objects
            from models import ProductReview
            review = ProductReview(
                rating=rating,
                title=f"Review {i+1}",
                comment=comment,
                verified_purchase=random.choice([True, False]),
                helpful_votes=random.randint(0, 25)
            )
            product.reviews.append(review)
        
        product.save()

def main():
    """Main function to populate the database"""
    print("Starting database population...")
    
    try:
        # Setup database connection
        setup_database()
        
        # Clear existing data
        clear_existing_data()
        
        # Create categories
        print("Creating categories...")
        categories = create_categories()
        
        # Create products
        print("Creating electronics products...")
        create_electronics_products(categories)
        
        print("Creating fashion products...")
        create_fashion_products(categories)
        
        print("Creating mobile products...")
        create_mobile_products(categories)
        
        # Add sample reviews
        print("Adding sample reviews...")
        add_sample_reviews()
        
        # Print summary
        category_count = Category.objects.count()
        product_count = Product.objects.count()
        
        print(f"\nDatabase population completed successfully!")
        print(f"Created {category_count} categories")
        print(f"Created {product_count} products")
        
        # Print product list
        print("\nProducts created:")
        for product in Product.objects():
            print(f"- {product.name} (${product.price}) - {product.stock_quantity} in stock")
            
    except Exception as e:
        print(f"Error populating database: {e}")
        raise

if __name__ == "__main__":
    main()
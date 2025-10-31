from datetime import datetime
from typing import Optional
from mongoengine import connect, EmbeddedDocument, Document
from mongoengine.fields import (
    StringField, DecimalField, IntField, ListField, 
    EmbeddedDocumentField, EmbeddedDocumentListField,
    DateTimeField, BooleanField, URLField, DictField,
    ReferenceField, EmailField, ObjectIdField
)
from datetime import timedelta
from bson import ObjectId

# Import your document classes (make sure these match your existing definitions)
# Assuming the document classes are already defined as per your code

# --------------------------
# MongoDB connection
# --------------------------
connect(
    db="ecommerce",
    host="localhost",
    port=27017
)


# --------------------------
# Embedded Documents
# --------------------------

class ProductImage(EmbeddedDocument):
    """Embedded document for product images"""
    url = URLField(required=True)
    alt_text = StringField(max_length=200)
    is_primary = BooleanField(default=False)
    display_order = IntField(default=0)

class ProductVariant(EmbeddedDocument):
    """Embedded document for product variants"""
    sku = StringField(required=True, max_length=100)
    size = StringField(max_length=50)
    color = StringField(max_length=50)
    material = StringField(max_length=100)
    weight = DecimalField(precision=2)
    price_adjustment = DecimalField(precision=2, default=0.00)
    stock_quantity = IntField(default=0)
    images = EmbeddedDocumentListField(ProductImage)

class ProductReview(EmbeddedDocument):
    """Embedded document for product reviews"""
    review_id = ObjectIdField(required=True, default=lambda: ObjectId())
    user_id = ReferenceField('User', required=True)
    rating = IntField(required=True, min_value=1, max_value=5)
    title = StringField(max_length=200)
    comment = StringField(max_length=2000)
    verified_purchase = BooleanField(default=False)
    helpful_votes = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

class ProductSpecification(EmbeddedDocument):
    """Embedded document for product specifications"""
    key = StringField(required=True, max_length=100)
    value = StringField(required=True, max_length=500)

class PriceHistory(EmbeddedDocument):
    """Embedded document for price history tracking"""
    price = DecimalField(required=True, precision=2)
    sale_price = DecimalField(precision=2)
    effective_date = DateTimeField(default=datetime.utcnow)
    reason = StringField(max_length=200)  # "price_change", "sale", "discount", etc.


# --------------------------
# Main Documents
# --------------------------

class Category(Document):
    """Category document for product categorization"""
    meta = {
        'collection': 'categories',
        'indexes': [
            'name',
            'slug',
            'parent_category',
            {'fields': ['name', 'parent_category'], 'unique': True}
        ]
    }
    
    name = StringField(required=True, max_length=100)
    slug = StringField(required=True, max_length=100, unique=True)
    description = StringField(max_length=500)
    parent_category = ReferenceField('self', null=True)
    image_url = URLField()
    is_active = BooleanField(default=True)
    display_order = IntField(default=0)
    meta_title = StringField(max_length=200)
    meta_description = StringField(max_length=500)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def clean(self):
        """Automatically generate slug if not provided"""
        if not self.slug and self.name:
            self.slug = self.name.lower().replace(' ', '-')
        self.updated_at = datetime.utcnow()

class Product(Document):
    """Main Product document"""
    meta = {
        'collection': 'products',
        'indexes': [
            'name',
            'category',
            'brand',
            'price',
            'is_active',
            'created_at',
            {'fields': ['name', 'brand'], 'unique': False},
            {'fields': ['$name', '$description', '$tags'], 'default_language': 'english'}
        ],
        'ordering': ['-created_at']
    }
    
    # Basic Information
    name = StringField(required=True, max_length=200)
    slug = StringField(required=True, max_length=200, unique=True)
    description = StringField(required=True, max_length=5000)
    short_description = StringField(max_length=500)
    sku = StringField(required=True, max_length=100, unique=True)
    
    # Categorization
    category = ReferenceField(Category, required=True)
    brand = StringField(required=True, max_length=100)
    tags = ListField(StringField(max_length=50))
    
    # Pricing
    price = DecimalField(required=True, precision=2)
    sale_price = DecimalField(precision=2)
    cost_price = DecimalField(precision=2)
    price_history = EmbeddedDocumentListField(PriceHistory)
    
    # Inventory
    stock_quantity = IntField(required=True, default=0)
    low_stock_threshold = IntField(default=5)
    manage_stock = BooleanField(default=True)
    allow_backorders = BooleanField(default=False)
    
    # Product Variants
    has_variants = BooleanField(default=False)
    variants = EmbeddedDocumentListField(ProductVariant)
    
    # Media
    images = EmbeddedDocumentListField(ProductImage)
    primary_image = URLField()
    
    # Specifications
    specifications = EmbeddedDocumentListField(ProductSpecification)
    
    # Reviews and Ratings
    reviews = EmbeddedDocumentListField(ProductReview)
    average_rating = DecimalField(precision=2, min_value=0, max_value=5, default=0)
    review_count = IntField(default=0)
    
    # Shipping
    weight = DecimalField(precision=2)  # in kg
    dimensions = DictField()  # {length: 10, width: 5, height: 3, unit: 'cm'}
    shipping_class = StringField(max_length=50)
    
    # SEO
    meta_title = StringField(max_length=200)
    meta_description = StringField(max_length=500)
    meta_keywords = ListField(StringField(max_length=50))
    
    # Status and Dates
    is_active = BooleanField(default=True)
    is_featured = BooleanField(default=False)
    is_digital = BooleanField(default=False)  # For digital products
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    published_at = DateTimeField()
    
    def clean(self):
        """Automatically update fields before saving"""
        # Generate slug if not provided
        if not self.slug and self.name:
            self.slug = self.name.lower().replace(' ', '-')
        
        # Set primary image
        if self.images and not self.primary_image:
            primary_img = next((img for img in self.images if img.is_primary), self.images[0])
            self.primary_image = primary_img.url
        
        # Calculate average rating
        if self.reviews:
            total_rating = sum(review.rating for review in self.reviews)
            self.average_rating = round(total_rating / len(self.reviews), 2)
            self.review_count = len(self.reviews)
        
        # Set published_at if not set and product is active
        if self.is_active and not self.published_at:
            self.published_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0
    
    def is_on_sale(self):
        """Check if product is on sale"""
        return bool(self.sale_price and self.sale_price < self.price)
    
    def get_current_price(self):
        """Get current price (sale price if available)"""
        return self.sale_price if self.is_on_sale() else self.price
    
    def add_review(self, user_id, rating, comment, title=None, verified_purchase=False):
        """Add a review to the product"""
        review = ProductReview(
            user_id=user_id,
            rating=rating,
            title=title,
            comment=comment,
            verified_purchase=verified_purchase
        )
        self.reviews.append(review)
        self.save()
    
    def update_stock(self, quantity):
        """Update stock quantity"""
        if self.manage_stock:
            self.stock_quantity += quantity
            self.save()

class User(Document):
    """User document for customer accounts"""
    meta = {
        'collection': 'users',
        'indexes': [
            'email',
            'username',
            'created_at',
            'is_admin',
            'is_staff'
        ]
    }
    
    # Authentication
    username = StringField(required=True, max_length=50, unique=True)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True, max_length=255)
    
    # Personal Information
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50)
    phone = StringField(max_length=20)
    
    # Address
    addresses = ListField(ReferenceField('Address'))
    default_shipping_address = ReferenceField('Address')
    default_billing_address = ReferenceField('Address')
    
    # Preferences
    email_preferences = DictField(default={
        'promotional': True,
        'order_updates': True,
        'price_drops': True
    })
    
    # Status
    is_admin = BooleanField(default=False)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=True)
    is_verified = BooleanField(default=False)
    last_login = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    @staticmethod
    def pre_delete(sender, document, **kwargs):
        Session.objects(user_id=document).delete()

class Address(EmbeddedDocument):
    """Embedded document for user addresses"""
    address_type = StringField(required=True, choices=('shipping', 'billing', 'both'))
    first_name = StringField(required=True, max_length=50)
    last_name = StringField(required=True, max_length=50)
    street_address = StringField(required=True, max_length=200)
    apartment = StringField(max_length=50)
    city = StringField(required=True, max_length=50)
    state = StringField(required=True, max_length=50)
    postal_code = StringField(required=True, max_length=20)
    country = StringField(required=True, max_length=50, default='United States')
    phone = StringField(max_length=20)
    is_default = BooleanField(default=False)


class OrderItem(EmbeddedDocument):
    """Embedded document for order items"""
    product = ReferenceField(Product, required=True)
    product_name = StringField(required=True, max_length=200)  # Snapshot of product name
    product_sku = StringField(required=True, max_length=100)   # Snapshot of product SKU
    variant_sku = StringField(max_length=100)  # For variant products
    quantity = IntField(required=True, min_value=1)
    unit_price = DecimalField(required=True, precision=2)
    total_price = DecimalField(required=True, precision=2)
    
    def clean(self):
        """Calculate total price"""
        self.total_price = self.unit_price * self.quantity

class Order(Document):
    """Order document for customer purchases"""
    meta = {
        'collection': 'orders',
        'indexes': [
            'order_number',
            'user',
            'status',
            'created_at',
            'email'
        ]
    }
    
    # Order Identification
    order_number = StringField(required=True, unique=True)
    user = ReferenceField(User, null=True)  # null for guest checkout
    email = EmailField(required=True)
    
    # Order Items
    items = ListField(EmbeddedDocumentField('OrderItem'))
    
    # Pricing
    subtotal = DecimalField(required=True, precision=2)
    shipping_cost = DecimalField(required=True, precision=2, default=0.00)
    tax_amount = DecimalField(required=True, precision=2, default=0.00)
    discount_amount = DecimalField(required=True, precision=2, default=0.00)
    total_amount = DecimalField(required=True, precision=2)
    
    # Addresses
    shipping_address = EmbeddedDocumentField(Address, required=True)
    billing_address = EmbeddedDocumentField(Address, required=True)
    
    # Payment
    payment_method = StringField(required=True, max_length=50)
    payment_status = StringField(required=True, max_length=20, 
                                choices=('pending', 'paid', 'failed', 'refunded'),
                                default='pending')
    transaction_id = StringField(max_length=100)
    
    # Shipping
    shipping_method = StringField(required=True, max_length=50)
    tracking_number = StringField(max_length=100)
    shipping_status = StringField(required=True, max_length=20,
                                 choices=('pending', 'processing', 'shipped', 'delivered'),
                                 default='pending')
    
    # Status and Dates
    status = StringField(required=True, max_length=20,
                        choices=('pending', 'confirmed', 'processing', 'shipped', 
                                'delivered', 'cancelled', 'refunded'),
                        default='pending')
    notes = StringField(max_length=1000)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    completed_at = DateTimeField()


class Session(Document):
    """Session document for user and admin sessions"""
    meta = {
        'collection': 'sessions',
        'indexes': [
            'session_id',
            'user_id',
            'session_type',
            'expires_at'
        ]
    }
    
    session_id = StringField(required=True, max_length=500, unique=True)
    user_id = ReferenceField(User)
    session_type = StringField(required=True, choices=('user', 'admin'), default='user')
    is_authenticated = BooleanField(default=False)
    user_data = DictField()  # Store user-specific data
    created_at = DateTimeField(default=datetime.utcnow)
    expires_at = DateTimeField(default=lambda: datetime.utcnow() + timedelta(hours=24))
    
    def clean(self):
        """Set expiration time"""
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    







# --------------------------
# Session Management
# --------------------------

class SessionManager:
    @staticmethod
    def create_session(user_id: str = None, session_type: str = 'user', user_data: dict = None) -> str:
        """Create a new session and return session_id"""
        session_id = str(ObjectId())
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            session_type=session_type,
            is_authenticated=True,
            user_data=user_data or {}
        )
        session.save()
        return session_id
    
    @staticmethod
    def verify_session(session_id: str, session_type: str = None) -> bool:
        """Verify if session is valid and not expired"""
        if not session_id:
            return False
            
        session = Session.objects(session_id=session_id).first()
        if not session:
            return False
            
        if session.is_expired():
            session.delete()
            return False
            
        if session_type and session.session_type != session_type:
            return False
            
        return session.is_authenticated
    
    @staticmethod
    def get_session_data(session_id: str) -> Optional[dict]:
        """Get session data"""
        session = Session.objects(session_id=session_id).first()
        if session and not session.is_expired():
            return {
                'user_id': str(session.user_id.id) if session.user_id else None,
                'session_type': session.session_type,
                'user_data': session.user_data
            }
        return None
    
    @staticmethod
    def delete_session(session_id: str):
        """Delete a session"""
        Session.objects(session_id=session_id).delete()
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions"""
        expired_sessions = Session.objects(expires_at__lt=datetime.utcnow())
        expired_sessions.delete()



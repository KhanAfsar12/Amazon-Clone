from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from typing import List, Optional, Type, Any
import json
import uvicorn

from mongoengine import connect, Document, EmbeddedDocument, signals
from mongoengine.fields import (
    StringField, DecimalField, IntField, ListField, 
    EmbeddedDocumentField, EmbeddedDocumentListField,
    DateTimeField, BooleanField, URLField, DictField,
    ReferenceField, EmailField, ObjectIdField
)
from datetime import datetime, timedelta
import mongoengine.errors
from bson import ObjectId

from werkzeug.security import generate_password_hash, check_password_hash


# --------------------------
# FastAPI connection
# --------------------------
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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
    sku = StringField(required=True, max_length=100, unique=True)
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
            'sku',
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
            'created_at'
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
    user_type = StringField(max_length=200, default='user')
    is_active = BooleanField(default=True)
    is_verified = BooleanField(default=False)
    last_login = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    @staticmethod
    def pre_delete(sender, document, **kwargs):
        from mongoengine.queryset.visitor import Q
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


# --------------------------
# Authentication Classes
# --------------------------

class AdminAuth:
    @staticmethod
    def login(username: str, password: str) -> bool:
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        existing_user = User.objects(username=username).first()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not check_password_hash(existing_user.password_hash, password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Check if user has admin privileges
        if existing_user.user_type != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges"
            )
        
        return True
    
    @staticmethod
    def create_session(user_id: str) -> str:
        """Create admin session"""
        user_data = {
            "user_type": "admin"
        }
        return SessionManager.create_session(user_id, 'admin', user_data)


class UserAuth:
    @staticmethod
    def verify_credentials(username: str, password: str) -> User:
        """Verify user credentials and return user object if valid"""
        user = User.objects(username=username).first()
        if not user:
            user = User.objects(email=username).first()
        
        if not user:
            return None

        if not check_password_hash(user.password_hash, password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def create_session(user_id: str) -> str:
        """Create user session"""
        user_data = {
            "user_type": "user"
        }
        return SessionManager.create_session(user_id, 'user', user_data)



# --------------------------
# Connect signals for automatic session clean-up
# --------------------------
signals.pre_delete.connect(User.pre_delete, sender=User)


# --------------------------
# Admin Models & Forms
# --------------------------

class AdminModelConfig:
    def __init__(self, model: Type[Document], list_display: List[str] = None, search_fields: List[str] = None, list_filter: List[str] = None):
        self.model = model
        self.list_display = list_display or ["id", "name"] if hasattr(model, "name") else ["id"]
        self.search_fields = search_fields or []
        self.list_filter = list_filter or []

# Admin configurations for each model
ADMIN_MODELS = {
    'products': AdminModelConfig(
        Product,
        list_display=['name', 'sku', 'price', 'stock_quantity', 'is_active', 'created_at'],
        search_fields=['name', 'sku', 'description'],
        list_filter=['category', 'brand', 'is_active']
    ),
    'categories': AdminModelConfig(
        Category,
        list_display=['name', 'slug', 'is_active', 'display_order', 'created_at'],
        search_fields=['name', 'description'],
        list_filter=['is_active', 'parent_category']
    ),
    'users': AdminModelConfig(
        User,
        list_display=['username', 'email', 'first_name', 'last_name', 'is_active', 'created_at'],
        search_fields=['username', 'email', 'first_name', 'last_name'],
        list_filter=['is_active', 'is_verified']
    ),
    'orders': AdminModelConfig(
        Order,
        list_display=['order_number', 'email', 'total_amount', 'status', 'created_at'],
        search_fields=['order_number', 'email'],
        list_filter=['status', 'payment_status', 'shipping_status']
    )
}


# --------------------------
# Routes
# --------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    featured_products = Product.objects(is_featured=True, is_active=True)
    category_list = Category.objects(parent_category=None, is_active=True)

    category_products = {}
    for category in category_list:
        subcategories = Category.objects(parent_category=category, is_active=True)
        category_ids = [category.id] + [sub.id for sub in subcategories]

        products = Product.objects(category__in=category_ids, is_active=True).order_by("-created_at")[:6]
        category_products[category.slug] = products

    context = {
        "featured_products": featured_products,
        "category_list": category_list,
        "category_products": category_products
    }
    return templates.TemplateResponse(request, "dashboard.html", context)


# --------------------------
# Admin Routes
# --------------------------

@app.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})

@app.post("/admin")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        if AdminAuth.login(username, password):
            user = User.objects(username=username).first()
            session_id = AdminAuth.create_session(str(user.id))
            
            response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="admin_session", value=session_id, httponly=True)
            return response
    except HTTPException as e:
        return templates.TemplateResponse("admin/login.html", {
            "request": request, 
            "error": e.detail
        })
    
    return templates.TemplateResponse("admin/login.html", {
        "request": request, 
        "error": "Invalid credentials"
    })

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    # Get counts for dashboard
    product_count = Product.objects.count()
    category_count = Category.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "product_count": product_count,
        "category_count": category_count,
        "user_count": user_count,
        "order_count": order_count,
        "models": ADMIN_MODELS
    })

@app.get("/admin/{model_name}", response_class=HTMLResponse)
async def admin_model_list(
    request: Request, 
    model_name: str,
    page: int = 1,
    search: str = None,
    filter_field: str = None,
    filter_value: str = None
):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    if model_name not in ADMIN_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = ADMIN_MODELS[model_name]
    model = config.model

    # Build query
    query = {}
    
    # Search
    if search and config.search_fields:
        or_queries = []
        for field in config.search_fields:
            or_queries.append({f"{field}__icontains": search})
        if or_queries:
            query["$or"] = or_queries
    
    # Filter
    if filter_field and filter_value:
        query[filter_field] = filter_value
    
    # Pagination
    per_page = 20
    skip = (page - 1) * per_page
    
    objects = model.objects(**query).skip(skip).limit(per_page)
    total_count = model.objects(**query).count()
    total_pages = (total_count + per_page - 1) // per_page
    
    return templates.TemplateResponse("admin/model_list.html", {
        "request": request,
        "model_name": model_name,
        "model_config": config,
        "objects": objects,
        "page": page,
        "total_pages": total_pages,
        "search": search,
        "filter_field": filter_field,
        "filter_value": filter_value
    })

@app.get("/admin/{model_name}/add", response_class=HTMLResponse)
async def admin_model_add(request: Request, model_name: str):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    if model_name not in ADMIN_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = ADMIN_MODELS[model_name]
    
    # Get related objects for foreign keys
    context = {"request": request, "model_name": model_name, "model_config": config}
    
    if model_name == "products":
        context["categories"] = Category.objects.all()
    elif model_name == "categories":
        context["parent_categories"] = Category.objects.all()
    elif model_name == "orders":
        context["users"] = User.objects.all()
    elif model_name == "users":
        pass
    
    return templates.TemplateResponse("admin/model_form.html", context)

@app.post("/admin/{model_name}/add")
async def admin_model_create(request: Request, model_name: str):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    if model_name not in ADMIN_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = ADMIN_MODELS[model_name]
    form_data = await request.form()
    try:
        # Create object from form data
        obj_data = {}
        for field_name in form_data:
            if field_name not in ['csrf_token']:  # Skip CSRF if you add it
                value = form_data[field_name]
                
                # Handle different field types
                field = getattr(config.model, field_name, None)
                if field and isinstance(field, (ReferenceField, ObjectIdField)):
                    if value:
                        if field_name == "category" and model_name == "products":
                            obj_data[field_name] = Category.objects.get(id=value)
                        elif field_name == "user" and model_name == "orders":
                            obj_data[field_name] = User.objects.get(id=value)
                elif field and isinstance(field, (DecimalField, IntField)):
                    obj_data[field_name] = float(value) if value else 0
                elif field and isinstance(field, BooleanField):
                    obj_data[field_name] = bool(value)
                else:
                    obj_data[field_name] = value
        
        # Create the object
        obj = config.model(**obj_data)
        obj.save()
        
        return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        return templates.TemplateResponse("admin/model_form.html", {
            "request": request,
            "model_name": model_name,
            "model_config": config,
            "error": str(e),
            "form_data": dict(form_data)
        })

@app.get("/admin/{model_name}/{obj_id}", response_class=HTMLResponse)
async def admin_model_edit(request: Request, model_name: str, obj_id: str):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    if model_name not in ADMIN_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = ADMIN_MODELS[model_name]
    
    try:
        obj = config.model.objects.get(id=obj_id)
    except config.model.DoesNotExist:
        raise HTTPException(status_code=404, detail="Object not found")
    
    context = {
        "request": request, 
        "model_name": model_name, 
        "model_config": config,
        "object": obj
    }
    
    # Get related objects for foreign keys
    if model_name == "products":
        context["categories"] = Category.objects.all()
    elif model_name == "categories":
        context["parent_categories"] = Category.objects.all()
    elif model_name == "orders":
        context["users"] = User.objects.all()
    
    return templates.TemplateResponse("admin/model_form.html", context)

@app.post("/admin/{model_name}/{obj_id}")
async def admin_model_update(request: Request, model_name: str, obj_id: str):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    if model_name not in ADMIN_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = ADMIN_MODELS[model_name]
    form_data = await request.form()
    
    try:
        obj = config.model.objects.get(id=obj_id)
        
        # Update object from form data
        for field_name in form_data:
            if field_name not in ['csrf_token'] and hasattr(obj, field_name):
                value = form_data[field_name]
                
                # Handle different field types
                field = getattr(config.model, field_name, None)
                if field and isinstance(field, (ReferenceField, ObjectIdField)):
                    if value:
                        if field_name == "category" and model_name == "products":
                            setattr(obj, field_name, Category.objects.get(id=value))
                        elif field_name == "user" and model_name == "orders":
                            setattr(obj, field_name, User.objects.get(id=value))
                elif field and isinstance(field, (DecimalField, IntField)):
                    setattr(obj, field_name, float(value) if value else 0)
                elif field and isinstance(field, BooleanField):
                    setattr(obj, field_name, bool(value))
                else:
                    setattr(obj, field_name, value)
        
        obj.save()
        
        return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        return templates.TemplateResponse("admin/model_form.html", {
            "request": request,
            "model_name": model_name,
            "model_config": config,
            "object": obj,
            "error": str(e)
        })

@app.post("/admin/{model_name}/{obj_id}/delete")
async def admin_model_delete(request: Request, model_name: str, obj_id: str):
    session_id = request.cookies.get("admin_session")
    if not SessionManager.verify_session(session_id, 'admin'):
        return RedirectResponse(url="/admin")
    
    if model_name not in ADMIN_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = ADMIN_MODELS[model_name]
    
    try:
        obj = config.model.objects.get(id=obj_id)
        obj.delete()
        return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_302_FOUND)
    except config.model.DoesNotExist:
        raise HTTPException(status_code=404, detail="Object not found")

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin")
    response.delete_cookie(key="admin_session")
    return response


# --------------------------
# User Authentication Routes
# --------------------------

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("auth/signup.html", {"request": request})

@app.post("/signup")
async def signup_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(None),
    last_name: str = Form(None)
):
    # Validation
    errors = []
    
    # Password validation
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    # Truncate password if longer than 72 characters
    if len(password) > 72:
        password = password[:72]
    
    # Username validation
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    if len(username) > 50:
        errors.append("Username must be 50 characters or less")
    
    # Email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        errors.append("Please enter a valid email address")
    
    # Check if user already exists (only if no errors so far)
    if not errors:
        if User.objects(username=username):
            errors.append("Username already exists")
        
        if User.objects(email=email):
            errors.append("Email already exists")
    
    # Return errors if any
    if errors:
        return templates.TemplateResponse("auth/signup.html", {
            "request": request,
            "error": errors[0],
            "form_data": {
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        })
    
    try:
        # Create new user
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        user.save()
        
        # Create session
        session_id = UserAuth.create_session(str(user.id))
        
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="user_session", value=session_id, httponly=True)
        return response
        
    except Exception as e:
        return templates.TemplateResponse("auth/signup.html", {
            "request": request,
            "error": f"Error creating account: {str(e)}",
            "form_data": {
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            }
        })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.post("/login")
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        user = UserAuth.verify_credentials(username, password)
        if not user:
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "error": "Invalid username or password"
            })
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.save()
        
        # Create session
        session_id = UserAuth.create_session(str(user.id))
        
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="user_session", value=session_id, httponly=True)
        return response
        
    except Exception as e:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": f"Login error: {str(e)}"
        })

@app.get("/logout")
async def logout_user(request: Request):
    session_id = request.cookies.get("user_session")
    if session_id:
        SessionManager.delete_session(session_id)
    
    response = RedirectResponse(url="/")
    response.delete_cookie(key="user_session")
    return response

@app.get("/admin/logout")
async def admin_logout(request: Request):
    session_id = request.cookies.get("admin_session")
    if session_id:
        SessionManager.delete_session(session_id)
    
    response = RedirectResponse(url="/admin")
    response.delete_cookie(key="admin_session")
    return response

# Dependency to get current user
def get_current_user(request: Request):
    session_id = request.cookies.get("user_session")
    if session_id and SessionManager.verify_session(session_id, 'user'):
        session_data = SessionManager.get_session_data(session_id)
        if session_data and session_data.get('user_id'):
            user = User.objects.get(id=session_data['user_id'])
            return user
    return None

@app.get("/profile", response_class=HTMLResponse)
async def user_profile(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse("auth/profile.html", {
        "request": request,
        "user": current_user
    })


# --------------------------
# Background Tasks (Optional)
# --------------------------

@app.on_event("startup")
async def startup_event():
    """Clean up expired sessions on startup"""
    SessionManager.cleanup_expired_sessions()

app.extra['models'] = ADMIN_MODELS

if __name__ == "__main__":
    uvicorn.run("app:app", port=5000, host='127.0.0.1', reload=True)
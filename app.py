from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Type
import uvicorn

from mongoengine import connect, Document, signals
from mongoengine.fields import (
    DecimalField, IntField, ListField, 
    BooleanField, ReferenceField, ObjectIdField
)
from mongoengine.queryset.visitor import Q
from datetime import datetime
from bson import ObjectId

from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import asynccontextmanager
from models import Category, Order, Product, Session, SessionManager, User
from routers.product import product_router


# --------------------------
# Background Tasks (Optional)
# --------------------------

@asynccontextmanager
async def life_span(app: FastAPI):
    """Clean up expired sessions on startup"""
    SessionManager.cleanup_expired_sessions()
    yield


# --------------------------
# FastAPI connection
# --------------------------
app = FastAPI(lifespan=life_span)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


app.include_router(product_router)

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
        
        # Check if user has admin privileges using is_admin field
        if not existing_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges - Admin access required"
            )
        
        return True
    
    @staticmethod
    def create_session(user_id: str) -> str:
        """Create admin session"""
        user_data = {
            "is_admin": True
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
            "is_admin": False
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
        self.list_display = list_display or []
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
        list_display=['username', 'email', 'first_name', 'last_name', 'is_active', 'is_verified', 'is_admin', 'is_staff', 'created_at', 'last_login'],
        search_fields=['username', 'email', 'first_name', 'last_name'],
        list_filter=['is_active', 'is_verified', 'is_admin', 'is_staff']
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
            user.last_login = datetime.utcnow()
            user.save()
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


@app.get("/admin/logout")
async def admin_logout(request: Request):
    session_id = request.cookies.get("admin_session")
    if session_id:
        SessionManager.delete_session(session_id)
    
    response = RedirectResponse(url="/admin")
    response.delete_cookie(key="admin_session")
    return response


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
    query = Q()
    
    # Search
    if search and config.search_fields:
        or_queries = Q()
        for field in config.search_fields:
            or_queries |= Q(**({f"{field}__icontains": search}))
        query &= or_queries
    
    # Filter
    if filter_field and filter_value:
        query &= Q(**{filter_field: filter_value})
    
    # Pagination
    per_page = 20
    skip = (page - 1) * per_page
    
    if query:
        objects = model.objects(query).skip(skip).limit(per_page)
        total_count = model.objects(query).count()
    else:
        objects = model.objects.skip(skip).limit(per_page)
        total_count = model.objects.count()
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
        obj_data = {}
        for field_name in form_data:
            if field_name not in ['csrf_token']:
                value = form_data[field_name]
                
                field = getattr(config.model, field_name, None)
                
                if model_name == 'users' and field_name == 'password' and value:
                    hashed_password = generate_password_hash(value)
                    obj_data['password_hash'] = hashed_password
                    continue
                
                if model_name == 'users' and field_name == 'user_type':
                    continue 
                
                if field and isinstance(field, BooleanField):
                    boolean_value = value.lower() == 'true' if value else False
                    obj_data[field_name] = boolean_value
                    continue
                
                if field and isinstance(field, ListField):
                    if value:
                        if field_name == 'tags':
                            obj_data[field_name] = [tag.strip() for tag in value.split(',') if tag.strip()]
                        else:
                            obj_data[field_name] = value.split(',') if value else []
                    else:
                        obj_data[field_name] = []
                
                elif field and isinstance(field, (ReferenceField, ObjectIdField)):
                    if value:
                        if field_name == "category" and model_name == "products":
                            obj_data[field_name] = Category.objects.get(id=value)
                        elif field_name == "user" and model_name == "orders":
                            obj_data[field_name] = User.objects.get(id=value)
                        elif field_name == "parent_category" and model_name == "categories":
                            obj_data[field_name] = Category.objects.get(id=value)
                
                elif field and isinstance(field, (DecimalField, IntField)):
                    obj_data[field_name] = float(value) if value else 0
                
                else:
                    obj_data[field_name] = value
        
        if model_name == 'users':
            if 'is_active' not in obj_data:
                obj_data['is_active'] = True
            if 'is_admin' not in obj_data:
                obj_data['is_admin'] = False
            if 'is_staff' not in obj_data:
                obj_data['is_staff'] = False
        
        if model_name == 'products':
            if 'manage_stock' not in obj_data:
                obj_data['manage_stock'] = True
            if 'allow_backorders' not in obj_data:
                obj_data['allow_backorders'] = False
            if 'has_variants' not in obj_data:
                obj_data['has_variants'] = False
            if 'is_active' not in obj_data:
                obj_data['is_active'] = True
            if 'is_featured' not in obj_data:
                obj_data['is_featured'] = False
            if 'is_digital' not in obj_data:
                obj_data['is_digital'] = False
        
        obj = config.model(**obj_data)
        obj.save()
        
        return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        # Get related objects for context in case of error
        context = {
            "request": request,
            "model_name": model_name,
            "model_config": config,
            "error": str(e),
            "form_data": dict(form_data)
        }
        
        if model_name == "products":
            context["categories"] = Category.objects.all()
        elif model_name == "categories":
            context["parent_categories"] = Category.objects.all()
        elif model_name == "orders":
            context["users"] = User.objects.all()
        
        return templates.TemplateResponse("admin/model_form.html", context)

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
    data_dict = form_data._dict
    try:
        obj = config.model.objects.get(id=obj_id)
        for field_name in form_data:
            if field_name not in ['csrf_token'] and hasattr(obj, field_name):
                value = form_data[field_name]
                if model_name == 'users' and data_dict['password']:
                    hashed_password = generate_password_hash(data_dict['password'])
                    obj.password_hash = hashed_password
                    obj.save()
                    continue
                
                field = getattr(config.model, field_name, None)
                
                if field and isinstance(field, BooleanField):
                    boolean_value = value.lower() == 'true' if value else False
                    
                    setattr(obj, field_name, boolean_value)
                    session_user = Session.objects(user_id=obj_id).first()
                    
                    if session_user is None:
                        RedirectResponse(url=f"/admin/{model_name}/{obj_id}", status_code=status.HTTP_404_NOT_FOUND)
                    print(session_user)
                    if field_name == 'is_admin' and boolean_value == True:
                        session_user['session_type'], session_user['user_data']['is_admin'] = 'admin', True
                        session_user.save()
                    if field_name == 'is_admin' and boolean_value == False:
                        session_user['session_type'], session_user['user_data']['is_admin'] = 'user', False
                        session_user.save()
                    continue
                
                if field and isinstance(field, ListField):
                    if value:
                        if field_name == 'tags':
                            setattr(obj, field_name, [tag.strip() for tag in value.split(',') if tag.strip()])
                        else:
                            setattr(obj, field_name, value.split(',') if value else [])
                    else:
                        setattr(obj, field_name, [])
                
                elif field and isinstance(field, (ReferenceField, ObjectIdField)):
                    if value:
                        if field_name == "category" and model_name == "products":
                            setattr(obj, field_name, Category.objects.get(id=value))
                        elif field_name == "user" and model_name == "orders":
                            setattr(obj, field_name, User.objects.get(id=value))
                        elif field_name == "parent_category" and model_name == "categories":
                            setattr(obj, field_name, Category.objects.get(id=value))
                    else:
                        setattr(obj, field_name, None)
                
                elif field and isinstance(field, (DecimalField, IntField)):
                    setattr(obj, field_name, float(value) if value else 0)                
                else:
                    setattr(obj, field_name, value)
        obj.save()
        
        return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_302_FOUND)
    
    except Exception as e:
        context = {
            "request": request,
            "model_name": model_name,
            "model_config": config,
            "object": obj,
            "error": str(e)
        }
        # Add related objects for foreign keys in error case
        if model_name == "products":
            context["categories"] = Category.objects.all()
        elif model_name == "categories":
            context["parent_categories"] = Category.objects.all()
        elif model_name == "orders":
            context["users"] = User.objects.all()
        
        return templates.TemplateResponse("admin/model_form.html", context)    


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
    errors = []
    
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    if len(password) > 72:
        password = password[:72]
    
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    if len(username) > 50:
        errors.append("Username must be 50 characters or less")
    
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        errors.append("Please enter a valid email address")
    
    if not errors:
        if User.objects(username=username):
            errors.append("Username already exists")
        
        if User.objects(email=email):
            errors.append("Email already exists")
    
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
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_admin=False,
            is_staff=False
        )
        user.save()
        
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


app.extra['models'] = ADMIN_MODELS

if __name__ == "__main__":
    uvicorn.run("app:app", port=7000, host='127.0.0.1', reload=True)
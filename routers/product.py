from typing import Optional
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mongoengine.queryset.visitor import Q

from models import Category


product_router = APIRouter(prefix="/products")
templates = Jinja2Templates(directory="templates")


@product_router.get("/", response_class=HTMLResponse)
def products_home(request:Request, category: Optional[str]= None):
    query = Q(is_active=True)
    if category:
        category_obj = Category.objects(slug=category, is_active=True).first()
        if category_obj:
            subcategories = Category.objects(parent_category=category_obj, is_active=True)
            category_ids = [category_obj.id] + [sub.id for sub in subcategories]
            query &= Q(category_in=category_ids)
        else:
            query &= Q(category__in=[])
    context = {
        "request": request,
        "current_category": category
    }
    return templates.TemplateResponse("products/products.html", context)
import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
load_dotenv()

from db.database import get_db

from models.db_models import get_shop_by_api_key, Shop

from models.shopify_api import(
    OrderCountUrlParams, 
    OrderUrlParams,
    CustomerCountUrlParams,
    CustomerSearchUrlParams,
)
from models.api import (
    CountResponse,
    CustomersResponse,
    CustomerResponse,
    OrdersResponse,
    OrderResponse,
)

from services.shopify import (
    get_shop_order,
    get_shop_orders,
    get_shop_orders_count,
    get_shop_customer,
    get_shop_customers,
    get_shop_customers_count,
    DEFAULT_CUSTOMER_FIELDS,
    DEFAULT_ORDER_FIELDS,
)

PORT = int(os.getenv("PORT", 8000))
DOMAIN = os.getenv("DOMAIN")
ENVIRONMENT = os.getenv("ENVIRONMENT")
if ENVIRONMENT != "production":
    DOMAIN = f"{DOMAIN}:{PORT}"

origins = [
    DOMAIN,
    "https://chat.openai.com",
]

bearer_scheme = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials.scheme != "Bearer" or credentials.credentials is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials


def get_current_shop(db, api_key) -> Shop:
    shop = get_shop_by_api_key(db, api_key)
    if shop is None:
        raise HTTPException(status_code=404, detail="Shop not found, check API key")
    
    return shop


app = FastAPI(
    title="Shopify Store Admin Plugin API",
    description="An API for querying and looking up information about a Shopify store's orders and customers.",
    version="1.0.0",
    servers=[{"url": DOMAIN}]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")


@app.get(
    "/orders", 
    response_model=OrdersResponse,
    response_model_exclude_unset=True
)
async def get_orders(
    attribution_app_id: str | None = None,
    created_at_max: datetime | None = None,
    created_at_min: datetime | None = None,
    fields: str | None = DEFAULT_ORDER_FIELDS,
    financial_status: str = "any",
    fulfillment_status: str = "any",
    ids: str | None = None,
    limit: int = 10,
    processed_at_max: datetime | None = None,
    processed_at_min: datetime | None = None,
    since_id: int | None = None,
    status: str = "open",
    updated_at_max: datetime | None = None,
    updated_at_min: datetime | None = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(validate_token)
):
    shop = get_current_shop(db, credentials.credentials)
    try:
        orders = get_shop_orders(shop.shopify_token, shop.shopify_domain, OrderUrlParams(
            attribution_app_id=attribution_app_id,
            created_at_max=created_at_max,
            created_at_min=created_at_min,
            fields=fields,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            ids=ids,
            limit=limit,
            processed_at_max=processed_at_max,
            processed_at_min=processed_at_min,
            since_id=since_id,
            status=status,
            updated_at_max=updated_at_max,
            updated_at_min=updated_at_min,
        ))
        return orders
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


@app.get(
    "/orders/count", 
    response_model=CountResponse,
    response_model_exclude_unset=True
)
async def get_orders_count(    
    created_at_max: datetime | None = None,
    created_at_min: datetime | None = None,
    financial_status: str | None = "any",
    fulfillment_status: str | None = "any",
    status: str | None = "open",
    updated_at_max: datetime | None = None,
    updated_at_min: datetime | None = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(validate_token)
):
    shop = get_current_shop(db, credentials.credentials)
    try:
        orders_count = get_shop_orders_count(shop.shopify_token, shop.shopify_domain, OrderCountUrlParams(
            created_at_max=created_at_max,
            created_at_min=created_at_min,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            status=status,
            updated_at_max=updated_at_max,
            updated_at_min=updated_at_min,
        ))
        return orders_count
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


@app.get(
    "/orders/{order_id}", 
    response_model=OrderResponse,
    response_model_exclude_unset=True
)
async def get_order(
    order_id: int, 
    fields: str | None = DEFAULT_ORDER_FIELDS, 
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(validate_token)
):
    shop = get_current_shop(db, credentials.credentials)
    try:
        order = get_shop_order(shop.shopify_token, shop.shopify_domain, order_id, fields=fields)
        return order
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


@app.get(
    "/customers/count", 
    response_model=CountResponse
)
async def get_customers_count(
    created_at_max: datetime | None = None,
    created_at_min: datetime | None = None,
    updated_at_max: datetime | None = None,
    updated_at_min: datetime | None = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(validate_token)
):
    shop = get_current_shop(db, credentials.credentials)
    try:
        customers_count = get_shop_customers_count(shop.shopify_token, shop.shopify_domain, CustomerCountUrlParams(
            created_at_max=created_at_max,
            created_at_min=created_at_min,
            updated_at_max=updated_at_max,
            updated_at_min=updated_at_min,
        ))

        return customers_count
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


@app.get(
    "/customers/search", 
    response_model=CustomersResponse,
    response_model_exclude_unset=True
)
async def search_customers(
    fields: str | None = DEFAULT_CUSTOMER_FIELDS,
    limit: int = 10,
    order_field: str = "last_order_date",
    order_direction: str = "DESC",
    query: str = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(validate_token)
):
    shop = get_current_shop(db, credentials.credentials)
    try:
        customers = get_shop_customers(shop.shopify_token, shop.shopify_domain, CustomerSearchUrlParams(
            fields=fields,
            limit=limit,
            order_field=order_field,
            order_direction=order_direction,
            query=query,
        ))

        return customers
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


@app.get(
    "/customers/{customer_id}", 
    response_model=CustomerResponse,
    response_model_exclude_unset=True
)
async def get_customer(
    customer_id: int, 
    fields: str | None = DEFAULT_CUSTOMER_FIELDS, 
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(validate_token)
):
    shop = get_current_shop(db, credentials.credentials)
    try:
        customer = get_shop_customer(shop.shopify_token, shop.shopify_domain, customer_id, fields)
        return customer
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


def start():
    uvicorn.run("server.main:app", host="0.0.0.0", port=PORT, reload=True)
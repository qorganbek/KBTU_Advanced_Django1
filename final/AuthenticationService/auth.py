import datetime
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from exceptions import AuthTokenMissing
from models import Customer, Courier, Restaurant
from config import SECRET_KEY
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from schemas import CreateCustomerRequest, Token, CreateCourierRequest, CreateRestaurantRequest
import database as db

router = APIRouter(
    prefix="/auth",
    tags=['auth']
)

SECRET_KEY = SECRET_KEY
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_bearer_customer = OAuth2PasswordBearer(tokenUrl='auth/login')
oauth2_bearer_restaurant = OAuth2PasswordBearer(tokenUrl='auth/login_restaurant')
oauth2_bearer_courier = OAuth2PasswordBearer(tokenUrl='auth/login_courier')


def get_db():
    try:
        ss = db.session
        yield ss
        ss.commit()
    except Exception:
        raise
    finally:
        ss.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_customer(dp: db_dependency, customer_request: CreateCustomerRequest) -> dict:
    try:
        customer = Customer(
            email=customer_request.email,
            phone_number=customer_request.phone_number,
            address=customer_request.address,
            hashed_password=bcrypt_context.hash(customer_request.hashed_password.get_secret_value()),
        )
        dp.add(customer)
        return {"message": "user successfully created!"}
    except Exception as e:
        dp.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register_restaurant", status_code=status.HTTP_201_CREATED)
async def create_restaurant(dp: db_dependency, restaurant_request: CreateRestaurantRequest) -> dict:
    try:
        customer = Restaurant(
            email=restaurant_request.email,
            phone_number=restaurant_request.phone_number,
            address=restaurant_request.address,
            hashed_password=bcrypt_context.hash(restaurant_request.hashed_password.get_secret_value()),
            name=restaurant_request.name
        )
        dp.add(customer)
        return {"message": "restaurant successfully created!"}
    except Exception as e:
        dp.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register_courier", status_code=status.HTTP_201_CREATED)
async def create_courier(dp: db_dependency, courier_request: CreateCourierRequest) -> dict:
    try:
        courier = Courier(
            email=courier_request.email,
            phone_number=courier_request.phone_number,
            hashed_password=bcrypt_context.hash(courier_request.hashed_password.get_secret_value())
        )
        dp.add(courier)
        return {"message": "courier successfully created!"}
    except Exception as e:
        dp.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], dp: db_dependency):
    entity = authenticate_customer(form_data.username, form_data.password, dp)

    if not entity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(entity.email, str(entity.id), timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}


@router.post("/login_courier", response_model=Token)
async def login_as_courier(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], dp: db_dependency):
    entity = authenticate_courier(form_data.username, form_data.password, dp)

    if not entity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(entity.email, str(entity.id), timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}


@router.post("/login_restaurant", response_model=Token)
async def login_as_restaurant(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], dp: db_dependency):
    entity = authenticate_restaurant(form_data.username, form_data.password, dp)

    if not entity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(entity.email, str(entity.id), timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_customer(email: str, password: str, dp: db_dependency):
    customer = dp.query(Customer).filter(Customer.email == email).first()

    if not customer:
        return False

    if not bcrypt_context.verify(password, customer.hashed_password):
        return False

    return customer


def authenticate_courier(email: str, password: str, dp: db_dependency):
    courier = dp.query(Courier).filter(Courier.email == email).first()

    if not courier:
        return False

    if not bcrypt_context.verify(password, courier.hashed_password):
        return False

    return courier


def authenticate_restaurant(email: str, password: str, dp: db_dependency):
    restaurant = dp.query(Restaurant).filter(Restaurant.email == email).first()

    if not restaurant:
        return False

    if not bcrypt_context.verify(password, restaurant.hashed_password):
        return False

    return restaurant


def create_access_token(email: str, entity_id: str, expires_delta: timedelta):
    encode = {'sub': email, 'id': entity_id}
    expires = datetime.datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(authorization: str = None):
    if not authorization:
        raise AuthTokenMissing('Auth token is missing in headers.')
    token = authorization.replace('Bearer ', '')
    try:
        payload = jwt.decode(token, SECRET_KEY, [ALGORITHM])
        return payload
    except Exception as e:
        raise e


async def get_current_entity(token: Annotated[str, Depends(oauth2_bearer_customer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        entity_id: str = payload.get("id")
        if email is None or entity_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return {"email": email, 'id': entity_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")


async def get_current_restaurant(token: Annotated[str, Depends(oauth2_bearer_restaurant)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        entity_id: str = payload.get("id")
        if email is None or entity_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return {"email": email, 'id': entity_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")


async def get_current_courier(token: Annotated[str, Depends(oauth2_bearer_courier)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        entity_id: str = payload.get("id")
        if email is None or entity_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return {"email": email, 'id': entity_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")


def is_default_user(token_payload):
    return len(token_payload.get('sub')) > 0


def generate_request_header(token_payload):
    return {'request-user-id': str(token_payload['id'])}

import datetime
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from models import Customer
from config import SECRET_KEY
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from schemas import CreateCustomerRequest, Token
import database as db

router = APIRouter(
    prefix="/auth",
    tags=['auth']
)

SECRET_KEY = SECRET_KEY
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


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


@router.post("/", status_code=status.HTTP_201_CREATED)
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


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], dp: db_dependency):
    entity = authenticate_customer(form_data.username, form_data.password, dp)

    if not entity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(entity.email, entity.id, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_customer(email: str, password: str, dp: db_dependency):
    entity = dp.query(Customer).filter(Customer.email == email).first()

    if not entity:
        return False
    if not bcrypt_context.verify(password, entity.hashed_password):
        return False

    return entity


def create_access_token(email: str, entity_id: str, expires_delta: timedelta):
    encode = {'sub': email, 'id': entity_id}
    expires = datetime.datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_entity(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        entity_id: str = payload.get("id")
        if email is None or entity_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return {"email": email, 'id': entity_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

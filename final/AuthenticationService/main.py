from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from fastapi import FastAPI, Depends, HTTPException
import auth
import database as db
from models import Base
from database import engine

Base.metadata.create_all(engine)

app = FastAPI()

app.include_router(auth.router)


def get_db():
    try:
        session = db.session
        yield session
        session.commit()
    except Exception:
        raise
    finally:
        session.close()


entity_dependency = Annotated[dict, Depends(auth.get_current_entity)]
db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/health_check", tags=['check'])
async def health_check() -> dict:
    return {"message": "I'm alive"}


@app.get("/", status_code=status.HTTP_200_OK, tags=['check'])
async def entity(entity: entity_dependency, db: db_dependency):
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Authentication failed!')
    return entity

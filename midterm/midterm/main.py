import http
import models as db
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from database import session
from schemas import CreateUser, User

app = FastAPI()


def get_db():
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.post("/users", response_model=dict)
def add_user(user: CreateUser, session: Session = Depends(get_db)) -> dict:
    try:
        new_user = db.User(**user.model_dump())
        session.add(new_user)
        return {"message": "User added successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users", response_model=list[User])
def get_users(session: Session = Depends(get_db)):
    try:
        users = session.execute(select(db.User)).scalars().all()
        user_response = [User.validate(user) for user in users]
        return user_response
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=User)
def get_user_by_id(user_id: str, session: Session = Depends(get_db)):
    try:
        user = session.query(db.User).filter(db.User.id == user_id).first()
        if user.id:
            return User.model_validate(user)
        else:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail={"message": "User not found"})
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: str, session: Session = Depends(get_db)):
    try:
        deleted_count = session.execute(delete(db.User).where(db.User.id == user_id)).rowcount
        if deleted_count == 0:
            raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

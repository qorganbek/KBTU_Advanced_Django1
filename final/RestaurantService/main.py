from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from restaurant import router
import database as db

app = FastAPI()

app.include_router(router)


def get_db():
    try:
        session = db.session
        yield session
        session.commit()
    except Exception:
        raise
    finally:
        session.commit()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/health_check", tags=['check'])
async def health_check() -> dict:
    return {'message': "I'm alive"}


# TODO change order status deny, accepted, ready +
# TODO order detail restaurant orders +
# TODO orders by status look like history +

@app.get("/orders/{order_id}/{restaurant_id}", tags=['orders'])
async def order_detail(db: db_dependency, order_id: str, restaurant_id: str):
    try:
        orders = db.execute(select(models.Order).filter(models.Order.restaurant_id == restaurant_id).
                            filter(models.Order.id == order_id)).scalars().all()
        return orders[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{e}')


@app.get("/orders/{restaurant_id}", tags=['orders'])
async def history_orders(db: db_dependency, restaurant_id: str,
                         status_req: str = Query('DENY',
                                                 enum=['PENDING', 'DENY', 'PAID', 'ACCEPTED', 'READY', 'IN-TRANSIT',
                                                       'DELIVERED'])):
    try:
        orders = db.execute(select(models.Order).filter(models.Order.restaurant_id == restaurant_id)).scalars().all()
        res = [x for x in orders if x.status == status_req]
        if not res:
            return {'message': 'orders not found!'}
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{e}')


@app.patch("/orders/{order_id}/{restaurant_id}", tags=['orders'])
async def change_status(db: db_dependency, order_id: str, restaurant_id: str,
                        status: str = Query('DENY', enum=['ACCEPTED', 'DENY', 'READY'])):
    try:
        orders = db.execute(select(models.Order).filter(models.Order.restaurant_id == restaurant_id).
                            filter(models.Order.id == order_id)).scalars().all()
        if not orders:
            return {'message': 'order not found!'}
        orders[0].status = status
        return {'message': 'status is changed!'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{e}')

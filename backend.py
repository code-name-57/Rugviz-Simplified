#!/usr/bin/env python3
from fastapi import FastAPI
from models import Hero
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlmodel import Field, Session, SQLModel, create_engine

from fastapi import FastAPI
from models import Hero, RVBackground

app = FastAPI()
engine = create_engine("sqlite:///database.db", echo=True)
SQLModel.metadata.create_all(engine)

@app.get('/')
def read_root():
    return {'Hello': 'World'}

@app.get('/heroes/', response_model=list[Hero])
def list_heroes():
    with Session(engine) as session:
        heroes = session.exec(select(Hero)).all()
        return heroes
@app.post('/heroes/', response_model=Hero)
def create_hero(hero: Hero):
    with Session(engine) as session:
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return hero

@app.get('/heroes/{hero_id}', response_model=Hero)
def read_hero(hero_id: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        return hero

@app.put('/heroes/{hero_id}', response_model=Hero)
def update_hero(hero_id: int, hero: Hero):
    with Session(engine) as session:
        existing_hero = session.get(Hero, hero_id)
        if not existing_hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        hero.id = hero_id
        session.merge(hero)
        session.commit()
        session.refresh(hero)
        return hero

@app.delete('/heroes/{hero_id}')
def delete_hero(hero_id: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        session.delete(hero)
        session.commit()
        return {"ok": True}


@app.get('/backgrounds/', response_model=list[RVBackground])
def list_backgrounds():
    with Session(engine) as session:
        backgrounds = session.exec(select(RVBackground)).all()
        return backgrounds

@app.post('/backgrounds/', response_model=RVBackground)
def create_background(background: RVBackground):
    with Session(engine) as session:
        session.add(background)
        session.commit()
        session.refresh(background)
        return background

@app.get('/backgrounds/{background_id}', response_model=RVBackground)
def read_background(background_id: int):
    with Session(engine) as session:
        background = session.get(RVBackground, background_id)
        if not background:
            raise HTTPException(status_code=404, detail="RVBackground not found")
        return background

@app.put('/backgrounds/{background_id}', response_model=RVBackground)
def update_background(background_id: int, background: RVBackground):
    with Session(engine) as session:
        existing_background = session.get(RVBackground, background_id)
        if not existing_background:
            raise HTTPException(status_code=404, detail="RVBackground not found")
        background.id = background_id
        session.merge(background)
        session.commit()
        session.refresh(background)
        return background

@app.delete('/backgrounds/{background_id}')
def delete_background(background_id: int):
    with Session(engine) as session:
        background = session.get(RVBackground, background_id)
        if not background:
            raise HTTPException(status_code=404, detail="RVBackground not found")
        session.delete(background)
        session.commit()
        return {"ok": True}

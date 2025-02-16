#!/usr/bin/env python3
import frontend
from fastapi import FastAPI
from models import Hero
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlmodel import Field, Session, SQLModel, create_engine

from fastapi import FastAPI
from models import Hero

from backend import app
frontend.init(app)
engine = create_engine("sqlite:///database.db", echo=True)
SQLModel.metadata.create_all(engine)

if __name__ == '__main__':
    print('Please start the app with the "uvicorn" command as shown in the start.sh script')
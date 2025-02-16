from sqlmodel import Field, SQLModel
from typing import Optional

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None

class RVBackground(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    image_path: Optional[str] = Field(default=None)
    point1_x: Optional[int] = Field(default=None)
    point1_y: Optional[int] = Field(default=None)
    point2_x: Optional[int] = Field(default=None)
    point2_y: Optional[int] = Field(default=None)
    point3_x: Optional[int] = Field(default=None)
    point3_y: Optional[int] = Field(default=None)
    point4_x: Optional[int] = Field(default=None)
    point4_y: Optional[int] = Field(default=None)

# class RVRender(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     image_path: str
#     background: RVBackground

# class RVRug(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     image_path: str
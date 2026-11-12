"""SQLAlchemy 2.0 宣告式基底。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM model 的基底類別。"""

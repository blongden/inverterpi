from enum import unique
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class Register(Base):
    __tablename__ = "registers"

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)
    date_created = Column('date_created', DateTime(timezone=True), server_default=func.now())

    register_history = relationship("RegisterHistory", back_populates="register")

    def __repr__(self):
        return f"Register(id={self.id!r}, name={self.name!r}, date_created={self.date_created!r})"

class RegisterHistory(Base):
    __tablename__ = "register_history"

    history_id = Column(Integer, primary_key=True)
    state = Column('state', Integer)
    register_id = Column(Integer, ForeignKey('registers.id'))
    register = relationship("Register", back_populates="register_history")
    date = Column('date_created', DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"RegisterHistory(id={self.history_id!r}, name={self.state!r}, date_created={self.date!r}, register_id={self.register_id!r})"

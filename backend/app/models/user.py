from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    """
    SQLAlchemy ORM Model representing the 'users' table in MySQL.
    """
    __tablename__ = "users"

    # Primary key: Unique identifier for each user
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Full name of the user
    name = Column(String(100), nullable=False)

    # Email address: Must be unique across all accounts
    # Index allows fast lookup during login and registration checks
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Salted hash of the user's password (NEVER plaintext)
    hashed_password = Column(String(255), nullable=False)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to user's tasks
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

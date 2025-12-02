"""SQLAlchemy models for Resource and ResourceDependency"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship, declarative_base
from uuid import uuid4

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string for primary keys"""
    return str(uuid4())


def utc_now():
    """Generate timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


# Junction table for many-to-many resource dependencies
resource_dependencies = Table(
    'resource_dependencies',
    Base.metadata,
    Column('resource_id', String, ForeignKey('resources.id', ondelete='CASCADE'), primary_key=True),
    Column('depends_on_id', String, ForeignKey('resources.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_dependencies_resource', 'resource_id'),
    Index('idx_dependencies_depends_on', 'depends_on_id')
)


class Resource(Base):
    """Resource model representing a managed entity with dependencies"""
    __tablename__ = 'resources'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationship: resources this resource depends on
    dependencies = relationship(
        'Resource',
        secondary=resource_dependencies,
        primaryjoin=id == resource_dependencies.c.resource_id,
        secondaryjoin=id == resource_dependencies.c.depends_on_id,
        backref='dependents',
        lazy='selectin'
    )
    
    def __repr__(self):
        return f"<Resource(id={self.id}, name={self.name})>"

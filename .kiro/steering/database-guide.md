---
inclusion: manual
---

# Database Implementation Guide

## Overview

This project supports two database backends through the Repository Pattern:
- **SQLite** with SQLAlchemy (default, for development)
- **MongoDB** with Motor (for production)

## Adding Database Support for New Features

### Step-by-Step Process

When adding a new feature that requires database changes:

1. **Update Pydantic Schemas** (`app/schemas.py`)
2. **Update Repository Interface** (`app/repositories/base.py`)
3. **Update SQLAlchemy Model** (`app/models/`)
4. **Implement SQLAlchemy Repository** (`app/repositories/sqlalchemy_repository.py`)
5. **Implement MongoDB Repository** (`app/repositories/mongodb_repository.py`)
6. **Test Both Implementations**

### Example: Adding a "Tags" Field

#### 1. Update Schema

```python
# app/schemas.py
class ResourceCreate(BaseModel):
    name: str
    description: str | None
    dependencies: list[str] = []
    tags: list[str] = []  # New field
```

#### 2. Update Repository Interface

```python
# app/repositories/base.py
from abc import ABC, abstractmethod

class ResourceRepository(ABC):
    @abstractmethod
    async def get_by_tag(self, tag: str) -> list[ResourceResponse]:
        """Get all resources with a specific tag."""
        pass
```

#### 3. Update SQLAlchemy Model

```python
# app/models/resource.py
from sqlalchemy import Column, String, JSON

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    dependencies = Column(JSON, default=list)
    tags = Column(JSON, default=list)  # New field
```

#### 4. Implement SQLAlchemy Repository

```python
# app/repositories/sqlalchemy_repository.py
async def get_by_tag(self, tag: str) -> list[ResourceResponse]:
    """Get all resources with a specific tag."""
    async with self.session() as session:
        result = await session.execute(
            select(Resource).where(Resource.tags.contains([tag]))
        )
        resources = result.scalars().all()
        return [ResourceResponse.model_validate(r) for r in resources]
```

#### 5. Implement MongoDB Repository

```python
# app/repositories/mongodb_repository.py
async def get_by_tag(self, tag: str) -> list[ResourceResponse]:
    """Get all resources with a specific tag."""
    cursor = self.collection.find({"tags": tag})
    resources = await cursor.to_list(length=None)
    return [self._to_response(r) for r in resources]
```

## SQLite/SQLAlchemy Implementation

### Connection Management

```python
# app/database_sqlalchemy.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

### Model Definition

```python
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    dependencies = Column(JSON, default=list)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

### CRUD Operations

```python
# Create
async def create(self, data: ResourceCreate) -> ResourceResponse:
    async with self.session() as session:
        resource = Resource(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
            dependencies=data.dependencies,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return ResourceResponse.model_validate(resource)

# Read
async def get(self, resource_id: str) -> ResourceResponse:
    async with self.session() as session:
        result = await session.execute(
            select(Resource).where(Resource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError(resource_id)
        return ResourceResponse.model_validate(resource)

# Update
async def update(self, resource_id: str, data: ResourceUpdate) -> ResourceResponse:
    async with self.session() as session:
        result = await session.execute(
            select(Resource).where(Resource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError(resource_id)
        
        if data.name is not None:
            resource.name = data.name
        if data.description is not None:
            resource.description = data.description
        if data.dependencies is not None:
            resource.dependencies = data.dependencies
        
        resource.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(resource)
        return ResourceResponse.model_validate(resource)

# Delete
async def delete(self, resource_id: str) -> None:
    async with self.session() as session:
        result = await session.execute(
            select(Resource).where(Resource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        if not resource:
            raise NotFoundError(resource_id)
        
        await session.delete(resource)
        await session.commit()
```

## MongoDB Implementation

### Connection Management

```python
# app/database_mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(settings.database_url)
database = client[settings.mongodb_database]
```

### Collection Access

```python
class MongoDBResourceRepository(ResourceRepository):
    def __init__(self):
        self.collection = database["resources"]
```

### CRUD Operations

```python
# Create
async def create(self, data: ResourceCreate) -> ResourceResponse:
    resource_dict = {
        "_id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description,
        "dependencies": data.dependencies,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await self.collection.insert_one(resource_dict)
    return self._to_response(resource_dict)

# Read
async def get(self, resource_id: str) -> ResourceResponse:
    resource = await self.collection.find_one({"_id": resource_id})
    if not resource:
        raise NotFoundError(resource_id)
    return self._to_response(resource)

# Update
async def update(self, resource_id: str, data: ResourceUpdate) -> ResourceResponse:
    update_dict = {"updated_at": datetime.utcnow()}
    
    if data.name is not None:
        update_dict["name"] = data.name
    if data.description is not None:
        update_dict["description"] = data.description
    if data.dependencies is not None:
        update_dict["dependencies"] = data.dependencies
    
    result = await self.collection.find_one_and_update(
        {"_id": resource_id},
        {"$set": update_dict},
        return_document=True
    )
    
    if not result:
        raise NotFoundError(resource_id)
    
    return self._to_response(result)

# Delete
async def delete(self, resource_id: str) -> None:
    result = await self.collection.delete_one({"_id": resource_id})
    if result.deleted_count == 0:
        raise NotFoundError(resource_id)
```

### Helper Methods

```python
def _to_response(self, doc: dict) -> ResourceResponse:
    """Convert MongoDB document to ResourceResponse."""
    return ResourceResponse(
        id=doc["_id"],
        name=doc["name"],
        description=doc.get("description"),
        dependencies=doc.get("dependencies", []),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"]
    )
```

## Database Migrations

### SQLite Migrations

For schema changes in SQLite:

```python
# Create migration script
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('resources', sa.Column('tags', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('resources', 'tags')
```

### MongoDB Migrations

MongoDB is schema-less, but you may need data migrations:

```python
# scripts/migrate_add_tags.py
async def migrate():
    """Add empty tags array to existing resources."""
    await collection.update_many(
        {"tags": {"$exists": False}},
        {"$set": {"tags": []}}
    )
```

## Testing Database Implementations

### Test Both Backends

```python
import pytest

@pytest.mark.parametrize("db_type", ["sqlite", "mongodb"])
async def test_create_resource(db_type):
    """Test create operation on both databases."""
    repository = get_repository_for_type(db_type)
    
    data = ResourceCreate(name="Test", dependencies=[])
    result = await repository.create(data)
    
    assert result.name == "Test"
    assert result.id is not None
```

### Database-Specific Tests

```python
# Test SQLite-specific features
async def test_sqlite_json_query():
    """Test JSON column querying in SQLite."""
    pass

# Test MongoDB-specific features
async def test_mongodb_aggregation():
    """Test MongoDB aggregation pipeline."""
    pass
```

## Performance Considerations

### SQLite
- Use indexes on frequently queried columns
- Avoid large JSON columns
- Consider connection pooling
- Use PRAGMA statements for optimization

### MongoDB
- Create indexes on query fields
- Use projection to limit returned fields
- Leverage aggregation pipeline
- Monitor query performance with explain()

## Common Patterns

### Batch Operations

```python
# SQLite
async def create_many(self, resources: list[ResourceCreate]) -> list[ResourceResponse]:
    async with self.session() as session:
        db_resources = [Resource(**r.dict(), id=str(uuid.uuid4())) for r in resources]
        session.add_all(db_resources)
        await session.commit()
        return [ResourceResponse.model_validate(r) for r in db_resources]

# MongoDB
async def create_many(self, resources: list[ResourceCreate]) -> list[ResourceResponse]:
    docs = [
        {
            "_id": str(uuid.uuid4()),
            **r.dict(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        for r in resources
    ]
    await self.collection.insert_many(docs)
    return [self._to_response(doc) for doc in docs]
```

### Transactions

```python
# SQLite
async def transfer_dependencies(self, from_id: str, to_id: str):
    async with self.session() as session:
        async with session.begin():
            # Operations are atomic within this block
            from_resource = await session.get(Resource, from_id)
            to_resource = await session.get(Resource, to_id)
            to_resource.dependencies.extend(from_resource.dependencies)
            from_resource.dependencies = []

# MongoDB
async def transfer_dependencies(self, from_id: str, to_id: str):
    async with await client.start_session() as session:
        async with session.start_transaction():
            from_resource = await self.collection.find_one({"_id": from_id}, session=session)
            await self.collection.update_one(
                {"_id": to_id},
                {"$push": {"dependencies": {"$each": from_resource["dependencies"]}}},
                session=session
            )
            await self.collection.update_one(
                {"_id": from_id},
                {"$set": {"dependencies": []}},
                session=session
            )
```

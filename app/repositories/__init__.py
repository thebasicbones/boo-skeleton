"""Data Access Repositories"""
from app.repositories.sqlalchemy_resource_repository import SQLAlchemyResourceRepository
from app.repositories.base_resource_repository import BaseResourceRepository

__all__ = ['SQLAlchemyResourceRepository', 'BaseResourceRepository']

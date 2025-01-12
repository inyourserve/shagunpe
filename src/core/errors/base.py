# src/core/errors/base.py
from typing import Any, Dict, Optional

class BaseError(Exception):
   """Base class for custom exceptions"""
   def __init__(
       self,
       message: str,
       error_code: Optional[str] = None,
       details: Optional[Dict[str, Any]] = None
   ):
       self.message = message
       self.error_code = error_code
       self.details = details
       super().__init__(self.message)

class NotFoundError(BaseError):
   """Raised when a requested resource is not found"""
   def __init__(
       self,
       message: str = "Resource not found",
       error_code: Optional[str] = "NOT_FOUND",
       details: Optional[Dict[str, Any]] = None
   ):
       super().__init__(message, error_code, details)

class ValidationError(BaseError):
   """Raised when data validation fails"""
   def __init__(
       self,
       message: str = "Validation error",
       error_code: Optional[str] = "VALIDATION_ERROR",
       details: Optional[Dict[str, Any]] = None
   ):
       super().__init__(message, error_code, details)

class DatabaseError(BaseError):
   """Raised when database operations fail"""
   def __init__(
       self,
       message: str = "Database error",
       error_code: Optional[str] = "DATABASE_ERROR",
       details: Optional[Dict[str, Any]] = None
   ):
       super().__init__(message, error_code, details)

class AuthenticationError(BaseError):
   """Raised when authentication fails"""
   def __init__(
       self,
       message: str = "Authentication failed",
       error_code: Optional[str] = "AUTH_ERROR",
       details: Optional[Dict[str, Any]] = None
   ):
       super().__init__(message, error_code, details)

class AuthorizationError(BaseError):
   """Raised when user is not authorized to perform an action"""
   def __init__(
       self,
       message: str = "Not authorized",
       error_code: Optional[str] = "FORBIDDEN",
       details: Optional[Dict[str, Any]] = None
   ):
       super().__init__(message, error_code, details)

class BusinessLogicError(BaseError):
   """Raised when business logic rules are violated"""
   def __init__(
       self,
       message: str = "Business rule violation",
       error_code: Optional[str] = "BUSINESS_RULE_ERROR",
       details: Optional[Dict[str, Any]] = None
   ):
       super().__init__(message, error_code, details)

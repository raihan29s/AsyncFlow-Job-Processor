"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app.models import JobPriority, JobStatus, JobType


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    job_type: JobType = Field(..., description="Type of job to process")
    payload: Dict[str, Any] = Field(..., description="Job input data")
    priority: JobPriority = Field(
        default=JobPriority.NORMAL,
        description="Job priority level"
    )
    notify_email: Optional[str] = Field(
        default=None,
        description="Email address for job completion notification"
    )
    max_retries: Optional[int] = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )
    timeout_seconds: Optional[int] = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Job timeout in seconds"
    )
    user_id: Optional[str] = Field(default=None, description="User identifier")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")
    
    @field_validator("notify_email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation."""
        if v and "@" not in v:
            raise ValueError("Invalid email address")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_type": "data_processing",
                "payload": {
                    "input_file": "data.csv",
                    "operation": "transform",
                    "parameters": {"columns": ["name", "age"]}
                },
                "priority": "high",
                "notify_email": "user@example.com",
                "max_retries": 3
            }
        }


class JobResponse(BaseModel):
    """Schema for job response."""
    id: str
    job_type: JobType
    status: JobStatus
    priority: JobPriority
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    worker_id: Optional[str] = None
    notification_sent: bool
    actual_duration: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "job_type": "data_processing",
                "status": "completed",
                "priority": "high",
                "payload": {"input_file": "data.csv"},
                "result": {"output_file": "processed_data.csv", "rows_processed": 1000},
                "error_message": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": "2024-01-15T10:35:00Z",
                "retry_count": 0,
                "max_retries": 3,
                "worker_id": "worker-001",
                "notification_sent": True,
                "actual_duration": 295
            }
        }


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobUpdate(BaseModel):
    """Schema for updating job status (internal use)."""
    status: Optional[JobStatus] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None


class JobCancelRequest(BaseModel):
    """Schema for job cancellation request."""
    reason: Optional[str] = Field(default=None, description="Reason for cancellation")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database_connected: bool
    sqs_accessible: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "environment": "production",
                "database_connected": True,
                "sqs_accessible": True
            }
        }


class JobStatsResponse(BaseModel):
    """Schema for job statistics response."""
    total_jobs: int
    pending: int
    queued: int
    processing: int
    completed: int
    failed: int
    cancelled: int
    average_processing_time: Optional[float] = None
    success_rate: Optional[float] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Job not found",
                "detail": "Job with ID 550e8400-e29b-41d4-a716-446655440000 does not exist",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str  # job_update, job_completed, job_failed, heartbeat
    job_id: Optional[str] = None
    status: Optional[JobStatus] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NotificationRequest(BaseModel):
    """Schema for notification requests."""
    job_id: str
    recipient_email: str
    subject: str
    template: str
    context: Dict[str, Any]

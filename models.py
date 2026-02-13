"""
SQLAlchemy database models for job processing system.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, enum.Enum):
    """Job priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class JobType(str, enum.Enum):
    """Supported job types."""
    DATA_PROCESSING = "data_processing"
    REPORT_GENERATION = "report_generation"
    EMAIL_CAMPAIGN = "email_campaign"
    IMAGE_PROCESSING = "image_processing"
    VIDEO_TRANSCODING = "video_transcoding"
    ML_INFERENCE = "ml_inference"
    CUSTOM = "custom"


class Job(Base):
    """
    Job model representing an asynchronous task.
    
    Tracks the complete lifecycle of a job from submission to completion,
    including retries, failures, and notifications.
    """
    __tablename__ = "jobs"
    
    # Primary Key
    id = Column(String(36), primary_key=True, index=True)
    
    # Job Information
    job_type = Column(Enum(JobType), nullable=False, index=True)
    status = Column(
        Enum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING,
        index=True
    )
    priority = Column(
        Enum(JobPriority),
        nullable=False,
        default=JobPriority.NORMAL,
        index=True
    )
    
    # Job Data
    payload = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Retry Logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Worker Information
    worker_id = Column(String(100), nullable=True, index=True)
    
    # SQS Information
    sqs_message_id = Column(String(100), nullable=True, index=True)
    sqs_receipt_handle = Column(Text, nullable=True)
    
    # Notifications
    notify_email = Column(String(255), nullable=True)
    notification_sent = Column(Boolean, default=False, nullable=False)
    
    # Timeout and Resource Limits
    timeout_seconds = Column(Integer, default=3600, nullable=False)
    estimated_duration = Column(Integer, nullable=True)
    actual_duration = Column(Integer, nullable=True)
    
    # User Context
    user_id = Column(String(36), nullable=True, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_jobs_status_priority', 'status', 'priority'),
        Index('ix_jobs_created_at', 'created_at'),
        Index('ix_jobs_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, type={self.job_type}, "
            f"status={self.status}, priority={self.priority})>"
        )
    
    def to_dict(self) -> dict:
        """Convert job to dictionary representation."""
        return {
            "id": self.id,
            "job_type": self.job_type.value if self.job_type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "worker_id": self.worker_id,
            "notification_sent": self.notification_sent,
            "actual_duration": self.actual_duration,
        }


class JobLog(Base):
    """
    Job execution logs for debugging and auditing.
    Stores detailed information about job execution steps.
    """
    __tablename__ = "job_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), nullable=False, index=True)
    
    # Log Information
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Worker Information
    worker_id = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('ix_job_logs_job_id_created', 'job_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<JobLog(job_id={self.job_id}, level={self.level})>"


class WorkerHealth(Base):
    """
    Worker health monitoring table.
    Tracks active workers and their health status.
    """
    __tablename__ = "worker_health"
    
    worker_id = Column(String(100), primary_key=True)
    
    # Health Status
    status = Column(String(20), nullable=False, default="healthy")  # healthy, degraded, unhealthy
    last_heartbeat = Column(DateTime(timezone=True), nullable=False)
    
    # Worker Metrics
    active_jobs = Column(Integer, default=0, nullable=False)
    total_processed = Column(Integer, default=0, nullable=False)
    total_failed = Column(Integer, default=0, nullable=False)
    
    # Resource Usage
    cpu_usage = Column(Integer, nullable=True)  # Percentage
    memory_usage = Column(Integer, nullable=True)  # MB
    
    # Metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    version = Column(String(50), nullable=True)
    hostname = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<WorkerHealth(worker_id={self.worker_id}, status={self.status})>"

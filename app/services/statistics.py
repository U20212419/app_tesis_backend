import logging
import os
import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db import get_db
from app.exceptions import AppException, ResourceNotFoundException
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.models.section import Section
from app.models.statistics import Statistics
from app.schemas.statistics import StatisticsUpdate
from app.services import video_pipeline

logger = logging.getLogger(__name__)

class StatisticsService:
    """Service for handling statistics operations."""
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with a database session."""
        self.db = db
        try:
            access_key = os.getenv("AWS_ACCESS_KEY_ID")
            secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            region = os.getenv("AWS_REGION")
            logger.info("region: %s", region)

            if access_key and secret_key and region:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
                logger.info("Local: S3 client initialized with .env credentials.")
            elif not access_key and not secret_key and region:
                self.s3_client = boto3.client(
                    's3',
                    region_name=region
                )
                logger.info("Production: S3 client initialized with IAM role.")
            else:
                logger.error("S3 client initialization failed due to missing AWS credentials.")
                self.s3_client = None
        except Exception as e:
            logger.error("Failed to initialize S3 client: %s", e)
            self.s3_client = None

    def get_presigned_upload_url(self, file_name: str, user_id: str) -> dict:
        if not self.s3_client:
            raise AppException(
                message="S3 client is not initialized.",
                code="ERR_S3_CLIENT_NOT_INITIALIZED"
            )

        bucket_name = os.getenv("S3_BUCKET_NAME")
        if not bucket_name:
            raise AppException(
                message="S3 bucket name is not configured.",
                code="ERR_S3_BUCKET_NOT_CONFIGURED"
            )

        file_extension = os.path.splitext(file_name)[1]
        unique_key = f"videos/{user_id}/{uuid.uuid4()}{file_extension}"

        try:
            upload_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': unique_key,
                    'ContentType': 'video/mp4'
                },
                ExpiresIn=3600  # 1 hour expiration
            )

            region = os.getenv("AWS_REGION", "us-east-1")

            download_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_key}"
            logger.info("Generated presigned URL for user_id=%s unique_key=%s",
                        user_id, unique_key)
            return {
                "upload_url": upload_url,
                "download_url": download_url
            }
        except Exception as e:
            logger.error("Error generating presigned URL for user_id=%s: %s",
                         user_id, e, exc_info=True)
            raise AppException(
                message="Failed to generate presigned upload URL.",
                code="ERR_PRESIGNED_URL_GENERATION_FAILED"
            ) from e

    def _parse_s3_url(self, s3_url: str) -> tuple[str, str]:
        """Parse S3 URL into bucket and key."""
        try:
            parsed_url = urlparse(s3_url)
            hostname = parsed_url.hostname
            if parsed_url.scheme == 's3':
                bucket_name = parsed_url.netloc
                object_key = parsed_url.path.lstrip('/')
            elif hostname and ".s3.amazonaws.com" in hostname:
                # Format: https://[bucket].s3.amazonaws.com/[key]
                bucket_name = hostname.split('.')[0]
                object_key = parsed_url.path.lstrip('/')
            elif hostname and hostname.startswith("s3.") and ".amazonaws.com" in hostname:
                # Format: https://s3.[region].amazonaws.com/[bucket]/[key]
                path_parts = parsed_url.path.lstrip('/').split('/', 1)
                bucket_name = path_parts[0]
                object_key = path_parts[1]
            elif hostname and "s3." in hostname and ".amazonaws.com" in hostname:
                # Format: https://[bucket].s3.[region].amazonaws.com/[key]
                path_parts = hostname.split('.s3.', 1)
                bucket_name = path_parts[0]
                object_key = parsed_url.path.lstrip('/')
            else:
                raise ValueError("Invalid S3 URL format.")

            if not bucket_name or not object_key:
                raise ValueError("Bucket name or object key is missing in S3 URL.")

            return bucket_name, object_key
        except Exception as e:
            logger.error("Error parsing S3 URL %s: %s", s3_url, e)
            raise AppException(
                message="Invalid S3 URL provided.",
                code="ERR_INVALID_S3_URL"
            ) from e

    def _download_from_s3(self, s3_url: str) -> str:
        """Download a file from S3 to a temporary local path."""
        if not self.s3_client:
            raise AppException(
                message="S3 client is not initialized.",
                code="ERR_S3_CLIENT_NOT_INITIALIZED"
            )

        bucket_name, object_key = self._parse_s3_url(s3_url)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                logger.info("Downloading S3 object s3://%s/%s to %s",
                            bucket_name, object_key, tmp_file.name)
                self.s3_client.download_fileobj(bucket_name, object_key, tmp_file)
                logger.info("Download completed: %s", tmp_file.name)
                return tmp_file.name
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error("The object s3://%s/%s does not exist.",
                             bucket_name, object_key, exc_info=True)
                raise ResourceNotFoundException(
                    message="The requested S3 object does not exist."
                ) from e
            logger.error("Error downloading S3 object s3://%s/%s: %s",
                         bucket_name, object_key, e, exc_info=True)
            raise AppException(message="Failed to download file from S3.") from e

    def _cleanup_file(self, file_path: str, s3_url: str):
        """Remove a temporary file and the original S3 object."""
        try:
            logger.info("Removing temporary file %s", file_path)
            os.remove(file_path)
            logger.info("Temporary file %s removed", file_path)
        except OSError as e:
            logger.warning("Error removing temporary file %s: %s", file_path, e)

        if not self.s3_client:
            logger.warning("S3 client not initialized; %s cannot be deleted from S3.", s3_url)
            return

        try:
            bucket_name, object_key = self._parse_s3_url(s3_url)
            logger.info("Deleting S3 object s3://%s/%s", bucket_name, object_key)
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            logger.info("S3 object s3://%s/%s deleted", bucket_name, object_key)
        except Exception as e:
            logger.warning("Error deleting S3 object %s: %s", s3_url, e, exc_info=True)

    def _get_validated_assessment_and_section(self, user_id: str,
                                              assessment_id: int, section_id: int):
        """Validate that the assessment and section exist and belong to the user."""
        assessment_section = (
            self.db.query(Assessment, Section)
            .select_from(Assessment)
            .join(
                Section,
                and_(
                    Assessment.id_semester == Section.id_semester,
                    Assessment.id_course == Section.id_course
                )
            )
            .join(
                CourseInSemester,
                and_(
                    Assessment.id_course == CourseInSemester.Course_id_course,
                    Assessment.id_semester == CourseInSemester.Semester_id_semester
                )
            )
            .join(
                Course,
                CourseInSemester.Course_id_course == Course.id_course
            )
            .filter(
                Course.id_user == user_id,
                Assessment.id_assessment == assessment_id,
                Section.id_section == section_id,
                Course.is_deleted.is_(False),
                CourseInSemester.is_deleted.is_(False),
                Assessment.is_deleted.is_(False),
                Section.is_deleted.is_(False)
            )
            .first()
        )

        if not assessment_section:
            logger.warning("Assessment or Section not found for "
                           "assessment_id=%d, section_id=%d, user_id=%s",
                           assessment_id, section_id, user_id)
            raise ResourceNotFoundException(
                message="Assessment or Section not found."
            )
        return assessment_section

    def process_and_save_video(self, s3_url: str, question_amount: int,
                               assessment_id: int, section_id: int, user_id: str):
        """Process the video from S3 and save statistics to the database."""
        # Fetch assessment and section to validate existence and ownership
        self._get_validated_assessment_and_section(
            user_id,
            assessment_id,
            section_id
        )

        video_path = None
        try:
            # Download video from S3
            video_path = self._download_from_s3(s3_url)

            # Process video using the pipeline
            logger.info("Processing video for assessment_id=%d, section_id=%d, user_id=%s",
                        assessment_id, section_id, user_id)
            json_scores = video_pipeline.process_video(
                video_path=video_path,
                question_amount=question_amount
            )
            logger.info("Pipeline processing completed for "
                        "assessment_id=%d, section_id=%d, user_id=%s",
                        assessment_id, section_id, user_id)

            # Save or update statistics in the database
            self.create_or_update_statistics(
                assessment_id=assessment_id,
                section_id=section_id,
                user_id=user_id,
                stats_data=json_scores
            )
        except Exception as e:
            logger.error("Error processing video for "
                         "assessment_id=%d, section_id=%d, user_id=%s: %s",
                         assessment_id, section_id, user_id, e, exc_info=True)
        finally:
            if video_path:
                self._cleanup_file(video_path, s3_url)

    def create_or_update_statistics(self, assessment_id: int, section_id: int,
                                    stats_data: Optional[Dict[str, Any]], user_id: str,
                                    status: str = "PROCESSED"):
        """Create or update statistics in the database after processing a video."""
        # Fetch assessment and section to validate existence and ownership
        self._get_validated_assessment_and_section(
            user_id,
            assessment_id,
            section_id
        )

        try:
            existing_stats = (
                self.db.query(Statistics)
                .filter(
                    Statistics.id_assessment == assessment_id,
                    Statistics.id_section == section_id
                )
                .first()
            )

            if existing_stats:
                if stats_data is not None:
                    existing_stats.stats = stats_data
                existing_stats.is_deleted = False
                existing_stats.deleted_at = None
                existing_stats.status = status
                logger.info("Updated existing statistics for "
                            "assessment_id=%d, section_id=%d, user_id=%s",
                            assessment_id, section_id, user_id)
            else:
                new_stats = Statistics(
                    id_assessment=assessment_id,
                    id_section=section_id,
                    stats=stats_data,
                    status=status
                )
                self.db.add(new_stats)
                logger.info("Created new statistics for "
                            "assessment_id=%d, section_id=%d, user_id=%s",
                            assessment_id, section_id, user_id)
            
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Integrity error while saving statistics for "
                         "assessment_id=%d, section_id=%d, user_id=%s: %s",
                         assessment_id, section_id, user_id, e, exc_info=True)
            raise AppException() from e

    def update_statistics(self, assessment_id: int, section_id: int,
                          updated_statistics: StatisticsUpdate, user_id: str):
        """Update statistics scores and recalculated stats for a given assessment and section."""
        assessment, _ = self._get_validated_assessment_and_section(
            user_id,
            assessment_id,
            section_id
        )

        question_amount = assessment.question_amount
        if not question_amount:
            logger.error("Assessment id=%d has no question_amount set.", assessment_id)
            raise AppException(
                message="Assessment has no question amount set."
            )

        if updated_statistics.scores is not None:
            new_stats_dict = video_pipeline.calculate_statistics(
                updated_statistics.scores,
                question_amount
            )

            final_payload = {
                "scores": updated_statistics.scores,
                "statistics": new_stats_dict
            }

        try:
            db_stats = self.get_statistics(assessment_id, section_id, user_id)
            if updated_statistics.scores is not None:
                db_stats.stats = final_payload
            if updated_statistics.status is not None:
                db_stats.status = updated_statistics.status
            self.db.commit()
            self.db.refresh(db_stats)
            logger.info("Statistics updated for "
                        "assessment_id=%d, section_id=%d, user_id=%s",
                        assessment_id, section_id, user_id)
            return db_stats
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error occurred while updating statistics for "
                         "assessment_id=%d, section_id=%d, user_id=%s: %s",
                         assessment_id, section_id, user_id, e, exc_info=True)
            raise AppException() from e

    def get_statistics(self, assessment_id: int, section_id: int, user_id: str):
        """Retrieve statistics for a given assessment and section."""
        # Validate assessment and section existence and ownership
        self._get_validated_assessment_and_section(
            user_id,
            assessment_id,
            section_id
        )

        stats = (
            self.db.query(Statistics)
            .filter(
                Statistics.id_assessment == assessment_id,
                Statistics.id_section == section_id,
                Statistics.is_deleted.is_(False)
            )
            .first()
        )

        if not stats:
            logger.warning("Statistics not found for "
                           "assessment_id=%d, section_id=%d, user_id=%s",
                           assessment_id, section_id, user_id)
            raise ResourceNotFoundException(
                message="Statistics not found for the specified assessment and section."
            )
        return stats

    def delete_statistics(self, assessment_id: int, section_id: int, user_id: str):
        """Soft delete statistics for a given assessment and section."""
        # Validate assessment and section existence and ownership
        stats = self.get_statistics(
            assessment_id,
            section_id,
            user_id
        )

        if not stats:
            logger.warning("Statistics not found for deletion for "
                           "assessment_id=%d, section_id=%d, user_id=%s",
                           assessment_id, section_id, user_id)
            raise ResourceNotFoundException(
                message="Statistics not found for the specified assessment and section."
            )

        try:
            stats.is_deleted = True
            stats.deleted_at = func.now()
            stats.status = "DELETED"
            self.db.commit()
            logger.info("Statistics soft deleted for "
                        "assessment_id=%d, section_id=%d, user_id=%s",
                        assessment_id, section_id, user_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error occurred while soft deleting statistics for "
                         "assessment_id=%d, section_id=%d, user_id=%s: %s",
                         assessment_id, section_id, user_id, e, exc_info=True)
            raise AppException() from e

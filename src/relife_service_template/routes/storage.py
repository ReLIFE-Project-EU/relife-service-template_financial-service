import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from relife_service_template.auth.dependencies import (
    AuthenticatedUserDep,
    UserClientDep,
)
from relife_service_template.config.settings import SettingsDep
from relife_service_template.models.storage import FileUploadResponse, StorageFileInfo

router = APIRouter(tags=["storage"])

_logger = logging.getLogger("uvicorn")


@router.post("/storage", response_model=FileUploadResponse)
async def upload_file(
    supabase: UserClientDep,
    current_user: AuthenticatedUserDep,
    settings: SettingsDep,
    file: UploadFile = File(...),
):
    """Upload a file to Supabase Storage. Files are stored in a user-specific folder."""

    file_path = f"{current_user.user_id}/{file.filename}"
    file_content = await file.read()

    try:
        response = await supabase.storage.from_(settings.bucket_name).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type},
        )

        _logger.debug("Uploaded file: %s", response.full_path)

        public_url = await supabase.storage.from_(settings.bucket_name).get_public_url(
            file_path
        )

        return FileUploadResponse(
            message="File uploaded successfully",
            path=file_path,
            public_url=public_url,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get("/storage", response_model=list[StorageFileInfo])
async def list_files(
    supabase: UserClientDep,
    current_user: AuthenticatedUserDep,
    settings: SettingsDep,
):
    """List all files uploaded by the current user."""

    try:
        response = await supabase.storage.from_(settings.bucket_name).list(
            current_user.user_id
        )

        files = []

        for file in response:
            public_url = await supabase.storage.from_(
                settings.bucket_name
            ).get_public_url(f"{current_user.user_id}/{file['name']}")

            files.append(
                StorageFileInfo(
                    name=file["name"],
                    size=file["metadata"]["size"],
                    created_at=file["created_at"],
                    public_url=public_url,
                )
            )

        return files
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}",
        )

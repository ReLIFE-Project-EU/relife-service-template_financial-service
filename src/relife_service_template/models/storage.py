from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint."""

    message: str
    path: str
    public_url: str


class StorageFileInfo(BaseModel):
    """Model representing information about a stored file."""

    name: str
    size: int
    created_at: str
    public_url: str

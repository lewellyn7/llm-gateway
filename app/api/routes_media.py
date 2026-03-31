"""Media routes for multimodal."""
from fastapi import APIRouter, Depends, UploadFile, File
from app.core.security import verify_api_key
from app.services.media_service import MediaService

router = APIRouter()
media_service = MediaService()


@router.post("/media/image/process")
async def process_image(
    file: UploadFile = File(...),
    api_key_info: dict = Depends(verify_api_key),
):
    """Process an image for vision models."""
    content = await file.read()
    # In production, would upload to storage and get URL
    return {"processed": True, "size": len(content)}


@router.post("/media/audio/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    api_key_info: dict = Depends(verify_api_key),
):
    """Transcribe audio to text."""
    content = await file.read()
    # Placeholder - would use whisper API
    return {"text": "Transcription not yet implemented", "size": len(content)}

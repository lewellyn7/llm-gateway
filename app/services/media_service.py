"""Media service for multimodal requests."""


class MediaService:
    """Service for handling multimodal requests."""

    async def process_image(self, image_url: str) -> dict:
        """Process image URL for vision models."""
        # Placeholder for image processing
        return {"processed": True, "url": image_url}

    async def process_audio(self, audio_url: str) -> dict:
        """Process audio URL for speech-to-text."""
        # Placeholder for audio processing
        return {"processed": True, "url": audio_url}

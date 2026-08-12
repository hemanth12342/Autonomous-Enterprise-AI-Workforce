"""Documents API stub."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_documents():
    return []

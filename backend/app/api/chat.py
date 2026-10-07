from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def chat():
    """Chat endpoint - placeholder for Phase 3"""
    return {"message": "Chat endpoint coming in Phase 3"}


@router.get("/conversations")
async def get_conversations():
    """Get conversations - placeholder"""
    return {"conversations": []}


@router.get("/conversations/{id}")
async def get_conversation(id: str):
    """Get conversation by ID - placeholder"""
    return {"id": id, "messages": []}

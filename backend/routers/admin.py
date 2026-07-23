from fastapi import APIRouter, Depends
from db.supabase_client import supabase_admin
from core.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
async def list_users(admin=Depends(require_admin)):
    result = supabase_admin.from_("users").select("*").execute()
    return {"users": result.data}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin=Depends(require_admin)):
    supabase_admin.from_("users").delete().eq("id", user_id).execute()
    return {"message": "User deleted"}

@router.get("/stats")
async def system_stats(admin=Depends(require_admin)):
    users = supabase_admin.from_("users").select("id", count="exact").execute()
    debates = supabase_admin.from_("debates").select("id", count="exact").execute()
    return {
        "total_users": users.count,
        "total_debates": debates.count
    }

@router.patch("/users/{user_id}/ban")
async def ban_user(user_id: str, admin=Depends(require_admin)):
    supabase_admin.from_("users").update({"is_banned": True}).eq("id", user_id).execute()
    return {"message": "User banned"}
from typing import Optional
from pydantic import BaseModel
from supabase import Client
from fastapi import HTTPException

class AuthResult(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

class AuthService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def register_user(self, email: str, password: str) -> AuthResult:
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return AuthResult(
                success=True,
                message="Registration successful. Please verify your email.",
                data=response.dict()
            )
        except Exception as e:
            return AuthResult(
                success=False,
                message="Registration failed",
                error=str(e)
            )

    async def login_user(self, email: str, password: str) -> AuthResult:
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return AuthResult(
                success=True,
                message="Login successful",
                data=response.dict()
            )
        except Exception as e:
            return AuthResult(
                success=False,
                message="Invalid login credentials",
                error=str(e)
            )

    async def reset_password(self, email: str) -> AuthResult:
        try:
            response = self.supabase.auth.reset_password_email(email)
            return AuthResult(
                success=True,
                message="Password reset instructions have been sent to your email"
            )
        except Exception as e:
            return AuthResult(
                success=False,
                message="Password reset failed",
                error=str(e)
            )

    async def update_password(self, user_id: str, new_password: str) -> AuthResult:
        try:
            response = self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            return AuthResult(
                success=True,
                message="Password updated successfully"
            )
        except Exception as e:
            return AuthResult(
                success=False,
                message="Password update failed",
                error=str(e)
            ) 
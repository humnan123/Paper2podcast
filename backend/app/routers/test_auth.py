from fastapi import APIRouter, Depends

from app.dependencies import (
    get_current_user,
    require_role
)


router = APIRouter(
    prefix="/test",
    tags=["test"]
)



@router.get("/me")
def my_profile(
    user = Depends(get_current_user)
):

    return {
        "message": "Logged in user",
        "user": user
    }



@router.get("/author-only")
def author_test(
    user = Depends(
        require_role("author")
    )
):

    return {
        "message": "Author access granted",
        "user": user
    }



@router.get("/reviewer-only")
def reviewer_test(
    user = Depends(
        require_role("reviewer")
    )
):

    return {
        "message": "Reviewer access granted",
        "user": user
    }
"""CRUD operations package."""
from app.crud.user_crud import user_crud, UserCRUD
from app.crud.blog_crud import blog_crud, BlogCRUD
from app.crud.feature_request_crud import feature_request_crud, FeatureRequestCRUD
from app.crud.comment_crud import comment_crud, CommentCRUD

__all__ = [
    "user_crud",
    "UserCRUD",
    "blog_crud",
    "BlogCRUD",
    "feature_request_crud",
    "FeatureRequestCRUD",
    "comment_crud",
    "CommentCRUD"
]

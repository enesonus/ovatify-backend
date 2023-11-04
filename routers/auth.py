from fastapi import APIRouter, HTTPException
import logging
from utils.firebase import verify_token
from typing import Annotated
from fastapi import Header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


@router.post("/createUser")
async def create_user(authorization: Annotated[str | None, Header()] = None):
    if not authorization:
        logger.info("No authorization header")
        raise HTTPException(status_code=401, detail="Unauthorized.")
    bearer_token = authorization.split()[1]
    decoded_token = verify_token(bearer_token)
    logger.info(decoded_token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    # create user in database
    return {"message": "User created successfully", "uid": decoded_token}

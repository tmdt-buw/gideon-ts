from http import HTTPStatus

from fastapi import APIRouter
from starlette.responses import Response
from starlette.status import HTTP_204_NO_CONTENT


router = APIRouter(tags=["health"])


@router.get("/", status_code=HTTP_204_NO_CONTENT)
async def get() -> Response:
    """Check server health"""
    return Response(status_code=HTTPStatus.NO_CONTENT)

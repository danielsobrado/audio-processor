from fastapi import Request, status
from fastapi.responses import JSONResponse

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Placeholder for a generic exception handler.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"An unexpected error occurred: {exc}"},
    )

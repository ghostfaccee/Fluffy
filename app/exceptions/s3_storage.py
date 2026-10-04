from fastapi import HTTPException, status

class S3InternalError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Internal s3 storage error')


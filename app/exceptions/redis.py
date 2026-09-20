from fastapi import HTTPException, status

class InternalRedisError(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Internal redis error')

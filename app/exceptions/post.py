from fastapi import HTTPException, status

class PostDoesNotExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Post does not exists')

class AccessDenied(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, 'The user does not have permission for this post.')

class InvalidMediaKey(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, 'This media belongs to another user. The user attempted to access the media using a key that does not belong to them.')

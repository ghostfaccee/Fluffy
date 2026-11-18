from fastapi import HTTPException, status

class StoryDoesNotExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Story does not exists')

class InvalidStoryKey(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, 'This story key belongs to another person. The user attempted to claim rights to a story key that does not belong to them.')

class AccessDenied(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, 'The user does not have permission for this story.')

class StoryLimitExceeded(HTTPException):
    def __init__(self, limit: int = 5):
        super().__init__(status.HTTP_403_FORBIDDEN, f'You have exceeded the allowed limit of active stories. Limit: {limit}.')

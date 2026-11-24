from fastapi import HTTPException, status

class FriendshipDoesNotExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Friendship does not exists')

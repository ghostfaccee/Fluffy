from fastapi import HTTPException, status

class GroupNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, 'Group not found')

class NotGroupMember(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, 'Not group member')

class NoPermissions(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, 'No permissions')

class AlreadyGroupMember(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, 'Already group member')

class OwnerCannotLeave(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, 'Owner cannot leave')


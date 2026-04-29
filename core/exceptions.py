class Cars24Exception(Exception):
    pass


class SessionNotFoundError(Cars24Exception):
    pass


class CarNotFoundError(Cars24Exception):
    pass


class InvalidProfileError(Cars24Exception):
    pass

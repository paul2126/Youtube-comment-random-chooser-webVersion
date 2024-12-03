class SuccessException(Exception):
    """
    Custion exception to indicate success
    """
    def __init__(self, message="성공"):
        self.message = message
        super().__init__(self.message)


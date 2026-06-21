class DownloadAgentException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

class UpstreamAPIException(DownloadAgentException):
    def __init__(self, message: str, status_code: int = 500, detail: str = "") -> None:
        full_msg = f"{message} (Status: {status_code})"
        if detail:
            full_msg += f": {detail}"
        super().__init__(full_msg)
        self.status_code = status_code
        self.detail = detail

class MediaResolutionException(DownloadAgentException):
    pass

class FileSystemException(DownloadAgentException):
    pass

class ValidationException(DownloadAgentException):
    pass

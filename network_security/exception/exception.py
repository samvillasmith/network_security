import sys
# Import the custom 'logger' object we created in the other file
from network_security.logger.custom_logger import logger

class NetworkSecurityException(Exception):
    def __init__(self, error_message, error_detail: sys):
        self.error_message = error_message

        _, _, exc_tb = error_detail.exc_info()

        if exc_tb is not None:
            self.file_name = exc_tb.tb_frame.f_code.co_filename
            self.line_no = exc_tb.tb_lineno
        else:
            self.file_name = "<no active exception>"
            self.line_no = -1

    def __str__(self):
        return f"Error occurred in script: [{self.file_name}] at line number: [{self.line_no}] with error message: [{self.error_message}]"
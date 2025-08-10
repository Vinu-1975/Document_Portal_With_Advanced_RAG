import sys
import traceback
from logger.custom_logger import CustomLogger
logger = CustomLogger().get_logger(__file__)

class DocumentPortalException(Exception):
    """Custom exception for document portal"""
    def __init__(self,err_message, err_details:sys):
        _,_,exc_tb = err_details.exc_info()
        self.file_name = exc_tb.tb_frame.f_code.co_filename
        self.line_no = exc_tb.tb_lineno
        self.err_message = str(err_message)
        self.traceback_str = ''.join(traceback.format_exception(*err_details.exc_info()))
    
    def __str__(self):
        return f"""
        Error in [{self.file_name}] at line [{self.line_no}]
        Message: {self.err_message}
        Traceback:
        {self.traceback_str}
        """

if __name__ == "__main__":
    try:
        a = 1/0
        print(a)
    except Exception as e:
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # tb_str = ''.join(traceback.format_exception(exc_type,exc_value,exc_traceback))
        # print(f"An error occurred: {tb_str}")
        app_exc = DocumentPortalException(e,sys)
        logger.error(app_exc)
        raise app_exc
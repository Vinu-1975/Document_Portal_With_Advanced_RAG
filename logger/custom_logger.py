import os
import logging
from datetime import datetime
import struct
import structlog

class CustomLogger:
    def __init__(self, log_dir="logs"):
        # ensure logs dir exist
        self.logs_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.logs_dir, exist_ok=True)

        # create time-stamped log file
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.logs_dir, log_file)

        #configure logging
        # logging.basicConfig(
        #     filename=log_file_path,
        #     format="[%(asctime)s] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
        #     level=logging.INFO
        # )
    def get_logger(self,name=__file__):
        """
        Returns a logger instance with file + console handlers.
        Default name is the current file name (without path).
        """
        # return logging.getLogger(os.path.basename(name))
        logger_name = os.path.basename(name)
        # logger = logging.getLogger(logger_name)
        # logger.setLevel(logging.INFO)

        #format for both handlers
        # file_formatter = logging.Formatter(
        #     "[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s"
        # )
        # console_formatter = logging.Formatter(
        #     "[ %(levelname)s ] %(message)s"
        # )

        # File handler - logs saved to file
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Console handler - logs printed on console or terminal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s", # structlog will handle the JSON rendering
            handlers=[file_handler,console_handler]
        )

        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso",utc=True,key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )



        
        return structlog.get_logger(logger_name)

if __name__ == "__main__":
    logger = CustomLogger()
    logger = logger.get_logger(__file__)
    logger.info("Custom logger initialized")



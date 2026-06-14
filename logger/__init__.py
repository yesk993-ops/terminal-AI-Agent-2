import logging
import os
from datetime import datetime
from typing import Optional, List, Dict

class TellLogger:
    def __init__(self, name: str = "tell"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(simple_formatter)
        
        log_dir = os.path.expanduser("~/.tell")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(f"{log_dir}/tell_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)
        
    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)
        
    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)
        
    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)
        
    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def log_request(self, model: str, messages: List[Dict[str, str]]) -> None:
        self.logger.info(f"API Request - Model: {model}, Messages: {len(messages)}")
        
    def log_response(self, model: str, response: str, success: bool = True) -> None:
        self.logger.info(f"API Response - Model: {model}, Success: {success}, Response length: {len(response)}")
        
    def log_command(self, cmd: str, success: bool = True, error: Optional[str] = None) -> None:
        if success:
            self.logger.info(f"Command executed: {cmd}")
        else:
            self.logger.error(f"Command failed: {cmd}, Error: {error}")
            
    def log_security_block(self, reason: str, context: str = "") -> None:
        self.logger.warning(f"Security blocked - Reason: {reason}, Context: {context}")
        
    def log_file_operation(self, path: str, operation: str, success: bool = True, error: Optional[str] = None) -> None:
        if success:
            self.logger.info(f"File operation: {operation} {path}")
        else:
            self.logger.error(f"File operation failed: {operation} {path}, Error: {error}")

_logger: Optional[TellLogger] = None

def get_logger(name: Optional[str] = None) -> TellLogger:
    global _logger
    if _logger is None:
        _logger = TellLogger(name)
    return _logger

def log_api_call(model: str, message_count: int, success: bool = True) -> None:
    get_logger().log_request(model, message_count)
    if not success:
        get_logger().error(f"API call failed for model: {model}")

def log_command_execution(cmd: str, success: bool = True, error: Optional[str] = None) -> None:
    get_logger().log_command(cmd, success, error)

def log_security_event(reason: str, context: str = "") -> None:
    get_logger().log_security_block(reason, context)

def log_file_event(path: str, operation: str, success: bool = True, error: Optional[str] = None) -> None:
    get_logger().log_file_operation(path, operation, success, error)
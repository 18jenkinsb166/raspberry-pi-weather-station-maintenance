# code from: https://realpython.com/python-logging/

import logging
import os


# def setup_logger(name, file_path='log.log', c_level='INFO', f_level='INFO'):
def setup_logger(name, file_path='log.log', level='INFO'):
    log_file_dir = os.path.abspath(file_path)
    # clear log file:
    with open(log_file_dir, 'w') as file:
        file.write("")
    
    
    # Create a custom logger
    logger = logging.getLogger(name)
    # Create handlers
    c_handler = logging.StreamHandler()


    f_handler = logging.FileHandler(log_file_dir)
    # c_handler.setLevel(c_level)
    # f_handler.setLevel(f_level)
    logger.setLevel(level)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    logger.info(f"this logger named {name} created")




if __name__ == "__main__":
    setup_logger(name=__name__)
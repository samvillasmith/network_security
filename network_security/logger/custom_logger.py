import logging
import os
from datetime import datetime

LOG_FILE = f"network_security_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log"

logs_path = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_path, exist_ok=True)

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

# Configure the basic settings
logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='[%(asctime)s] %(lineno)d %(name)s %(levelname)s - %(message)s',
    level=logging.INFO 
)

# Best Practice: Create a specific logger object that you can import into other files
logger = logging.getLogger("NetworkSecurity")
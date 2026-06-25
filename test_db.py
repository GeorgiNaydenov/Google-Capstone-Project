import traceback
import sys
sys.path.append('c:/Users/User/Downloads/Google Capstone Project')

from capstone_agent.database import init_db

try:
    init_db()
    print("Success")
except Exception as e:
    traceback.print_exc()

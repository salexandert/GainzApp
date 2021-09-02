from flask_migrate import Migrate
from configs.config import config_dict
from app import create_app, db
import os
import sys
from transactions import Transactions
from flask import current_app
import tkinter as tk
import time
import threading

get_config_mode = os.environ.get('GENTELELLA_CONFIG_MODE', 'Debug')


try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid GENTELELLA_CONFIG_MODE environment variable entry.')


transactions = Transactions()
app = create_app(config_mode)
app.config['transactions'] = transactions
Migrate(app, db)

# root = tk.Tk()
# root.title('Gainz App!')
# print(os.getcwd())
# root.geometry("300x275")
# myLabel = tk.Label(root, text="Hello World!")
# myLabel.pack()

# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

if __name__ == "__main__":

    print(f"\n\nGainz App runs on a non-production (Flask) web server. \nTo access Gainz to go http://127.0.0.1:5000 in a web browser. Preferably Chrome\n")
    print(f"Default credentials username: admin, password: admin\n")
    print("Close this window when finished.\n")
    
    app.run(debug=True)
 

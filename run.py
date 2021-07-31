from flask_migrate import Migrate
from configs.config import config_dict
from app import create_app, db
import os
import sys
from transactions import Transactions
from flask import current_app

get_config_mode = os.environ.get('GENTELELLA_CONFIG_MODE', 'Debug')


try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    sys.exit('Error: Invalid GENTELELLA_CONFIG_MODE environment variable entry.')


transactions = Transactions()
app = create_app(config_mode)
app.config['transactions'] = transactions
Migrate(app, db)


if __name__ == "__main__":
    
    app.run(debug = True)

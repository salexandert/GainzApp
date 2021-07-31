from flask import Blueprint

blueprint = Blueprint(
    'wizard_blueprint',
    __name__,
    url_prefix='/wizards',
    template_folder='templates',
    static_folder='static'
)



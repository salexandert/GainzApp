from . import blueprint
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
import sys

@blueprint.route('/',  methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        print('post detected')
        data = request.json
        print(jsonify(data))
    
    print(sys.executable)

    return render_template('index.html', transactions=current_app.config['transactions'])
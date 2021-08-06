from . import blueprint
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from utils import *
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateTimeLocalField
from utils import *
from wtforms import SubmitField
from dateutil.tz import tzutc
import dateutil.parser

class StatsDateRange(FlaskForm):

    start = DateTimeLocalField('Start', format='%Y-%m-%dT%H:%M')
    end = DateTimeLocalField('End', format='%Y-%m-%dT%H:%M')
    submit = SubmitField('Submit')


@blueprint.route('/',  methods=['GET', 'POST'])
@login_required
def index():
    
    date_range = StatsDateRange()
    transactions = current_app.config['transactions']
    stats_table_data = get_stats_table_data(transactions)

    return render_template('model.html', stats_table_data=stats_table_data, date_range=date_range)


@blueprint.route('/selected_asset',  methods=['POST'])
@login_required
def selected_asset():
    # Populate Links, Sells, Buys Tables based on selected asset from stats table

    print(request.json)

    transactions = current_app.config['transactions']

    asset = request.json['row_data'][0]

    # Selected Asset
    row_data = request.json['row_data']
    unlinked_remaining = request.json['unlinked_remaining']
    long_term =  request.json['long_term']
    usd_spot = float(request.json['usd_spot'].replace(',', ''))
    quantity = float(request.json['quantity'].replace(',', ''))

    buy_list = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == asset
        and (datetime.datetime.now() - trans.time_stamp).days > 365
        and trans.unlinked_quantity > .0000001
    ]

    linkable_table_data = []
    for trans in buy_list:
        linkable_table_data.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(trans.usd_total),
            "${:,.2f}".format(trans.unlinked_quantity * usd_spot)
            ])

    # Get Batches that can satify sell
    linkable_table_data.sort(key=lambda x: x[5], reverse=True)
    
    target_quantity = quantity
    
    sell_fully_linked = False
    sell_fully_linked_max_profit = False
    sell_fully_linked_min_profit = False
    
    min_links_batch = []
    min_profit_batch = []
    max_profit_batch = []

    min_links_profit = 0.0
    min_profit_profit = 0.0
    max_profit_profit = 0.0

    min_links_quantity = 0.0
    min_profit_quantity = 0.0
    max_profit_quantity = 0.0
    
    for trans in linkable_table_data:

        buy_unlinked_quantity = trans[3]
        
        # Determine max link quantity
        if target_quantity <= buy_unlinked_quantity:
            quantity = target_quantity
        
        elif quantity >= buy_unlinked_quantity:
            quantity = buy_unlinked_quantity

        target_quantity -= quantity

        trans[5] = quantity

        buy_price = quantity * float(trans[4])
        sell_price = quantity * usd_spot
        profit = sell_price - buy_price

        trans[6] = "${:,.2f}".format(profit)

        min_links_batch.append(trans)

        min_links_profit += profit
        min_links_quantity += quantity

        if target_quantity <= 0:
            sell_fully_linked = True
            break
   
    if sell_fully_linked:

        # Minimum Profit Batch
        target_quantity = quantity

        # Sort by profit
        linkable_table_data.sort(key=lambda x: x[6])
        
        for trans in linkable_table_data:
            buy_unlinked_quantity = trans[3]
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                quantity = buy_unlinked_quantity

            target_quantity -= quantity

            # Setting Link Quantity
            trans[5] = quantity

            # Set Link profit
            buy_price = quantity * float(trans[4])
            sell_price = quantity * usd_spot
            profit = sell_price - buy_price
            trans[6] = "${:,.2f}".format(profit)


            min_profit_batch.append(trans)

            min_profit_profit += profit
            min_profit_quantity += quantity
            
            if target_quantity <= 0:
                sell_fully_linked_min_profit = True
                break

        # Maximum Profit Batch
        target_quantity = quantity
        
        # Sort by profit reversed
        linkable_table_data.sort(key=lambda x: x[6], reverse=True)
        
        for trans in linkable_table_data:
            buy_unlinked_quantity = trans[3]
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                quantity = buy_unlinked_quantity

            target_quantity -= quantity
            buy_price = quantity * float(trans[4])
            sell_price = quantity * usd_spot
            profit = sell_price - buy_price
            trans[6] = "${:,.2f}".format(profit)

            # Setting Link Quantity
            trans[5] = quantity

            max_profit_batch.append(trans)

            max_profit_profit += profit
            max_profit_quantity += quantity
            
            if target_quantity <= 0:
                sell_fully_linked_max_profit = True
                break





    data_dict = {}
    data_dict['min_links'] = min_links_batch
    data_dict['min_links_text'] = f"Total Quantity: {min_links_quantity} <br> Total Profit: {'${:,.2f}'.format(min_links_profit)}"
    data_dict['min_profit'] = min_profit_batch
    data_dict['min_profit_text'] = f"Total Quantity: {min_profit_quantity} <br> Total Profit: {'${:,.2f}'.format(min_profit_profit)}"
    data_dict['max_profit'] = max_profit_batch
    data_dict['max_profit_text'] = f"Total Quantity: {max_profit_quantity} <br> Total Profit: {'${:,.2f}'.format(max_profit_profit)}"
    
    return jsonify(data_dict)


@blueprint.route('/date_range',  methods=['POST'])
@login_required
def date_range():


    # print(f" Date Range from stats page {request.json} ")

    transactions = current_app.config['transactions']

    date_range = {
        'start_date': request.json['start_date'],
        'end_date': request.json['end_date']
    }

    date_range = get_transactions_date_range(transactions, date_range)
        
    stats_table_data = get_stats_table_data_range(transactions, date_range)

    stats_table_rows = []
    for row in stats_table_data:
        stats_table_rows.append([
            row['symbol'],
            row['total_purchased_quantity'],
            row['total_sold_quantity'],
            row['total_sold_unlinked_quantity'],
            row['total_purchased_unlinked_quantity'],
            row['total_purchased_usd'],
            row['total_sold_usd'],
            row['total_profit_loss'],
            row['hodl']
        ])

    data = {}
    data['stats_table_rows'] = stats_table_rows

    # convert dates back to string format
    date_range['start_date'] = datetime.datetime.strftime(date_range['start_date'], "%Y-%m-%d %H:%M")
    date_range['end_date'] = datetime.datetime.strftime(date_range['end_date'], "%Y-%m-%d %H:%M")
    
    data['date_range'] = date_range

    return jsonify(data)



@blueprint.route('/linkable_data', methods=['POST'])
@login_required
def linkable_data():
    
    
    print(request.json)
    transactions = current_app.config['transactions']

    # Get selected Trans Object
    row_data = request.json['row_data']
    trans1_name = row_data[0]
    for trans in transactions:
        # print(trans.name)
        if trans.name == trans1_name:
            print(f"Trans1 Found {trans.name}")
            trans1_obj = trans
            break

    linked_table_data = get_linked_table_data(transactions, trans1_obj)
    linkable_table_data = get_linkable_table_data(transactions, trans1_obj)

    data_dict = {}
    data_dict['linked'] = linked_table_data
    data_dict['linkable'] = linkable_table_data
    
    print("linked Below")


    return jsonify(data_dict)

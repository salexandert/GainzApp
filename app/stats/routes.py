from . import blueprint
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from utils import *
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateTimeLocalField
from utils import *
from wtforms import SubmitField

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

    return render_template('stats_page.html', stats_table_data=stats_table_data, date_range=date_range)


@blueprint.route('/selected_asset',  methods=['POST'])
@login_required
def selected_asset():
    # Populate Links, Sells, Buys Tables based on selected asset from stats table

    # print(request.json)

    transactions = current_app.config['transactions']

    date_range = {
        'start_date': request.json['start_date'],
        'end_date': request.json['end_date']
    }

    date_range = get_transactions_date_range(transactions, date_range)


    # get stats table data 
    stats_table_data = get_stats_table_data_range(transactions, date_range)

    # get stats for selected asset
    asset_stats = None
    for asset in stats_table_data:
        if asset['symbol'] == request.json['row_data'][0]:
            asset_stats = asset
            break
        
    asset = asset_stats['symbol']

    # print(asset_stats)

    # Create detailed stats table data
    detailed_stats = [
        ["Quantity Purchased", asset_stats['total_purchased_quantity']],
        ["Number of Buys", asset_stats["num_buys"]],
        ["Number of Sells", asset_stats["num_sells"]],
        ["Number of Links", asset_stats["num_links"]],
        ["Average Buy Price", asset_stats["average_buy_price"]],
        ["Average Sell Price", asset_stats["average_sell_price"]],
        ["Quantity Sold", asset_stats['total_sold_quantity']],
        ["Quantity Sold Unlinked", asset_stats['total_sold_unlinked_quantity']],
        ["Quantity Purchased Unlinked", asset_stats['total_purchased_unlinked_quantity']],
        ["Quantity Purchased in USD", asset_stats['total_purchased_usd']],
        ["Quantity Sold in USD", asset_stats['total_sold_usd']],
        ["Profit / Loss in USD", asset_stats['total_profit_loss']],
    ]

    # Get Linked Table Data
    linked_table_data = get_linked_table_data(transactions, asset, date_range)

    # Get all trans table data filtered by date range and asset
    all_trans_table_data_range = get_all_trans_table_data_range(transactions, asset, date_range)
    

    # Get Sells Table Data 
    sells_table_data = get_sells_trans_table_data_range(transactions, asset, date_range)

    # Get Buys Table Data
    buys_table_data = get_buys_trans_table_data_range(transactions, asset, date_range)

    # Chart Data
    start_date = date_range['start_date']
    end_date = date_range['end_date']
  
                                                                                                                      
    # Filter Transactions to date range
    filtered_transactions = []
    for trans in transactions:
        if trans.symbol != asset:
            continue

        if start_date and not end_date:
            if trans.time_stamp >= start_date:
                filtered_transactions.append(trans)

        elif not start_date and end_date:
            if trans.time_stamp <= end_date:
                filtered_transactions.append(trans)

        elif start_date and end_date:
            if trans.time_stamp >= start_date and trans.time_stamp <= end_date:              
                filtered_transactions.append(trans)


    unrealized_chart_data = []

    to_date_quantity = 0.0
    to_date_usd_total = 0.0
    filtered_transactions.sort(key=lambda x: x.time_stamp)
    for trans in filtered_transactions:

        if trans.trans_type == 'buy':
        
            to_date_quantity += trans.quantity
            to_date_usd_total += trans.usd_total
            if 'remove_cost_baisis_checkbox' in request.json:

                if request.json['remove_cost_baisis_checkbox']:
                    to_date_profit = (to_date_quantity * trans.usd_spot) - to_date_usd_total
                else:
                    to_date_profit = (to_date_quantity * trans.usd_spot)

            unrealized_chart_data.append({'x': datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"), 'y': to_date_profit, 'quantity': to_date_quantity})

        elif trans.trans_type == 'sell':

            to_date_quantity -= trans.quantity
            to_date_usd_total -= trans.usd_total
            if 'remove_cost_baisis_checkbox' in request.json:

                if request.json['remove_cost_baisis_checkbox']:
                    to_date_profit = (to_date_quantity * trans.usd_spot) - to_date_usd_total
                else:
                    to_date_profit = (to_date_quantity * trans.usd_spot)

            unrealized_chart_data.append({'x': datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"), 'y': to_date_profit, 'quantity': to_date_quantity})

    
    data_dict = {}
    data_dict['detailed_stats'] = detailed_stats
    data_dict['linked'] = linked_table_data
    data_dict['sells'] = sells_table_data
    data_dict['buys'] = buys_table_data

    data_dict['unrealized_chart_data'] = unrealized_chart_data


    
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
    
    
    # print(request.json)
    transactions = current_app.config['transactions']

    # Get selected Trans Object
    row_data = request.json['row_data']
    trans1_name = row_data[0]
    for trans in transactions:
        # print(trans.name)
        if trans.name == trans1_name:
            # print(f"Trans1 Found {trans.name}")
            trans1_obj = trans
            break

    linked_table_data = get_linked_table_data(transactions, trans1_obj)
    linkable_table_data = get_linkable_table_data(transactions, trans1_obj)

    data_dict = {}
    data_dict['linked'] = linked_table_data
    data_dict['linkable'] = linkable_table_data
    

    return jsonify(data_dict)

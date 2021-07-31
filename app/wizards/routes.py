from transactions import Transactions
from . import blueprint
from flask import Flask, render_template, session, redirect, url_for, session, request, current_app
from flask_wtf import FlaskForm
from flask_login import login_required, current_user
from wtforms import (StringField, BooleanField, DateTimeField,
                     RadioField,SelectField,TextField,
                     TextAreaField,SubmitField, DecimalField, DateField, IntegerField, FloatField)
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from transaction import Buy, Sell
import json
from werkzeug.utils import secure_filename
from flask import jsonify

from wtforms.fields.html5 import DateTimeLocalField
from utils import *
from dateutil.tz import tzutc
import dateutil.parser

class ManualTransaction(FlaskForm):
    '''
    Manual Transaction values
    '''
    timestamp = DateTimeLocalField('Timestamp', format='%Y-%m-%dT%H:%M')
    type  = SelectField(u'Type', choices=[('buy', 'Buy'), ('sell', 'Sell')])
    symbol = TextField('Crypto Symbol')
    quantity = DecimalField('Quantity', rounding=None)
    usd_spot = DecimalField('USD Spot', rounding=None)

    submit = SubmitField('Submit')


class CurrentHodl(FlaskForm):
    symbol = TextField('Crypto Symbol')
    quantity = DecimalField('Quantity', rounding=None)
    
    submit = SubmitField('Submit')


class Search(FlaskForm):
    quantity = DecimalField('Quantity', rounding=None)
    symbol = TextField('Crypto Symbol')
    profit = DecimalField('Profit', rounding=None)
    timestamp = DateField('Date Sold')

    
    submit = SubmitField('Search')

    
@blueprint.route('/import', methods=['GET', 'POST'])
@login_required
def import_wizard():

    transactions = current_app.config['transactions']
    manual_trans = ManualTransaction()
    current_hodl = CurrentHodl()


    if 'imported_transactions' not in session:
        session['imported_transactions'] = []

    if 'current_hodl' not in session:
        session['current_hodl'] = []

    # if file is uploaded add new transactions 
    if request.method == 'POST':

        # Import from CSV File
        if 'file' in request.files:
            file = request.files['file']
            transactions.import_transactions(file, filename=secure_filename(file.filename))
    

        # Current Hodl
        if current_hodl.validate_on_submit():
           pass

    
    stats_table_data = get_stats_table_data(transactions)
    all_trans_table_data = get_all_trans_table_data(transactions)
    
    return render_template('import_transactions.html', manual_trans=manual_trans, current_hodl=current_hodl,transactions=all_trans_table_data, stats_table_data=stats_table_data)


@blueprint.route('/add_transactions', methods=['GET', 'POST'])
@login_required
def add_transaction():

    transactions = current_app.config['transactions']
    manual_trans = ManualTransaction()

    stats_table_data = get_stats_table_data(transactions)


    # Import Manual trans
    if manual_trans.is_submitted():
        print('valid as fuck')
        
        imported_transactions = session['imported_transactions']

        print(manual_trans.data)
        if manual_trans.type.data == 'buy':
            trans = Buy(
                trans_type=manual_trans.type.data,
                time_stamp=manual_trans.timestamp.data, 
                quantity=float(manual_trans.quantity.data), 
                usd_spot=float(manual_trans.usd_spot.data), 
                symbol=manual_trans.symbol.data.upper(),
                source="Gainz App Manual Add"
                )
        
        elif manual_trans.type.data == 'sell':
            trans = Sell(
                trans_type=manual_trans.type.data, 
                time_stamp=manual_trans.timestamp.data, 
                quantity=float(manual_trans.quantity.data), 
                usd_spot=float(manual_trans.usd_spot.data),
                symbol=manual_trans.symbol.data.upper(),
                source="Gainz App Manual Add"
                )
        
        
        transactions.transactions.append(trans)
        transactions.save(description="Manually Added Transaction")
        
        trans_data = {}
        trans_data['name'] = trans.name
        trans_data['type'] = trans.trans_type
        trans_data['asset'] = trans.symbol
        trans_data['time_stamp'] = trans.time_stamp
        trans_data['usd_spot'] = "${:,.2f}".format(trans.usd_spot)
        trans_data['quantity'] = trans.quantity
        trans_data['unlinked_quantity'] = trans.unlinked_quantity
        trans_data['usd_total'] = "${:,.2f}".format(trans.usd_total)
    
        imported_transactions.append(trans_data)
        session['imported_transactions'] = imported_transactions

        stats_table_data = get_stats_table_data(transactions)
        
    
    return render_template('add_transactions.html',  manual_trans=manual_trans, stats_table_data=stats_table_data)


@blueprint.route('/add_links', methods=['GET', 'POST'])
@login_required
def add_links():

    transactions = current_app.config['transactions']
    # Init Tables
    stats_table_data = get_stats_table_data(transactions)
    all_trans_table_data = get_all_trans_table_data(transactions)
    
    # Search for Sell
    search = Search()
    if search.validate_on_submit():
        print(search.data)
        
        transactions_found = []
        for trans in all_trans_table_data:
            potential_trans = False
            
            if trans['type'] == 'sell':
                
                if search.symbol.data.upper() == trans['asset']:
                    print(f"symbols Match {trans['asset']}")
                    
                    if search.timestamp.data == trans['time_stamp']:
                        print('match',  trans['time_stamp'])
                        potential_trans = True
                    else:
                        print(f" This is the timestamp {trans['time_stamp']} right here ")

                if search.quantity.data:
                    if float(search.quantity.data) == float(trans['quantity']):
                        potential_trans = True
                        print(f"Quantity Match on {trans['quantity']}")


                # find with profit
                if search.profit.data and search.quantity.data:
                    quantity = float(search.quantity.data)
                    
                    buy_price = quantity * trans['usd_spot']
                    # sell_price = quantity * sell_obj.usd_spot

                    # profit = sell_price - buy_price

                if potential_trans:
                    transactions_found.append(trans)

    # All Sells Table Data
    all_sells_table_data = []
    for trans in transactions:
        if trans.trans_type == 'sell':
            trans_data = {}

            trans_data['name'] = trans.name
            trans_data['type'] = trans.trans_type
            trans_data['asset'] = trans.symbol
            trans_data['time_stamp'] = trans.time_stamp
            trans_data['usd_spot'] = "${:,.2f}".format(trans.usd_spot)
            trans_data['quantity'] = trans.quantity
            trans_data['unlinked_quantity'] = trans.unlinked_quantity
            trans_data['usd_total'] = "${:,.2f}".format(trans.usd_total)
            
            all_sells_table_data.append(trans_data)
   
    

    return render_template(
        'add_links.html',
        transactions=all_trans_table_data,
        search=search,
        stats_table_data=stats_table_data, 
        sells=all_sells_table_data,
        )



@blueprint.route('/linkable_data', methods=['POST'])
@login_required
def linkable_data():
    transactions = current_app.config['transactions']
    
    print(request.json)
    
    # Get selected Trans Object
    row_data = request.json['row_data']
    trans1_symbol = row_data[1]
    trans1_time_stamp_str = row_data[2]
    trans1_time_stamp = dateutil.parser.parse(trans1_time_stamp_str)
    trans1_quantity = row_data[3]
    trans1_usd_spot = row_data[5]

    for trans in transactions:
        
        if trans.symbol == trans1_symbol and trans.quantity == trans1_quantity:
            
            trans2_time_stamp = trans.time_stamp.to_pydatetime()
            trans1_time_stamp = trans1_time_stamp.replace(tzinfo=tzutc())
            trans2_time_stamp = trans2_time_stamp.replace(tzinfo=tzutc())

            if trans1_time_stamp == trans2_time_stamp:

                # print(f"Trans with Symbol {trans1_symbol} and quantity {trans1_quantity} Found")
                # print(f"USD Spot {trans1_usd_spot}  {trans.usd_spot}")
                # print(f"\nTrans 1 Time Stamp {trans1_time_stamp} ")
                # print(f"Time Stamp {trans1_time_stamp}  {trans2_time_stamp}")
                # print(f"Time Stamp {type(trans1_time_stamp)}  {type(trans2_time_stamp)}")
                # print(trans1_time_stamp == trans2_time_stamp)
                
                trans1_obj = trans
                break

    # Get Linked Table Data
    other_transactions = trans1_obj.linked_transactions
    linked_table_data = []
    for link in trans1_obj.links:
        linked_table_data.append([
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            link.buy.source,
            link.buy.quantity,
            link.buy.unlinked_quantity,
            "${:,.2f}".format(link.buy.usd_spot),
            link.quantity,
            "${:,.2f}".format(link.profit_loss)
        ])
        
    
        
    # Get Linkable Table Data
    linkable_table_data = []
    for trans in transactions:
        
        # Don't show if different Asset types
        if trans1_obj.symbol != trans.symbol:
            continue            

        # Don't show if 0.0 unlinked quantity WE SHOULD TEST 0 NOT 0.0 AS 0.01 ISSUE CAN ARRISE < changed 7/24 11:30 AM
        if trans1_obj.unlinked_quantity <= 0 or trans.unlinked_quantity <= 0:
            continue
        
        # Don't show if same type
        if trans.trans_type == trans1_obj.trans_type:
            continue
        
        # Don't show if already linked
        if trans.name in other_transactions:
            continue
        
        # Don't show if time problem
        if trans1_obj.trans_type == "sell":
            if trans1_obj.time_stamp < trans.time_stamp: 
                continue
        
        elif trans1_obj.trans_type == "buy":
            if trans1_obj.time_stamp < trans.time_stamp:
                continue

        # Determine Buy and Sell Objects
        if trans1_obj.trans_type == "sell" and trans.trans_type == "buy":
            
            sell_obj = trans1_obj
            buy_obj = trans

        elif trans1_obj.trans_type == "buy" and trans.trans_type == "sell":
            sell_obj = trans
            buy_obj = trans1_obj
        
        else:
            continue

        # Determine max link quantity
        if sell_obj.unlinked_quantity <= buy_obj.unlinked_quantity:
            quantity = sell_obj.unlinked_quantity
        
        elif sell_obj.unlinked_quantity >= buy_obj.unlinked_quantity:
            quantity = buy_obj.unlinked_quantity

        # Determine link profitability
        buy_price = quantity * buy_obj.usd_spot
        sell_price = quantity * sell_obj.usd_spot
        profit = sell_price - buy_price


        linkable_table_data.append([
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"), 
            trans.source, 
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot), 
            quantity,
            "${:,.2f}".format(profit)
            ])

    # Get Batches that can satify sell
    
    linkable_table_data.sort(key=lambda x: x[5], reverse=True)
    
    # Minimum Links Batch
    target_quantity = trans1_obj.unlinked_quantity
    sell_fully_linked = False
    sell_fully_linked_max_profit = False
    sell_fully_linked_min_profit = False
    min_links_batch = []
    min_profit_batch = []
    max_profit_batch = []
    for trans in linkable_table_data:
        
        min_links_batch.append(trans)
        target_quantity -= trans[5]
        if target_quantity <= 0:
            sell_fully_linked = True
            break
   
    if sell_fully_linked:
        # Minimum Profit Batch
        target_quantity = trans1_obj.unlinked_quantity
        linkable_table_data.sort(key=lambda x: x[6])
        
        
        for trans in linkable_table_data:
            min_profit_batch.append(trans)
            target_quantity -= trans[5]
            if target_quantity <= 0:
                sell_fully_linked_min_profit = True
                break

        # Maximum Profit Batch
        target_quantity = trans1_obj.unlinked_quantity
        linkable_table_data.sort(key=lambda x: x[6], reverse=True)
        
        
        for trans in linkable_table_data:
            max_profit_batch.append(trans)
            target_quantity -= trans[5]
            if target_quantity <= 0:
                sell_fully_linked_max_profit = True
                break

    
    # print("\nMinimum Links Batchh")
    # print(min_links_batch)

    # print("\nMinimum Profit Batch")
    # print(min_profit_batch)

    # print("\nMaximum Profit Batch")
    # print(max_profit_batch)


    # Get Unlinkable 
    unlinkable_transactions = []
    unlinkable_table_data = []
    for trans in transactions:

        # Don't show if different Asset types
        if trans1_obj.symbol != trans.symbol:
            continue       

        # Don't show if same type
        if trans.trans_type == trans1_obj.trans_type:
            continue   

        # Don't show if already linked
        if trans.name in other_transactions:
            continue 

        # Determine Buy and Sell Objects
        if trans1_obj.trans_type == "sell" and trans.trans_type == "buy":
            
            sell_obj = trans1_obj
            buy_obj = trans

        elif trans1_obj.trans_type == "buy" and trans.trans_type == "sell":
            sell_obj = trans
            buy_obj = trans1_obj

        # Don't show if time problem
        if trans1_obj.trans_type == "sell":
            if trans1_obj.time_stamp < trans.time_stamp: 
                continue
        
        # Don't show if 0.0 unlinked quantity WE SHOULD TEST 0 NOT 0.0 AS 0.01 ISSUE CAN ARRISE < changed 7/24 11:30 AM
        if trans.unlinked_quantity <= 0:
            unlinkable_transactions.append(trans)

    # Create unlinkable Table Data 
    for trans in unlinkable_transactions:
        # Determine Buy and Sell Objects
        if trans1_obj.trans_type == "sell" and trans.trans_type == "buy":
            
            sell_obj = trans1_obj
            buy_obj = trans

        elif trans1_obj.trans_type == "buy" and trans.trans_type == "sell":
            sell_obj = trans
            buy_obj = trans1_obj

        # Determine max link quantity
        if sell_obj.unlinked_quantity <= buy_obj.unlinked_quantity:
            quantity = sell_obj.unlinked_quantity
        
        elif sell_obj.unlinked_quantity >= buy_obj.unlinked_quantity:
            quantity = buy_obj.unlinked_quantity

        # Determine link profitability
        buy_price = quantity * buy_obj.usd_spot
        sell_price = quantity * sell_obj.usd_spot
        profit = sell_price - buy_price

        unlinkable_table_data.append([
            trans.name, 
            trans.trans_type.capitalize(),
            trans.symbol,
            trans.time_stamp, 
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot), 
            "${:,.2f}".format(trans.usd_total),
            "${:,.2f}".format(profit),
            "Buy is Fully Linked!"        
        ])

    

    data_dict = {}
    data_dict['linked'] = linked_table_data
    data_dict['linkable'] = linkable_table_data
    data_dict['unlinkable'] = unlinkable_table_data
    
    # print("linked Below")
    # print(linked_table_data)
    # print()
    return jsonify(data_dict)


@blueprint.route('/link_button', methods=['POST'])
@login_required
def link_button():
    print(request.json)
    transactions = current_app.config['transactions']
    
    # Get selected Trans Object
    sell_data = request.json['sell_data']
    buy_data = request.json['buy_data']
    
    # Get Sell Object 
    trans1_symbol = sell_data[1]
    trans1_time_stamp_str = sell_data[2]
    trans1_time_stamp = dateutil.parser.parse(trans1_time_stamp_str)
    trans1_quantity = sell_data[3]
    trans1_usd_spot = sell_data[5]

    sell_obj = None
    for trans in transactions:
        
        if trans.symbol == trans1_symbol and trans.quantity == trans1_quantity:
            
            trans2_time_stamp = trans.time_stamp.to_pydatetime()
            trans1_time_stamp = trans1_time_stamp.replace(tzinfo=tzutc())
            trans2_time_stamp = trans2_time_stamp.replace(tzinfo=tzutc())

            if trans1_time_stamp == trans2_time_stamp:

                # print(f"Trans with Symbol {trans1_symbol} and quantity {trans1_quantity} Found")
                # print(f"USD Spot {trans1_usd_spot}  {trans.usd_spot}")
                # print(f"\nTrans 1 Time Stamp {trans1_time_stamp} ")
                # print(f"Time Stamp {trans1_time_stamp}  {trans2_time_stamp}")
                # print(f"Time Stamp {type(trans1_time_stamp)}  {type(trans2_time_stamp)}")
                # print(trans1_time_stamp == trans2_time_stamp)
                
                sell_obj = trans
                break
    
    # Get Buy Object
    trans1_time_stamp_str = buy_data[0]
    trans1_time_stamp = dateutil.parser.parse(trans1_time_stamp_str)
    trans1_quantity = buy_data[2]
    trans1_usd_spot = buy_data[4]
    quantity = buy_data[5]

    buy_obj = None
    for trans in transactions:
        
        if trans.symbol == trans1_symbol and trans.quantity == trans1_quantity:
            
            trans2_time_stamp = trans.time_stamp.to_pydatetime()
            trans1_time_stamp = trans1_time_stamp.replace(tzinfo=tzutc())
            trans2_time_stamp = trans2_time_stamp.replace(tzinfo=tzutc())

            if trans1_time_stamp == trans2_time_stamp:
                
                buy_obj = trans
                break

            
    if sell_obj and buy_obj:
        sell_obj.link_transaction(buy_obj, quantity)
        
        transactions.save(description="Manually Added Link")

    # All Sells Table Data
    all_sells_table_data = []
    for trans in transactions:
        if trans.trans_type == 'sell':

            all_sells_table_data.append([
            trans.name,
            trans.trans_type,
            trans.symbol,
            trans.time_stamp,
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(trans.usd_total)
            ])

    return jsonify(all_sells_table_data)


@blueprint.route('/hodl_accounting', methods=['POST', 'GET'])
@login_required
def hodl_accounting():
    transactions = current_app.config['transactions']
    
    stats_table_data = get_stats_table_data(transactions)

    if request.method == "POST":
        print(request.json)

        asset = request.json['asset'][0]
        hodl = float(request.json['quantity'])

        transactions.convert_sends_to_sells(asset=asset, current_hodl=hodl)

        transactions.save(description="Converted Sends to Sells")

        return jsonify("Converted Sends to Sells!")
    
    return render_template('hodl_accounting.html', stats_table_data=stats_table_data)


@blueprint.route('/auto_link', methods=['GET'])
@login_required
def auto_link():
    transactions = current_app.config['transactions']
    stats_table_data = get_stats_table_data(transactions)

    return render_template('auto_link.html', stats_table_data=stats_table_data)


@blueprint.route('/auto_link_asset', methods=['POST'])
@login_required
def auto_link_asset():
    transactions = current_app.config['transactions']
        
    print(request.json)
    
    asset = request.json['asset'][0]
    algo_type = request.json['algo']

    if algo_type == "fifo":
        transactions.link_with_fifo(asset)
        transactions.save(description="Auto Linked with FIFO")

    elif algo_type == "filo":
        transactions.link_with_filo(asset)
        transactions.save(description="Auto Linked with FILO")


    return jsonify("Auto-Link FTW!")


@blueprint.route('/auto_link_pre_check', methods=['POST'])
@login_required
def auto_link_pre_check():
    
    
    # print(request.json)
    
    data = {}
    
    asset = request.json['row_data'][0]

    transactions = current_app.config['transactions']

    sells = []
    buys = []
    
    sold = 0.0
    bought = 0.0
    
    checks = True

    for trans in transactions:
        if trans.symbol != asset:
            continue

        if trans.trans_type == "sell":
            sells.append(trans)
            sold += trans.quantity
        
        elif trans.trans_type == "buy":
            buys.append(trans)
            bought += trans.quantity

    print(asset)
    print(bought, sold)

    sells.sort(key=lambda x: x.time_stamp)
    buys.sort(key=lambda x: x.time_stamp)
    sold_to_date = 0.0
    latest_sell_time_stamp = None
    is_greater = False
    for sell in sells:

        if is_greater is True:
            break

        latest_sell_time_stamp = sell.time_stamp
        sold_to_date += sell.quantity
        bought_to_date = 0.0
        
        for buy in buys:
            
        
            # check if buy came before sell and if bought_to_date < sold_to_date
            if buy.time_stamp > sell.time_stamp and sold_to_date > bought_to_date:
                
                is_greater = True
                break

            else:

                bought_to_date += buy.quantity

            

    message = ""
    if bought >= sold:
        message += "Check Passed: More Buys than Sells"
        if is_greater is True:
            message += f"<br> Check Failed: At sell timestamp [{latest_sell_time_stamp}] buys [{bought_to_date}] can no longer cover sells [{sold_to_date}] "
            message += "<br> If you continue you will have sells not fully linked to buys."
            message += f"<br> You can track down the discrepency and add [{sold_to_date - bought_to_date}] in buys before [{latest_sell_time_stamp}], or  full profit amount will be used on unlinked sells."
        else:
            message += "<br> Check Passed: Individual sells can be covered by an earlier buy"
    else:
        message += "Check Failed: More Sells than buys"

    

        
    data['message'] = message

    return jsonify(data)


@blueprint.route('/buys_to_lost', methods=['POST'])
@login_required
def buys_to_lost():
    
    transactions = current_app.config['transactions']

    print(request.json)

    asset = request.json['asset'][0]
    hodl = float(request.json['quantity'])

    transactions.convert_buys_to_lost(asset=asset, current_hodl=hodl)

    transactions.save(description="Converted Buys to Lost")

    return jsonify("Yess")
    

@blueprint.route('/hodl_info', methods=['POST'])
@login_required
def hodl_info():
    asset_symbol = request.json['asset'][0]
    hodl = float(request.json['quantity'])

    transactions = current_app.config['transactions']

    for a in transactions.asset_objects:
        print(a.symbol, asset_symbol)
        if a.symbol != asset_symbol:
            continue 

        a.hodl = hodl
        print(f"Setting HODL for {a.symbol} is {a.hodl}")

    for a in transactions.asset_objects:
        print(f"Asset Object symbol {a.symbol} Asset {asset_symbol} HODL {a.hodl}")
        if a.hodl is not None:
            hodl = a.hodl
            print(f"Asset Object symbol {a.symbol} Asset {asset_symbol} HODL {a.hodl}")

    transactions.save(description=f"Added HODL for {asset_symbol}")

    return jsonify("HODL Accepted")


@blueprint.route('/sends_to_sells', methods=['POST'])
@login_required
def sends_to_sells():
    
    transactions = current_app.config['transactions']
    

    asset = request.json['asset'][0]
    amount_to_convert = float(request.json['quantity'])
    
    for a in transactions.asset_objects:
        if a.symbol != asset:
            continue 
        

        transactions.convert_sends_to_sells(asset=asset, amount_to_convert=amount_to_convert)

        transactions.save(description="Converted Sends to sells")

        # current_app.config['transactions'] = transactions.load()

        return jsonify("Yess")


@blueprint.route('/selected_asset',  methods=['POST'])
@login_required
def selected_asset():
    # Populate Links, Sells, Buys Tables based on selected asset from stats table

    print(request.json)

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
        ["Quantity Purchased Unlinked, AKA The HODL", asset_stats['total_purchased_unlinked_quantity']],
        ["Quantity Purchased in USD", asset_stats['total_purchased_usd']],
        ["Quantity Sold in USD", asset_stats['total_sold_usd']],
        ["Profit / Loss in USD* (Valid when Quantity Sold Unlinked is 0)", asset_stats['total_profit_loss']],
    ]

    # Get Linked Table Data
    linked_table_data = get_linked_table_data(transactions, asset, date_range)

    
    # Get Sells Table Data 
    sells_table_data = get_sells_trans_table_data_range(transactions, asset, date_range)

    sells_unlinked_remaining = []
    if request.json['unlinked_remaining']:
        for sell in sells_table_data:
            if sell[4] > 0.00001:
                sells_unlinked_remaining.append(sell)

        sells_table_data = sells_unlinked_remaining

    # Get Buys Table Data
    buys_table_data = get_buys_trans_table_data_range(transactions, asset, date_range)


    data_dict = {}
    data_dict['detailed_stats'] = detailed_stats
    data_dict['linked'] = linked_table_data
    data_dict['sells'] = sells_table_data
    data_dict['buys'] = buys_table_data
    
    
    return jsonify(data_dict)



@blueprint.route('/add_transactions_selected_asset',  methods=['POST'])
@login_required
def add_transactions_selected_asset():


    print(request.json)

    transactions = current_app.config['transactions']

    date_range = {
        'start_date': '',
        'end_date': ''
    }

    asset = request.json['row_data'][0]

    # Get date range of transactions
    date_range = get_transactions_date_range(transactions, date_range)

    # Get stats table data 
    stats_table_data = get_stats_table_data_range(transactions, date_range)


     # Get Sells Table Data 
    sells_table_data = get_sells_trans_table_data_range(transactions, asset, date_range)


    # Get Buys Table Data
    buys_table_data = get_buys_trans_table_data_range(transactions, asset, date_range)

    # Get Sends Table Data
    sends_table_data = get_sends_trans_table_data_range(transactions, asset, date_range)


    data_dict = {}
    data_dict['sells'] = sells_table_data
    data_dict['buys'] = buys_table_data
    data_dict['sends'] = sends_table_data

    return jsonify(data_dict)


@blueprint.route('/delete',  methods=['POST'])
@login_required
def delete():

    asset = request.json['asset'][0]
    trans_type = request.json['type']

    transactions = current_app.config['transactions']

    # Get selected Trans Object
    row_data = request.json['row_data']
    trans1_symbol = row_data[1]
    trans1_time_stamp_str = row_data[2]
    trans1_time_stamp = dateutil.parser.parse(trans1_time_stamp_str)
    trans1_quantity = row_data[3]
    trans1_usd_spot = row_data[5]

    for trans in transactions:
    
        if trans.symbol == trans1_symbol and trans.quantity == trans1_quantity:
            
            if isinstance(trans.time_stamp, datetime.date):
                trans2_time_stamp = trans.time_stamp
            else:
                trans2_time_stamp = trans.time_stamp.to_pydatetime()
                trans1_time_stamp = trans1_time_stamp.replace(tzinfo=tzutc())
                trans2_time_stamp = trans2_time_stamp.replace(tzinfo=tzutc())

            if trans1_time_stamp == trans2_time_stamp:

                # print(f"Trans with Symbol {trans1_symbol} and quantity {trans1_quantity} Found")
                # print(f"USD Spot {trans1_usd_spot}  {trans.usd_spot}")
                # print(f"\nTrans 1 Time Stamp {trans1_time_stamp} ")
                # print(f"Time Stamp {trans1_time_stamp}  {trans2_time_stamp}")
                # print(f"Time Stamp {type(trans1_time_stamp)}  {type(trans2_time_stamp)}")
                # print(trans1_time_stamp == trans2_time_stamp)
                
                trans1_obj = trans
                break
    
    
    trans1_name = trans1_obj.name
    transactions.transactions.remove(trans)
    transactions.save(f'Deleted {asset} {trans_type} {trans1_name}')

    return jsonify(f'Deleted {asset} {trans_type} {trans1_name}')
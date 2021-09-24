
from . import blueprint
from flask import Flask, render_template, session, redirect, url_for, session, request, current_app
from flask_wtf import FlaskForm
from flask_login import login_required, current_user
from wtforms import (SelectField,TextField,
                     SubmitField, DecimalField, DateField)

from wtforms.fields.html5 import DateField
from transaction import Buy, Sell
import json
from werkzeug.utils import secure_filename
from flask import jsonify
from conversion import Conversion

from wtforms.fields.html5 import DateTimeLocalField
from utils import *

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
    
    # print(request.json)
    
    # Get Sell Object
    row_data = request.json['row_data']
    symbol = row_data[1]
    time_stamp_str = row_data[2]
    time_stamp = dateutil.parser.parse(time_stamp_str)
    quantity = row_data[3]
    usd_spot = row_data[5]

    sell_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='sell', quantity=quantity, time_stamp=time_stamp)

    potential_sale_quantity = sell_obj.unlinked_quantity
    potential_sale_usd_spot = sell_obj.usd_spot
    total_in_usd = (sell_obj.usd_spot * sell_obj.unlinked_quantity)
    asset = sell_obj.symbol

    # Get Linked Table Data
    other_transactions = sell_obj.linked_transactions
    linked_table_data = []
    for link in sell_obj.links:

        if link.buy.unlinked_quantity != 0 and link.buy.unlinked_quantity < 0.00000009:
            unlinked_quantity = "Less than 0.00000009"
        else:
            unlinked_quantity = link.buy.unlinked_quantity
        
        linked_table_data.append([
            datetime.datetime.strftime(link.buy.time_stamp, "%Y-%m-%d %H:%M:%S"),
            link.buy.source,
            link.buy.quantity,
            unlinked_quantity,
            "${:,.2f}".format(link.buy.usd_spot),
            link.quantity,
            "${:,.2f}".format(link.profit_loss)
        ])
    
    
    # All Linkable Buys 
    linkable_buys = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == sell_obj.symbol
        and (sell_obj.time_stamp > trans.time_stamp)
        and trans.unlinked_quantity > .0000001
    ]

    linkable_table_data = []
    
    for trans in linkable_buys:
        target_quantity = potential_sale_quantity
        # Determine max link quantity
        if target_quantity <= trans.unlinked_quantity:
            link_quantity = target_quantity
        
        elif target_quantity >= trans.unlinked_quantity:
            link_quantity = trans.unlinked_quantity

        target_quantity -= link_quantity

        cost_basis = link_quantity * float(trans.usd_spot)
        proceeds = link_quantity * potential_sale_usd_spot
        gain_or_loss = proceeds - cost_basis

        if abs(gain_or_loss) < 0.01:
            continue

        linkable_table_data.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            trans.unlinked_quantity,
            link_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(proceeds),
            "${:,.2f}".format(cost_basis),
            "${:,.2f}".format(gain_or_loss)
            ])

    # Linkable Buys Long
    linkable_buys_long = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == asset
        and (datetime.datetime.now() - trans.time_stamp).days > 365
        and trans.unlinked_quantity > .0000001
    ]


    # Linkable Buys Short
    linkable_buys_short = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == asset
        and (datetime.datetime.now() - trans.time_stamp).days <= 365
        and trans.unlinked_quantity > .0000001
    ]

    # Start Batches
    target_quantity = potential_sale_quantity
    
    sell_fully_linked = False

    # Batch Types    
    min_links_batch = []
    min_links_batch_gain = 0.0
    min_links_batch_quantity = 0.0
    
    min_gain_batch = []
    min_gain_batch_gain = 0.0
    min_gain_batch_quantity = 0.0

    min_gain_long_batch = []
    min_gain_long_batch_gain = 0.0
    min_gain_long_batch_quantity = 0.0
    
    min_gain_short_batch = []
    min_gain_short_batch_gain = 0.0
    min_gain_short_batch_quantity = 0.0

    max_gain_batch = []
    max_gain_batch_gain = 0.0
    max_gain_batch_quantity = 0.0
    
    max_gain_long_batch = []
    max_gain_long_batch_gain = 0.0
    max_gain_long_batch_quantity = 0.0
    
    max_gain_short_batch = []
    max_gain_short_batch_gain = 0.0
    max_gain_short_batch_quantity = 0.0

    
    linkable_buys.sort(key=lambda trans: trans.unlinked_quantity, reverse=True)
    
    # Min Links Batch
    for trans in linkable_buys:

        buy_unlinked_quantity = trans.unlinked_quantity
        
        # Determine max link quantity
        if target_quantity <= buy_unlinked_quantity:
            link_quantity = target_quantity
        
        elif target_quantity >= buy_unlinked_quantity:
            link_quantity = buy_unlinked_quantity

        target_quantity -= link_quantity

        cost_basis = link_quantity * float(trans.usd_spot)
        proceeds = link_quantity * potential_sale_usd_spot
        gain_or_loss = proceeds - cost_basis

        if abs(gain_or_loss) < 0.01:
            continue

        min_links_batch_gain += gain_or_loss
        min_links_batch_quantity += link_quantity

        min_links_batch.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            trans.unlinked_quantity,
            link_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(proceeds),
            "${:,.2f}".format(cost_basis),
            "${:,.2f}".format(gain_or_loss)
            ])

        if target_quantity <= 0:
            sell_fully_linked = True
            break
   

    if sell_fully_linked:
        
        ## Batches without long/short requirement

        # Min Gain Batch
        target_quantity = potential_sale_quantity

        linkable_buys.sort(key=lambda trans: trans.usd_spot, reverse=True)
        
        for trans in linkable_buys:
            buy_unlinked_quantity = trans.unlinked_quantity
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                link_quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                link_quantity = buy_unlinked_quantity

            target_quantity -= link_quantity

            cost_basis = link_quantity * float(trans.usd_spot)
            proceeds = link_quantity * potential_sale_usd_spot
            gain_or_loss = proceeds - cost_basis

            if abs(gain_or_loss) < 0.01:
                continue

            min_gain_batch_gain += gain_or_loss
            min_gain_batch_quantity += link_quantity

            min_gain_batch.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                link_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(proceeds),
                "${:,.2f}".format(cost_basis),
                "${:,.2f}".format(gain_or_loss)
                ])
            
            if target_quantity <= 0:
                sell_fully_linked_min_profit = True
                break

        # Max Gain Batch
        target_quantity = potential_sale_quantity
        
        # Sort by profit
        linkable_buys.sort(key=lambda trans: trans.usd_spot)
        
        for trans in linkable_buys:
            buy_unlinked_quantity = trans.unlinked_quantity
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                link_quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                link_quantity = buy_unlinked_quantity

            target_quantity -= link_quantity
            
            cost_basis = link_quantity * float(trans.usd_spot)
            proceeds = link_quantity * potential_sale_usd_spot
            gain_or_loss = proceeds - cost_basis

            if abs(gain_or_loss) < 0.01:
                continue

            max_gain_batch.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                link_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(proceeds),
                "${:,.2f}".format(cost_basis),
                "${:,.2f}".format(gain_or_loss)
                ])

            max_gain_batch_gain += gain_or_loss
            max_gain_batch_quantity += link_quantity
            
            if target_quantity <= 0:
                sell_fully_linked_max_profit = True
                break


        ## Batches with long requirement
        target_quantity = potential_sale_quantity

        # Min Gain Long Batch
        linkable_buys_long.sort(key=lambda trans: trans.usd_spot, reverse=True)
        
        for trans in linkable_buys_long:
            buy_unlinked_quantity = trans.unlinked_quantity
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                link_quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                link_quantity = buy_unlinked_quantity

            target_quantity -= link_quantity

            cost_basis = link_quantity * float(trans.usd_spot)
            proceeds = link_quantity * potential_sale_usd_spot
            gain_or_loss = proceeds - cost_basis

            if abs(gain_or_loss) < 0.01:
                continue

            min_gain_long_batch_gain += gain_or_loss
            min_gain_long_batch_quantity += link_quantity

            min_gain_long_batch.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                link_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(proceeds),
                "${:,.2f}".format(cost_basis),
                "${:,.2f}".format(gain_or_loss)
                ])
            
            if target_quantity <= 0:
                sell_fully_linked_min_profit = True
                break

        # Max Gain Long Batch
        target_quantity = potential_sale_quantity
        
        # Sort by profit reversed
        linkable_buys_long.sort(key=lambda trans: trans.usd_spot)
        
        for trans in linkable_buys_long:
            buy_unlinked_quantity = trans.unlinked_quantity
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                link_quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                link_quantity = buy_unlinked_quantity

            target_quantity -= link_quantity
            
            cost_basis = link_quantity * float(trans.usd_spot)
            proceeds = link_quantity * potential_sale_usd_spot
            gain_or_loss = proceeds - cost_basis

            if abs(gain_or_loss) < 0.01:
                continue

            max_gain_long_batch.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                link_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(proceeds),
                "${:,.2f}".format(cost_basis),
                "${:,.2f}".format(gain_or_loss)
                ])

            max_gain_long_batch_gain += gain_or_loss
            max_gain_long_batch_quantity += link_quantity
            
            if target_quantity <= 0:
                sell_fully_linked_max_profit = True
                break


        ## Batches with Short Requirement
        target_quantity = potential_sale_quantity

        # Min Gain short Batch
        linkable_buys_short.sort(key=lambda trans: trans.usd_spot, reverse=True)
        
        for trans in linkable_buys_short:
            buy_unlinked_quantity = trans.unlinked_quantity
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                link_quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                link_quantity = buy_unlinked_quantity

            target_quantity -= link_quantity

            cost_basis = link_quantity * float(trans.usd_spot)
            proceeds = link_quantity * potential_sale_usd_spot
            gain_or_loss = proceeds - cost_basis

            if abs(gain_or_loss) < 0.01:
                continue

            min_gain_short_batch_gain += gain_or_loss
            min_gain_short_batch_quantity += link_quantity

            min_gain_short_batch.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                link_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(proceeds),
                "${:,.2f}".format(cost_basis),
                "${:,.2f}".format(gain_or_loss)
                ])
            
            if target_quantity <= 0:
                sell_fully_linked_min_profit = True
                break

        # Max Gain short Batch
        target_quantity = potential_sale_quantity
        
        # Sort by profit reversed
        linkable_buys_short.sort(key=lambda trans: trans.usd_spot)
        
        for trans in linkable_buys_short:
            buy_unlinked_quantity = trans.unlinked_quantity
            
            # Determine max link quantity
            if target_quantity <= buy_unlinked_quantity:
                link_quantity = target_quantity
            
            elif target_quantity >= buy_unlinked_quantity:
                link_quantity = buy_unlinked_quantity

            target_quantity -= link_quantity
            
            cost_basis = link_quantity * float(trans.usd_spot)
            proceeds = link_quantity * potential_sale_usd_spot
            gain_or_loss = proceeds - cost_basis

            if abs(gain_or_loss) < 0.01:
                continue

            max_gain_short_batch.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                link_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(proceeds),
                "${:,.2f}".format(cost_basis),
                "${:,.2f}".format(gain_or_loss)
                ])

            max_gain_short_batch_gain += gain_or_loss
            max_gain_short_batch_quantity += link_quantity
            
            if target_quantity <= 0:
                sell_fully_linked_max_profit = True
                break

    # Get Unlinkable 
    unlinkable_transactions = []
    unlinkable_table_data = []
    for trans in transactions:

        # Don't show if different Asset types
        if sell_obj.symbol != trans.symbol:
            continue       

        # Don't show if same type
        if trans.trans_type == sell_obj.trans_type:
            continue   

        # Don't show if already linked
        if trans.name in other_transactions:
            continue 

        # Determine Buy and Sell Objects
        if sell_obj.trans_type == "sell" and trans.trans_type == "buy":
            
            sell_obj = sell_obj
            buy_obj = trans

        elif sell_obj.trans_type == "buy" and trans.trans_type == "sell":
            sell_obj = trans
            buy_obj = sell_obj

        # Don't show if time problem
        if sell_obj.trans_type == "sell":
            if sell_obj.time_stamp < trans.time_stamp: 
                continue
        
        # Don't show if 0.0 unlinked quantity
        if trans.unlinked_quantity <= 0:
            unlinkable_transactions.append(trans)

    # Create unlinkable Table Data 
    for trans in unlinkable_transactions:
        # Determine Buy and Sell Objects
        if sell_obj.trans_type == "sell" and trans.trans_type == "buy":
            
            sell_obj = sell_obj
            buy_obj = trans

        elif sell_obj.trans_type == "buy" and trans.trans_type == "sell":
            sell_obj = trans
            buy_obj = sell_obj

        # Determine max link quantity
        if sell_obj.unlinked_quantity <= buy_obj.unlinked_quantity:
            quantity = sell_obj.unlinked_quantity
        
        elif sell_obj.unlinked_quantity >= buy_obj.unlinked_quantity:
            quantity = buy_obj.unlinked_quantity

        # Determine link profitability
        if trans.unlinked_quantity != 0 and trans.unlinked_quantity < 0.00000009:
            unlinked_quantity = "less than 0.00000009"
        else:
            unlinked_quantity = trans.unlinked_quantity

        unlinkable_table_data.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot),      
        ])




    data_dict = {}
    data_dict['min_links_batch'] = min_links_batch
    data_dict['min_links_batch_text'] = f"Total Quantity: {min_links_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(min_links_batch_gain)} "

    data_dict['min_gain_batch'] = min_gain_batch
    data_dict['min_gain_batch_text'] = f"Total Quantity: {min_gain_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(min_gain_batch_gain)}"
    
    data_dict['min_gain_long_batch'] = min_gain_long_batch
    data_dict['min_gain_long_batch_text'] = f"Total Quantity: {min_gain_long_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(min_gain_long_batch_gain)}"

    data_dict['min_gain_short_batch'] = min_gain_short_batch
    data_dict['min_gain_short_batch_text'] = f"Total Quantity: {min_gain_short_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(min_gain_short_batch_gain)}"


    data_dict['max_gain_batch'] = max_gain_batch
    data_dict['max_gain_batch_text'] = f"Total Quantity: {max_gain_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(max_gain_batch_gain)}"

    data_dict['max_gain_long_batch'] = max_gain_long_batch
    data_dict['max_gain_long_batch_text'] = f"Total Quantity: {max_gain_long_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(max_gain_long_batch_gain)}"

    data_dict['max_gain_short_batch'] = max_gain_short_batch
    data_dict['max_gain_short_batch_text'] = f"Total Quantity: {max_gain_long_batch_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or Loss: {'${:,.2f}'.format(max_gain_short_batch_gain)}"

    
    data_dict['linked'] = linked_table_data
    data_dict['linkable'] = linkable_table_data
    data_dict['unlinkable'] = unlinkable_table_data
    
    

    return jsonify(data_dict)


@blueprint.route('/link_button', methods=['POST'])
@login_required
def link_button():
    
    # print(request.json)
    
    transactions = current_app.config['transactions']
    
    # Get selected Trans Object
    sell_data = request.json['sell_data']
    buy_data = request.json['buy_data']
    
    # Get Sell Object 
    symbol = sell_data[1]
    sell_time_stamp_str = sell_data[2]
    sell_time_stamp = dateutil.parser.parse(sell_time_stamp_str)
    sell_quantity = sell_data[3]
    sell_usd_spot = sell_data[5]


    sell_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='sell', quantity=sell_quantity, time_stamp=sell_time_stamp)
    
    # Get Buy Object
    buy_time_stamp_str = buy_data[2]
    buy_time_stamp = dateutil.parser.parse(buy_time_stamp_str)
    buy_quantity = buy_data[3]
    link_quantity = buy_data[5]

    
    buy_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='buy', quantity=buy_quantity, time_stamp=buy_time_stamp)

  
    if sell_obj and buy_obj:
        sell_obj.link_transaction(buy_obj, link_quantity)
        transactions.save(description="Manually Added Link")

    else:
        print(f"No Link was added because sell {type(sell_obj)} or buy {type(buy_obj)} was not found")

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
        # print(request.json)

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
        
    # print(request.json)
    
    if 'asset' in request.json:
        asset = request.json['asset'][0]
    else:
        asset = None

    algo_type = request.json['algo']

    transactions.auto_link(asset=asset, algo=algo_type)

    if algo_type == "fifo":
        transactions.auto_link(asset=asset, algo=algo_type)
        transactions.save(description="Auto Linked with FIFO")

    elif algo_type == "filo":
        transactions.auto_link(asset=asset, algo=algo_type)
        transactions.save(description="Auto Linked with FILO")


    return jsonify(f"Auto Link using {algo_type} Successful!")


@blueprint.route('/auto_link_pre_check', methods=['POST'])
@login_required
def auto_link_pre_check():
    
    # print(request.json)
    
    data = {}
    
    asset = request.json['row_data'][0]

    transactions = current_app.config['transactions']

    auto_link_failures = transactions.auto_link(asset=asset, algo='fifo', pre_check=True)
    
    auto_link_failures.extend(transactions.auto_link(asset=asset, algo='filo', pre_check=True))

    auto_link_check_failed = False

    if len(auto_link_failures) > 0:
        auto_link_check_failed = True
        for i in auto_link_failures:
            print(i)


    sells = []
    buys = []
    
    sold = 0.0
    bought = 0.0
    

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
            if buy.time_stamp > sell.time_stamp and (sold_to_date - bought_to_date) > 0.000000009:
                
                is_greater = True
                break

            else:
                bought_to_date += buy.quantity

    message = ""
    if bought >= sold:
        message += "Check Passed: More Buys than Sells"
        
        if is_greater is True:
            message += f"<br> Check Failed: At sell timestamp [{latest_sell_time_stamp}] Buy Quantity [{bought_to_date}] can no longer cover Sell Quantity [{sold_to_date}] "
            message += f"<br> You can track down the discrepency and add [{sold_to_date - bought_to_date}] in buys manually or by converting receives to buys before [{latest_sell_time_stamp}]."
            message += "<br> If you continue you will have sells not fully linked (unlinked quantity) to buys. Full proceeds on quantity unlinked of sell will be used for Gain/Loss."
       
        else:
            message += "<br> Check Passed: Individual sells can be covered by an earlier buy"

            if auto_link_check_failed is True:
                message += "<br> Check Failed: Sell will not be fully linked using Auto Link"
                for i in auto_link_failures:

                    message += f"<br> {i}"
    
    else:
        message += "Check Failed: More Sells than buys"

        
    data['message'] = message

    return jsonify(data)


@blueprint.route('/buys_to_lost', methods=['POST'])
@login_required
def buys_to_lost():
   
    transactions = current_app.config['transactions']

    # print(request.json)

    asset = request.json['asset'][0]
    amount = float(request.json['quantity'])

    transactions.convert_buys_to_lost(asset=asset, amount=amount)

    transactions.save(description="Converted Buys to Lost")

    return jsonify("Yess")
    

@blueprint.route('/hodl_info', methods=['POST'])
@login_required
def hodl_info():
    asset_symbol = request.json['asset'][0]
    hodl = float(request.json['quantity'])

    transactions = current_app.config['transactions']

    for a in transactions.asset_objects:
        # print(a.symbol, asset_symbol)
        if a.symbol != asset_symbol:
            continue 

        a.hodl = hodl
        # print(f"Setting HODL for {a.symbol} is {a.hodl}")

    for a in transactions.asset_objects:
        # print(f"Asset Object symbol {a.symbol} Asset {asset_symbol} HODL {a.hodl}")
        if a.hodl is not None:
            hodl = a.hodl
            # print(f"Asset Object symbol {a.symbol} Asset {asset_symbol} HODL {a.hodl}")

    transactions.save(description=f"Added HODL for {asset_symbol}")

    return jsonify("HODL Accepted")


@blueprint.route('/sends_to_sells', methods=['POST'])
@login_required
def sends_to_sells():
    
    transactions = current_app.config['transactions']
    

    asset = request.json['asset'][0]
    amount_to_convert = float(request.json['quantity'])

    quantity_of_sends_converted_to_sells = None
    number_of_converted_transactions = None

    for a in transactions.asset_objects:
        if a.symbol != asset:
            continue 
        
        result_str = transactions.convert_sends_to_sells(asset=asset, amount_to_convert=amount_to_convert)

        transactions.save(description="Converted Sends to sells")

    return jsonify(result_str)



@blueprint.route('/receive_to_buy', methods=['POST'])
@login_required
def receive_to_buy():
    
    transactions = current_app.config['transactions']
    
    asset = request.json['asset'][0]
    amount_to_convert = float(request.json['quantity'])
    
    for a in transactions.asset_objects:
        if a.symbol != asset:
            continue 
        
        transactions.convert_receives_to_buys(asset=asset, amount_to_convert=amount_to_convert)

        transactions.save(description="Converted receives to buys")

        # current_app.config['transactions'] = transactions.load()

    return jsonify("Yess")


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
        ["Profit / Loss in USD* (Valid when Quantity Sold Unlinked is 0)", asset_stats['total_profit_loss']],
    ]

    # Get Linked Table Data
    linked_table_data = get_linked_table_data(transactions, asset, date_range)

    # Get Sells Table Data 
    sells_table_data = get_sells_trans_table_data_range(transactions, asset, date_range)

    sells_unlinked_remaining = []
    if request.json['unlinked_remaining']:
        for sell in sells_table_data:
            if type(sell[4]) is str:
                continue

            if sell[4] > 0.000000009:
                sells_unlinked_remaining.append(sell)

        sells_table_data = sells_unlinked_remaining

    # Get Buys Table Data
    buys_table_data = get_buys_trans_table_data_range(transactions, asset, date_range)

    # Get All Links Table Data
    all_links_table_data = get_all_links_table_data(transactions, asset)


    data_dict = {}

    data_dict['all_links'] = all_links_table_data
    data_dict['detailed_stats'] = detailed_stats
    data_dict['linked'] = linked_table_data
    data_dict['sells'] = sells_table_data
    data_dict['buys'] = buys_table_data
    
    return jsonify(data_dict)



@blueprint.route('/add_transactions_selected_asset',  methods=['POST'])
@login_required
def add_transactions_selected_asset():


    # print(request.json)

    transactions = current_app.config['transactions']

    date_range = {
        'start_date': '',
        'end_date': ''
    }

    asset = request.json['row_data'][0]

    # Get date range of transactions
    date_range = get_transactions_date_range(transactions, date_range)

     # Get Sells Table Data 
    sells_table_data = get_sells_trans_table_data_range(transactions, asset, date_range)

    # Get Buys Table Data
    buys_table_data = get_buys_trans_table_data_range(transactions, asset, date_range)

    # Get Sends Table Data
    sends_table_data = get_sends_trans_table_data_range(transactions, asset, date_range)

    # Get Receives Table Data
    receives_table_data = get_receives_trans_table_data_range(transactions, asset, date_range)

    data_dict = {}
    data_dict['sells'] = sells_table_data
    data_dict['buys'] = buys_table_data
    data_dict['sends'] = sends_table_data
    data_dict['receives'] = receives_table_data

    return jsonify(data_dict)


@blueprint.route('/delete_transactions',  methods=['POST'])
@login_required
def delete_transactions():

    asset = request.json['asset'][0]
    trans_type = request.json['type']

    transactions = current_app.config['transactions']

    # Get selected Trans Object
    row_data = request.json['row_data']
    symbol = row_data[1]
    time_stamp_str = row_data[2]
    time_stamp = dateutil.parser.parse(time_stamp_str)
    quantity = row_data[3]
    usd_spot = row_data[5]

    trans_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type=trans_type, quantity=quantity, time_stamp=time_stamp)

    if trans_obj is not None:
        
        transactions.transactions.remove(trans_obj)

        transactions.save(f'Deleted {asset} {trans_type} {quantity}')

        return jsonify(f'Deleted {asset} {trans_type} {quantity} on {time_stamp}')
    
    else:

        return jsonify(f'Transaction Not Found! {asset} {trans_type} {quantity}')



@blueprint.route('/buy_convert',  methods=['POST'])
@login_required
def buy_convert():

    # print(request.json)


    transactions = current_app.config['transactions']

    # Get selected Trans Object
    row_data = request.json['row_data']
    symbol = row_data[1]
    time_stamp_str = row_data[2]
    time_stamp = dateutil.parser.parse(time_stamp_str)
    quantity = row_data[3]
    usd_spot = row_data[5]

    trans_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='buy', quantity=quantity, time_stamp=time_stamp)

    if trans_obj is not None:

        if len(trans_obj.links) > 0:
            return jsonify(f"{trans_obj.trans_type} has {len(trans_obj.links)} links cannot convert!")
        
        else:
            conversion = Conversion(input_trans_type='buy', 
                                    output_trans_type='lost', 
                                    input_symbol=trans_obj.symbol, 
                                    input_quantity=trans_obj.quantity, 
                                    input_time_stamp=trans_obj.time_stamp, 
                                    input_usd_spot=trans_obj.usd_spot, 
                                    input_usd_total=trans_obj.usd_total, 
                                    reason="Converted Buy to Lost", 
                                    source=f"{trans_obj.source} Converted in Gainz App")

            transactions.conversions.append(conversion)
            
            transactions.transactions.remove(trans_obj)

            transactions.save(description=f"Converted {symbol} Buy to Lost")

            return jsonify(f'Converted Buy to Lost {trans_obj.name}')



@blueprint.route('/receive_convert',  methods=['POST'])
@login_required
def receive_convert():

    transactions = current_app.config['transactions']

    table_data = request.json['table_data']

    for row_data in table_data.values():
        if type(row_data) != list:
            continue

        if type(row_data[0]) != str:
            continue

        # Get selected Trans Object
        symbol = row_data[1]
        time_stamp_str = row_data[2]
        time_stamp = dateutil.parser.parse(time_stamp_str)
        quantity = row_data[3]
        usd_spot = row_data[5]

        receive_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='receive', quantity=quantity, time_stamp=time_stamp)

        if receive_obj is not None:

            buy = Buy(symbol=symbol, quantity=receive_obj.quantity, time_stamp=receive_obj.time_stamp, usd_spot=receive_obj.usd_spot, source="Gainz App Receive to Buy")
                
            conversion = Conversion(input_trans_type='receive', 
                                    output_trans_type='buy', 
                                    input_symbol=receive_obj.symbol, 
                                    input_quantity=receive_obj.quantity, 
                                    input_time_stamp=receive_obj.time_stamp, 
                                    input_usd_spot=receive_obj.usd_spot, 
                                    input_usd_total=receive_obj.usd_total, 
                                    reason="Converted Receive to Buy", 
                                    source=f"{receive_obj.source} Converted in Gainz App")

            transactions.conversions.append(conversion)
            
            transactions.transactions.append(buy)

            transactions.transactions.remove(receive_obj)

    transactions.save(description=f"Converted receive(s) to buy(s)")

    return jsonify(f'Converted Receive(s) to Buy {receive_obj.name}')


@blueprint.route('/send_convert',  methods=['POST'])
@login_required
def send_convert():

    # print(request.json)

    transactions = current_app.config['transactions']

    # Get selected Trans Object
    row_data = request.json['row_data']
    symbol = row_data[1]
    time_stamp_str = row_data[2]
    time_stamp = dateutil.parser.parse(time_stamp_str)
    quantity = row_data[3]
    usd_spot = row_data[5]

    send_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='send', quantity=quantity, time_stamp=time_stamp)

    if send_obj is not None:

            sell = Sell(symbol=symbol, quantity=send_obj.quantity, time_stamp=send_obj.time_stamp, usd_spot=send_obj.usd_spot, source="Gainz App Send to Sell")
                
            conversion = Conversion(input_trans_type='send', 
                                    output_trans_type='sell', 
                                    input_symbol=send_obj.symbol, 
                                    input_quantity=send_obj.quantity, 
                                    input_time_stamp=send_obj.time_stamp, 
                                    input_usd_spot=send_obj.usd_spot, 
                                    input_usd_total=send_obj.usd_total, 
                                    reason="Converted Send to Sell", 
                                    source=f"{send_obj.source} Converted in Gainz App")

            transactions.conversions.append(conversion)
            
            transactions.transactions.append(sell)

            transactions.transactions.remove(send_obj)

            transactions.save(description=f"Converted {symbol} Send to Sell")

            return jsonify(f'Converted Receive to Buy {send_obj.name}')



@blueprint.route('/link_batch',  methods=['POST'])
@login_required
def link_batch():

    # print(request.json)
    transactions = current_app.config['transactions']
    
    # Get selected Trans Object
    sell_data = request.json['sell_data']
    buy_data = request.json['buy_data']
    
    # Get Sell Object 
    symbol = sell_data[1]
    time_stamp_str = sell_data[2]
    time_stamp = dateutil.parser.parse(time_stamp_str)
    quantity = sell_data[3]


    sell_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='sell', quantity=quantity, time_stamp=time_stamp)
    
    for row_data in buy_data.values():
        if type(row_data) != list:
            continue

        if type(row_data[0]) != str:
            continue

        print(row_data)

    for row_data in buy_data.values():
        if type(row_data) != list:
            continue

        if type(row_data[0]) != str:
            continue

        # Get Buy Object
        symbol = row_data[1]
        time_stamp_str = row_data[2]
        time_stamp = dateutil.parser.parse(time_stamp_str)
        buy_quantity = row_data[3]
        link_quantity = row_data[5]

        buy_obj = get_trans_obj_from_table_data(transactions=transactions, symbol=symbol, trans_type='buy', quantity=buy_quantity, time_stamp=time_stamp)

        if sell_obj and buy_obj:
            sell_obj.link_transaction(buy_obj, link_quantity)
        else:
            print(f"Sell/Buy or Both were not found Sell [{sell_obj}] Buy [{buy_obj}]")
    
    transactions.save(description=f"linked batch of buys to {sell_obj}")

    
    return jsonify('all good!')


@blueprint.route('/delete_link_from_linked',  methods=['POST'])
@login_required
def delete_link_from_linked():
    
    transactions = current_app.config['transactions']

    links_to_delete = request.json['links']

    links = transactions.links

    for v in links_to_delete.values():
        if type(v) != list:
            continue

        if type(v[0]) != str:
            continue
        
        print(v)

        sell_time_stamp =  dateutil.parser.parse(request.json['sell_time_stamp'])
        
        symbol = request.json['symbol'] # incorportate in matched link!


        buy_time_stamp = dateutil.parser.parse(v[0])
        link_quantity = v[5]

        print(link_quantity)

        matched_link = [link for link in links if link.quantity == link_quantity and link.buy.time_stamp == buy_time_stamp and link.sell.time_stamp == sell_time_stamp][0]

        for link in matched_link.buy.links:
            if link in matched_link.buy.links:
                matched_link.buy.links.remove(link)

        for link in matched_link.sell.links:
            if link in matched_link.sell.links:
                matched_link.sell.links.remove(link)

        del(matched_link)

    transactions.save("Deleted Link(s)")

    return jsonify("Deleted Link(s)")





@blueprint.route('/delete_link',  methods=['POST'])
@login_required
def delete_link():
    
    transactions = current_app.config['transactions']

    links_to_delete = request.json['links']

    links = transactions.links

    for v in links_to_delete.values():
        if type(v) != list:
            continue

        if type(v[0]) != str:
            continue
        
        print(v)
        symbol = v[0]
        buy_time_stamp = dateutil.parser.parse(v[1])
        sell_time_stamp = dateutil.parser.parse(v[2])
        link_quantity = v[5]

        print(link_quantity)

        matched_link = [link for link in links if link.quantity == link_quantity and link.buy.time_stamp == buy_time_stamp and link.sell.time_stamp == sell_time_stamp][0]

        for link in matched_link.buy.links:
            if link in matched_link.buy.links:
                matched_link.buy.links.remove(link)

        for link in matched_link.sell.links:
            if link in matched_link.sell.links:
                matched_link.sell.links.remove(link)

        del(matched_link)

    transactions.save("Deleted Link(s)")

    return jsonify("Deleted Link(s)")


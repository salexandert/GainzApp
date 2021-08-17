@blueprint.route('/selected_asset',  methods=['POST'])
@login_required
def selected_asset():
    # Populate Links, Sells, Buys Tables based on selected asset from stats table

    print(request.json)

    transactions = current_app.config['transactions']

    asset = request.json['row_data'][0]

    # Selected Asset
    row_data = request.json['row_data']
    potential_sale_usd_spot = float(request.json['usd_spot'].replace(',', ''))
    print(request.json['quantity'])
    print(type(request.json['quantity']))

    
    # calculate quantity 
    if request.json['quantity'] == '':
        total_in_usd = float(request.json['total_in_usd'].replace(',', ''))
        potential_sale_quantity = 1 * (total_in_usd / potential_sale_usd_spot)

    else:
        potential_sale_quantity = float(request.json['quantity'].replace(',', ''))
        total_in_usd = (potential_sale_usd_spot * potential_sale_quantity)


    print(f" Potential Sale Quantity: [{potential_sale_quantity}]")
    print(f" Total in USD: [ ${total_in_usd} ]")

    # All Linkable Buys 
    linkable_buys = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == asset
        and (datetime.datetime.now() >= trans.time_stamp)
        and trans.unlinked_quantity > .0000001
    ]

    linkable_table_data = []
    for trans in linkable_buys:
        linkable_table_data.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(trans.usd_total),
            "${:,.2f}".format(trans.unlinked_quantity * potential_sale_usd_spot)
            ])

    # Linkable Buys Long
    linkable_buys_long = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == asset
        and (datetime.datetime.now() - trans.time_stamp).days > 365
        and trans.unlinked_quantity > .0000001
    ]

    linkable_long_table_data = []
    for trans in linkable_buys_long:
        linkable_long_table_data.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(trans.usd_total),
            "${:,.2f}".format(trans.unlinked_quantity * potential_sale_usd_spot)
            ])

    # Linkable Buys Short
    linkable_buys_short = [
    trans for trans in transactions
        if trans.trans_type == "buy"
        and trans.symbol == asset
        and (datetime.datetime.now() - trans.time_stamp).days <= 365
        and trans.unlinked_quantity > .0000001
    ]

    linkable_short_table_data = []
    for trans in linkable_buys_short:
        linkable_short_table_data.append([
            trans.source,
            trans.symbol,
            datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(trans.usd_total),
            "${:,.2f}".format(trans.unlinked_quantity * potential_sale_usd_spot)
            ])


    # Get Batches that can satify sell
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

    
    # Sort by quantity unlinked
    linkable_buys.sort(key=lambda trans: trans.unlinked_quantity, reverse=True)

    print(f" Linkable_buys unlinked_quantity of first {linkable_buys[0].unlinked_quantity}")
    print(f" Linkable_buys unlinked_quantity of last {linkable_buys[-1].unlinked_quantity}")
    
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

        min_links_profit += gain_or_loss
        min_links_quantity += link_quantity


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

        # Min Profit Batch
        target_quantity = potential_sale_quantity

        # Sort by profit
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

            min_profit_long_profit += gain_or_loss
            min_profit_long_quantity += link_quantity

            min_profit_long_batch.append([
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

        # Maximum Profit Batch
        target_quantity = potential_sale_quantity
        
        # Sort by profit reversed
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

            max_profit_batch.append([
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

            max_profit_profit += gain_or_loss
            max_profit_quantity += link_quantity
            
            if target_quantity <= 0:
                sell_fully_linked_max_profit = True
                break



    data_dict = {}
    data_dict['min_links'] = min_links_batch
    data_dict['min_links_text'] = f"Total Quantity: {min_links_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or (Loss): {'${:,.2f}'.format(min_links_profit)} "
    
    data_dict['min_profit_long'] = min_profit_long_batch
    data_dict['min_profit_long_text'] = f"Total Quantity: {min_profit_long_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or (Loss): {'${:,.2f}'.format(min_profit_long_profit)}"
    
    data_dict['max_profit_long'] = max_profit_batch
    data_dict['max_profit_long_text'] = f"Total Quantity: {max_profit_quantity} <br> Total Proceeds: {'${:,.2f}'.format(total_in_usd)} <br> Total Gain or (Loss): {'${:,.2f}'.format(max_profit_profit)}"
    
    data_dict['all_linkable_buys_datatable'] = linkable_table_data
    data_dict['potential_sale_quantity'] = potential_sale_quantity
    data_dict['total_in_usd'] = '${:,.2f}'.format(total_in_usd)


    
    return jsonify(data_dict)

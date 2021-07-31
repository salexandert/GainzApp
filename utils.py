
import datetime



def get_stats_table_data(transactions):
    # Stats Table Generation



    # Get links
    links = set([
            link 
            for trans in transactions
            for link in trans.links
            ])



    stats_table_data = []
        
    for asset in transactions.assets:
        
        total_purchased_quantity = 0.0
        total_purchased_unlinked_quantity = 0.0
        total_purchased_usd = 0.0

        total_sold_quantity = 0.0
        total_sold_unlinked_quantity = 0.0
        total_sold_usd = 0.0

        total_sent_quantity = 0.0

        profit_loss = 0.0

        for link in links:
            if link.symbol == asset:
                profit_loss += link.profit_loss

        # set profit loss to total sold if all unlinked
        if profit_loss == 0.0:
            profit_loss = total_sold_usd

        for trans in transactions:
            if trans.symbol != asset:
                continue

            if trans.trans_type.lower() == "buy":
                total_purchased_quantity += trans.quantity
                total_purchased_unlinked_quantity += trans.unlinked_quantity
                total_purchased_usd += trans.usd_total
                

            elif trans.trans_type.lower() == "sell":
                total_sold_quantity += trans.quantity
                total_sold_unlinked_quantity += trans.unlinked_quantity
                total_sold_usd += trans.usd_total
                if trans.unlinked_quantity > 0:
                    profit_loss += (trans.unlinked_quantity * trans.usd_spot)

            elif trans.trans_type.lower() == "send":
                total_sent_quantity += trans.quantity

            # print(f"Total Sold in usd: {total_sold_usd}")
            # print(f"Trans USD Total {trans.usd_total}")
        
        hodl = "N/A"
        
        for a in transactions.asset_objects:
            if a.symbol != asset:
                continue
            
            # print(f"Asset Object symbol {a.symbol} Asset {asset} HODL {a.hodl}")
            if a.hodl is not None:
                hodl = a.hodl
                # print(f"Asset Object symbol {a.symbol} Asset {asset} HODL {a.hodl}")
                                
        stats_table_data.append({   
                "symbol": f"{asset}",
                "total_purchased_quantity": total_purchased_quantity,
                "total_purchased_unlinked_quantity": total_purchased_unlinked_quantity,
                "total_purchased_usd": "${:,.2f}".format(total_purchased_usd),
                "total_sold_quantity": total_sold_quantity, 
                "total_sold_unlinked_quantity": total_sold_unlinked_quantity,
                "total_sold_usd": "${:,.2f}".format(total_sold_usd),
                "total_profit_loss": "${:,.2f}".format(profit_loss),
                "total_sent_quantity": total_sent_quantity,
                "hodl": hodl

            })
    
    return stats_table_data
        

def get_all_trans_table_data(transactions):
    all_trans_table_data = []
    for trans in transactions:
        trans_data = {}
        trans_data['name'] = trans.name
        trans_data['type'] = trans.trans_type
        trans_data['asset'] = trans.symbol
        trans_data['time_stamp'] = trans.time_stamp
        trans_data['usd_spot'] = "${:,.2f}".format(trans.usd_spot)
        trans_data['quantity'] = trans.quantity
        trans_data['unlinked_quantity'] = trans.unlinked_quantity
        trans_data['usd_total'] = "${:,.2f}".format(trans.usd_total)
        
        all_trans_table_data.append(trans_data)

    return all_trans_table_data


def td_format(td_object):
    # Used to Format Link Time Deltas
    seconds = int(td_object.total_seconds())
    periods = [
        ('year',        60*60*24*365),
        ('month',       60*60*24*30),
        ('day',         60*60*24),
        ('hour',        60*60),
        ('minute',      60),
        ('second',      1)
    ]

    strings=[]
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)




def get_linked_table_data(transactions, asset, date_range):


    if date_range:

        start_date = date_range['start_date']
        end_date = date_range['end_date']
        
    
    # Filter Transactions to date range
    filtered_transactions = []
    for trans in transactions:
        if start_date and not end_date:
            if trans.time_stamp >= start_date:
                filtered_transactions.append(trans)

        elif not start_date and end_date:
            if trans.time_stamp <= end_date:
                filtered_transactions.append(trans)

        elif start_date and end_date:
            if trans.time_stamp >= start_date and trans.time_stamp <= end_date:              
                filtered_transactions.append(trans)

    # Get links
    links = set([
            link 
            for trans in filtered_transactions
            for link in trans.links
            ])

    print(f" len of links {len(links)}")
    
    # Get linked Table Data
    linked_table_data = []
    for link in links:
        
        ## No clue why this does not work!
        # link_profit_loss = None 
        # abs_profit_loss = abs(link.profit_loss)
        # if abs_profit_loss <= .009:
        #     print( f"abs profit Loss {abs_profit_loss}" )
            
        #     link_profit_loss = "$0.00"
        # else:
        #     link_profit_loss = "${:,.2f}".format(link.profit_loss),
       
        linked_table_data.append([
            link.quantity,
            "${:,.2f}".format(link.profit_loss),
            td_format(link.hodl_duration),
            link.buy.time_stamp,
            link.buy.quantity,
            "${:,.2f}".format(link.buy.usd_total),
            link.sell.time_stamp,
            link.sell.quantity,
            "${:,.2f}".format(link.sell.usd_total),
            
        ])

    # print(linked_table_data)
    
    return linked_table_data


def get_linkable_table_data(transactions, trans1_obj):
    # Get Linkable Table Data
    linkable_table_data = []
    for trans in transactions:
        
        # Don't show if different Asset types
        if trans1_obj.symbol != trans.symbol:
            continue            

        # Don't show if 0.0 unlinked quantity WE SHOULD TEST 0 NOT 0.0 AS 0.01 ISSUE CAN ARRISE
        if trans1_obj.unlinked_quantity <= 0.0 or trans.unlinked_quantity <= 0.0:
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
            trans.name, 
            trans.trans_type.capitalize(),
            trans.symbol,
            trans.time_stamp, 
            trans.quantity,
            trans.unlinked_quantity,
            "${:,.2f}".format(trans.usd_spot), 
            "${:,.2f}".format(trans.usd_total),
            "${:,.2f}".format(profit)
            ])
    
    return linkable_table_data


def get_stats_table_data_range(transactions, date_range=None):
    # Stats Table Generation with date range

    
    if date_range:

        start_date = date_range['start_date']
        end_date = date_range['end_date']
  
                                                                                                                      
        # Filter Transactions to date range
        filtered_transactions = []
        for trans in transactions:
            if start_date and not end_date:
                if trans.time_stamp >= start_date:
                    filtered_transactions.append(trans)

            elif not start_date and end_date:
                if trans.time_stamp <= end_date:
                    filtered_transactions.append(trans)

            elif start_date and end_date:
                if trans.time_stamp >= start_date and trans.time_stamp <= end_date:              
                    filtered_transactions.append(trans)

        
        # Get links
        links = set([
                link 
                for trans in filtered_transactions
                for link in trans.links
                ])


        stats_table_data = []
            
        for asset in transactions.assets:
            
            total_purchased_quantity = 0.0
            total_purchased_unlinked_quantity = 0.0
            total_purchased_usd = 0.0

            total_sold_quantity = 0.0
            total_sold_unlinked_quantity = 0.0
            total_sold_usd = 0.0

            total_sent_quantity = 0.0

            profit_loss = 0.0

            buy_prices = []
            sell_prices = []
                        
            average_hodl_length = 0.0

            num_buys = 0
            num_sells = 0
            num_sends = 0

            num_links = 0

            for link in links:
                if link.symbol == asset:
                    num_links += 1
                    profit_loss += link.profit_loss


            for trans in filtered_transactions:
                if trans.symbol == asset:

                    if trans.trans_type.lower() == "buy":
                        num_buys += 1
                        total_purchased_quantity += trans.quantity
                        total_purchased_unlinked_quantity += trans.unlinked_quantity
                        total_purchased_usd += trans.usd_total
                        buy_prices.append(trans.usd_total)
                        

                    elif trans.trans_type.lower() == "sell":
                        num_sells += 1
                        total_sold_quantity += trans.quantity
                        total_sold_unlinked_quantity += trans.unlinked_quantity
                        total_sold_usd += trans.usd_total

                        if trans.unlinked_quantity > 0:
                            profit_loss += (trans.usd_spot * trans.unlinked_quantity)

                        sell_prices.append(trans.usd_total)

                    elif trans.trans_type.lower() == "send":
                        num_sends += 1
                        total_sent_quantity += trans.quantity
            
            if len(buy_prices) > 0:
                average_buy_price = total_purchased_usd / total_purchased_quantity
            
            else:
                average_buy_price = 0.0
            
            if len(sell_prices) > 0:
                average_sell_price = total_sold_usd / total_sold_quantity
            
            else:
                average_sell_price = 0.0

            hodl = "N/A"
        
            for a in transactions.asset_objects:
                if a.symbol != asset:
                    continue
                
                # print(f"Asset Object symbol {a.symbol} Asset {asset} HODL {a.hodl}")
                if a.hodl is not None:
                    hodl = a.hodl
                    # print(f"Asset Object symbol {a.symbol} Asset {asset} HODL {a.hodl}")

            stats_table_data.append({   
                    "symbol": f"{asset}",
                    "total_purchased_quantity": total_purchased_quantity,
                    "total_purchased_unlinked_quantity": total_purchased_unlinked_quantity,
                    "total_purchased_usd": "${:,.2f}".format(total_purchased_usd),
                    
                    "total_sold_quantity": total_sold_quantity, 
                    "total_sold_unlinked_quantity": total_sold_unlinked_quantity,
                    "total_sold_usd": "${:,.2f}".format(total_sold_usd),
                    "total_profit_loss": "${:,.2f}".format(profit_loss),
                    "total_sent_quantity": total_sent_quantity,

                    "num_buys": num_buys,
                    "num_sells": num_sells,

                    "num_links": num_links,

                    "average_buy_price": "${:,.2f}".format(average_buy_price),
                    "average_sell_price": "${:,.2f}".format(average_sell_price),
                    "hodl": hodl
                    
                })
    
    return stats_table_data
   

def get_all_trans_table_data_range(transactions, asset, date_range):
    
    if date_range:

        start_date = date_range['start_date']
        end_date = date_range['end_date']
        
                                                                    
                                                                        
        # Filter Transactions to date range
        filtered_transactions = []
        for trans in transactions:
            if start_date and not end_date:
                if trans.time_stamp >= start_date:
                    filtered_transactions.append(trans)

            elif not start_date and end_date:
                if trans.time_stamp <= end_date:
                    filtered_transactions.append(trans)

            elif start_date and end_date:
                if trans.time_stamp >= start_date and trans.time_stamp <= end_date:              
                    filtered_transactions.append(trans)


    all_trans_table_data = []
    for trans in filtered_transactions:
        
        all_trans_table_data.append([
            trans.name,
            trans.trans_type,
            trans.symbol,
            trans.time_stamp,
            trans.quantity,
            "${:,.2f}".format(trans.usd_spot),
            "${:,.2f}".format(trans.usd_total)
        ])
        

    return all_trans_table_data


def get_transactions_date_range(transactions, date_range):

    
    if date_range['start_date'] == '':
        first_time_stamps = transactions.first_transaction_date()

        first_time_stamp = None
        for time_stamp in first_time_stamps.values():
            if first_time_stamp is None:
                first_time_stamp = time_stamp
                
            if time_stamp < first_time_stamp:
                first_time_stamp = time_stamp 

        date_range['start_date'] = first_time_stamp

    else:
        date_range['start_date'] = datetime.datetime.strptime(date_range['start_date'], "%Y-%m-%d %H:%M")
        

    if date_range['end_date'] == '':
        last_time_stamps = transactions.last_transaction_date()

        last_time_stamp = None
        for time_stamp in last_time_stamps.values():
            if last_time_stamp is None:
                last_time_stamp = time_stamp
                continue
                        
            if time_stamp > last_time_stamp:
                last_time_stamp = time_stamp

        date_range['end_date'] = last_time_stamp
    
    else:
        date_range['end_date'] = datetime.datetime.strptime(date_range['end_date'], "%Y-%m-%d %H:%M")

    return date_range



def get_sells_trans_table_data_range(transactions, asset, date_range):
    
    if date_range:

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


    table_data = []
    for trans in filtered_transactions:
        if trans.trans_type == "sell":

            trans.update_linked_transactions()
        
            table_data.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(trans.usd_total)
            ])
        

    return table_data


def get_buys_trans_table_data_range(transactions, asset, date_range):
    
    if date_range:

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


    table_data = []
    for trans in filtered_transactions:
        if trans.trans_type == "buy":
        
            table_data.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(trans.usd_total)
            ])
        

    return table_data


def get_sends_trans_table_data_range(transactions, asset, date_range):
    
    if date_range:

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


    table_data = []
    for trans in filtered_transactions:
        if trans.trans_type == "send":
        
            table_data.append([
                trans.source,
                trans.symbol,
                datetime.datetime.strftime(trans.time_stamp, "%Y-%m-%d %H:%M:%S"),
                trans.quantity,
                trans.unlinked_quantity,
                "${:,.2f}".format(trans.usd_spot),
                "${:,.2f}".format(trans.usd_total)
            ])
        

    return table_data
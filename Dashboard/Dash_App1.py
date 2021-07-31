# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from transaction import Sell
from Dashboard.Dash_fun import apply_layout_with_auth
from dash import Dash
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components.Button import Button
from dash_html_components.Div import Div
import dash_table
from dash_table import DataTable, FormatTemplate
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import json
# from sklearn import preprocessing
from time import strftime
import numpy as np
from ast import literal_eval
import os
import locale
locale.setlocale( locale.LC_ALL, '' )

from transactions import Transactions

money = FormatTemplate.money(2)

colors = {
    'buy': 'green',
    'sell': 'red',
    'send': 'yellow'
}

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}



app = dash.Dash(__name__)
    
transactions = Transactions()


layout = html.Div(className="right_col", role="main", children=[
    html.Div(className="", children=[

        html.Div(className="row", children=[
            html.Div(className="col-md-12 col-sm-12", children=[
                html.Div(className="x_panel", children=[
                    html.Div(className="x_title", children=[
                        html.H2("Manually Add Transactions"),
                        html.Ul(className="nav navbar-right panel_toolbox", children=[
                            html.Li(html.A(className="collapse-link", children=html.I(className="fa fa-cevron-up"))),
                            html.Li(html.A(className="dropdown", children=[
                                html.A(className="dropdown-toggle")
                            ]))
                        ])

                    ])
                ])
            ])
        ])
    ])
]

)










url_base = '/dash/app1/'

def Add_Dash(server):
    app = Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)


    @app.callback(
        Output('asset-checklist', 'options'),
        Input('view-dropdown', 'value'))
    def update_asset_checklist(view_value):
        
        assets = set()
        
        for trans in transactions:
            assets.add(trans.symbol)

        options = []

        for asset in assets:
            options.append({'label': asset, 'value': asset})

        return options


    # view-checklist Select All Value
    @app.callback(
        Output('view-checklist', 'value'),
        Input('options_select_all', 'n_clicks'),
        State('view-checklist', 'options'),
        State('view-checklist', 'value')
    )
    def view_select_all_none(n_clicks, options, values):
        if n_clicks == 0:
            raise PreventUpdate

        select_all = False

        for option in options:
            if option['value'] not in values:
                select_all = True
            
        if select_all:
            all_or_none = [option["value"] for option in options]
        else:
            all_or_none = []

        return all_or_none

    # Asset Select All Button
    @app.callback(
        Output('asset-checklist', 'value'),
        Input('select_all', 'n_clicks'),
        State('asset-checklist', 'options'),
        State('asset-checklist', 'value')
    )
    def select_all_none(n_clicks, options, values):
        if n_clicks == 0:
            raise PreventUpdate
        
        select_all = False

        for option in options:
            if option['value'] not in values:
                select_all = True
            
        if select_all:
            all_or_none = [option["value"] for option in options]
        else:
            all_or_none = []

        return all_or_none



    @app.callback(
        Output('table1-text', 'children'),
        Input('main_scatter', 'clickData')
    )
    def table1_text_update(clickData):
        if clickData is None:
            raise PreventUpdate

        return "Selected Transaction"

    # Output to stats-table
    @app.callback(
        Output('stats-table', 'data'),
        Input('view-dropdown', 'value'),
        Input('asset-checklist', 'value'),
        Input('view-checklist', 'value')
    )
    def update_stats(viewValue, assetValues, viewValues):

        filtered_transactions = transactions.filter(symbols=assetValues, options=viewValues)
        
        # quantity in view = buys - sells
        total_purchased_quantity = 0.0
        total_purchased_unlinked_quantity = 0.0
        total_purchased_usd = 0.0

        total_sold_quantity = 0.0
        total_sold_unlinked_quantity = 0.0
        total_sold_usd = 0.0

        total_profit_loss = 0.0

        # Get links
        links = set([
                link 
                for trans in transactions
                for link in trans.links
                ])

        # sum total profit loss of links
        for link in links:
            total_profit_loss += link.profit_loss


        # Set Profit loss to max if no links
        if len(links) == 0:
            total_profit_loss = total_sold_usd

        table_data = []
            
        for asset in transactions.assets:
            
            total_purchased_quantity = 0.0
            total_purchased_unlinked_quantity = 0.0
            total_purchased_usd = 0.0

            total_sold_quantity = 0.0
            total_sold_unlinked_quantity = 0.0
            total_sold_usd = 0.0

            profit_loss = 0.0

            for link in links:
                if link.symbol == asset:
                    profit_loss += link.profit_loss

            # set profit loss to total sold if all unlinked
            if profit_loss == 0.0:
                profit_loss = total_sold_usd

            for trans in transactions:
                if trans.symbol == asset:
                    if trans.trans_type == "buy":
                        total_purchased_quantity += trans.quantity
                        total_purchased_unlinked_quantity += trans.unlinked_quantity
                        total_purchased_usd += trans.usd_total
                        

                    elif trans.trans_type == "sell":
                        total_sold_quantity += trans.quantity
                        total_sold_unlinked_quantity += trans.unlinked_quantity
                        total_sold_usd += trans.usd_total
            
                
            table_data.append({   
                    "symbol": f"{asset}",
                    "total_purchased_quantity": total_purchased_quantity,
                    "total_purchased_unlinked_quantity": total_purchased_unlinked_quantity,
                    "total_purchased_usd": total_purchased_usd,
                    
                    "total_sold_quantity": total_sold_quantity, 
                    "total_sold_unlinked_quantity": total_sold_unlinked_quantity,
                    "total_sold_usd": total_sold_usd,
                    "total_profit_loss": profit_loss

                })
            

        return table_data



    # Used for any modification of model
    @app.callback(
        Output('view-dropdown', 'value'),
        Input('link-button', 'n_clicks'),
        Input('fifo_button', 'n_clicks'),
        Input('filo_button', 'n_clicks'),
        Input('export_button', 'n_clicks'),
        Input('upload-data', 'contents'),
        State('main_scatter', 'selectedData'),
        State('table1', "derived_virtual_data"),
        State('table1', "derived_virtual_selected_rows"),
        State('linkable_table', "derived_virtual_data"),
        State('linkable_table', "derived_virtual_selected_rows"),
        State('view-dropdown', 'value'),
        State('upload-data', 'filename'),
        State('asset-checklist', 'value'),
        State('view-checklist', 'value'))
    def change_view(
                        n_clicks, 
                        fifo_n_clicks, 
                        filo_n_clicks,
                        export_n_clicks,
                        contents,
                        selectedData, 
                        rows1, 
                        derived_virtual_selected_rows1, 
                        rows2,
                        derived_virtual_selected_rows2,
                        viewValue,
                        filename,
                        assetValues,
                        viewValues
                    ):
        
        ctx = dash.callback_context
        print(f"Change View was triggered by {ctx.triggered[0]['prop_id']}")    


        filtered_transactions = transactions.filter(symbols=assetValues, options=viewValues)

        # Upload New Data
        if ctx.triggered[0]['prop_id'] == 'upload-data.contents':
            if contents is not None:

                if viewValue is None:
                    pass

                save_as_filename = transactions.import_transactions(contents=contents, filename=filename)

                return save_as_filename

        # Export Data 
        elif ctx.triggered[0]['prop_id'] == 'export_button.n_clicks':
            transactions.export_to_excel()

            return viewValue


        # Link with FIFO
        elif ctx.triggered[0]['prop_id'] == 'fifo_button.n_clicks':

        
            transactions.link_with_fifo()
            save_as_filename = transactions.save()
            
            return save_as_filename

        # Link with FILO
        elif ctx.triggered[0]['prop_id'] == 'filo_button.n_clicks':

            transactions.link_with_filo()
            save_as_filename = transactions.save()
            
            return save_as_filename

        # Link selected Transactions Manual 
        elif ctx.triggered[0]['prop_id'] == 'link-button.n_clicks':

            # Using Scatter plot Selected Data
            if len(selectedData["points"]) == 2:          

                trans1_name =  selectedData['points'][0]['customdata']['name']
                trans2_name =  selectedData['points'][1]['customdata']['name']

                print(trans1_name, '<->', trans2_name)

                # get Trans objects from transactions
                for trans in transactions:
                    # print(trans.name)
                    if trans.name == trans1_name:
                        print(f"Trans1 Found {trans.name}")
                        trans1_obj = trans
                    
                    elif trans.name == trans2_name:
                        print(f"Trans2 Found {trans.name}")
                        trans2_obj = trans


                # Link the transactions and redisplay
                trans1_obj.link_transaction(trans2_obj)

                save_as_filename = transactions.save()
                
                return save_as_filename
            
            # Link using Table Data
            elif len(rows1) > 0 and len(derived_virtual_selected_rows1) > 0 and len(rows2) > 0 and len(derived_virtual_selected_rows2) > 0:

                row_dict = rows1[derived_virtual_selected_rows1[0]]
                trans1_name = row_dict['name']
                row_dict = rows2[derived_virtual_selected_rows2[0]]
                trans2_name = row_dict['name']

                # get Trans objects from transactions
                for trans in transactions:
                    if trans.name == trans1_name:
                        print(f"Trans1 Found {trans.name}")
                        trans1_obj = trans
                    elif trans.name == trans2_name:
                        trans2_obj = trans
                
                # Link the transactions and redisplay
                trans1_obj.link_transaction(trans2_obj)

                save_as_filename = transactions.save()
                
                return save_as_filename

        else:
            return transactions.view


    # Update Linkable Table
    @app.callback(
        Output('linked_table', 'data'),
        Input('table1', "derived_virtual_data"),
        Input('table1', "derived_virtual_selected_rows")
        )
    def update_linked_table(rows, derived_virtual_selected_rows):

        ctx = dash.callback_context

        print(f"update_linked_table was triggered by {ctx.triggered[0]['prop_id']}")

        if ctx.triggered[0]['prop_id'] == 'table1.derived_virtual_selected_rows' and len(derived_virtual_selected_rows) > 0:

            row_dict = rows[derived_virtual_selected_rows[0]]

            trans1_name = row_dict['name']

            # get Trans objects from transactions
            for trans in transactions:
                # print(trans.name)
                if trans.name == trans1_name:
                    print(f"Trans1 Found in update_linked_table {trans.name}")
                    trans1_obj = trans

            table_data = []
            
            other_transactions = trans1_obj.linked_transactions
            
            for trans in transactions:
                if trans.name in other_transactions:

                    if trans.trans_type == "buy":
                        quantity = trans1_obj.quantity
                    elif trans.trans_type == "sell":
                        quantity = trans.quantity

                    trans1_usd = trans1_obj.usd_spot * quantity
                    trans2_usd = trans.usd_spot * quantity
                    
                    profit = trans1_usd - trans2_usd

                    table_data.append({
                        'name': trans.name, 
                        'trans_type': trans.trans_type.capitalize(),
                        'symbol': trans.symbol,
                        'time_stamp': trans.time_stamp, 
                        'usd_spot': trans.usd_spot, 
                        'quantity': trans.quantity,
                        'quantity_unlinked': trans.unlinked_quantity,
                        'usd_total': trans.usd_total,
                        'profit': profit}
                    )

            return table_data




    # Output Table Linking description
    @app.callback(
        Output('linkable_table_link_text', "children"),
        Input('linkable_table', "derived_virtual_selected_rows"),
        State('table1', "derived_virtual_data"),
        State('table1', "derived_virtual_selected_rows"),
        State('linkable_table', "derived_virtual_data"),
        State('view-dropdown', 'value'))
    def update_table_link_text(derived_virtual_selected_rows2, rows1, derived_virtual_selected_rows1, rows2, viewValue):

        if derived_virtual_selected_rows2 is None or derived_virtual_selected_rows1 is None:
            raise PreventUpdate


        ctx = dash.callback_context

        print(f"update_table_link_text was triggered by {ctx.triggered[0]['prop_id']}")

        # print(type(rows1), len(rows1))
        # print(type(derived_virtual_selected_rows1), len(derived_virtual_selected_rows1))

        if ctx.triggered[0]['prop_id'] == 'linkable_table.derived_virtual_selected_rows' and len(derived_virtual_selected_rows1) > 0 and len(derived_virtual_selected_rows2) > 0:

            row_dict = rows1[derived_virtual_selected_rows1[0]]
            trans1_name = row_dict['name']
            row_dict = rows2[derived_virtual_selected_rows2[0]]
            trans2_name = row_dict['name']

            # get Trans objects from transactions
            for trans in transactions:
                if trans.name == trans1_name:
                    print(f"Trans1 Found {trans.name}")
                    trans1_obj = trans
                elif trans.name == trans2_name:
                    trans2_obj = trans
            
            if trans1_obj.trans_type == "sell":
                
                sell_obj = trans1_obj
                buy_obj = trans2_obj

            elif trans1_obj.trans_type == "buy":
                sell_obj = trans2_obj
                buy_obj = trans1_obj


            if sell_obj.unlinked_quantity <= buy_obj.unlinked_quantity:
                quantity = sell_obj.unlinked_quantity
            
            elif sell_obj.unlinked_quantity >= buy_obj.unlinked_quantity:
                quantity = buy_obj.unlinked_quantity

            buy_price = quantity * buy_obj.usd_spot
            sell_price = quantity * sell_obj.usd_spot

            profit = sell_price - buy_price

            text_output = f"Linking these Transactions will create a {trans1_obj.symbol} {quantity} Link with Gainz/Loss of {locale.currency(profit)}"

            return text_output


    # Output to table 2
    @app.callback(
        Output('linkable_table', "data"),
        Input('table1', "derived_virtual_data"),
        Input('table1', "derived_virtual_selected_rows"),
        Input('view-dropdown', 'value'),
        Input('main_scatter', 'clickData'),
        Input('view-checklist', 'value'),
        Input('view-dropdown', 'value'))
    def update_linkable_table(rows, derived_virtual_selected_rows, viewValue, clickData, assetValues, viewValues,):
        if viewValue is None:
            raise PreventUpdate

        filtered_transactions = transactions.filter(symbols=assetValues, options=viewValues)

        ctx = dash.callback_context

        print(f"update_linkable_table was triggered by {ctx.triggered[0]['prop_id']}")

        if ctx.triggered[0]['prop_id'] == 'table1.derived_virtual_selected_rows' and len(derived_virtual_selected_rows) > 0:

            row_dict = rows[derived_virtual_selected_rows[0]]

            trans1_name = row_dict['name']

            # get Trans objects from transactions
            for trans in transactions:
                # print(trans.name)
                if trans.name == trans1_name:
                    # print(f"Trans1 Found in update_linkable_table {trans.name}")
                    trans1_obj = trans

            other_transactions = trans1_obj.linked_transactions
            
            # Get other transactions
            transactions_in_view = []

            for trans in transactions:
                # print(trans.name, trans.trans_type)

                # Don't show if different Asset types
                if trans1_obj.symbol != trans.symbol:
                    continue            

                if trans1_obj.unlinked_quantity <= 0.0 or trans.unlinked_quantity <= 0.0:
                    continue
                
                # Don't show if same type
                if trans.trans_type == trans1_obj.trans_type:
                    continue
                
                # Don't show if already linked
                if trans.name in other_transactions:
                    continue
                
                if trans1_obj.trans_type == "sell":
                    if trans1_obj.time_stamp < trans.time_stamp: 
                        continue
                
                elif trans1_obj.trans_type == "buy":
                    if trans1_obj.time_stamp < trans.time_stamp:
                        continue
                                    
                # Add transaction to view    
                transactions_in_view.append(trans)

            table_data = []
            
            for trans in transactions_in_view:
                # calculate link profitability
                if trans1_obj.trans_type == "sell":
                    
                    sell_obj = trans1_obj
                    buy_obj = trans

                elif trans1_obj.trans_type == "buy":
                    sell_obj = trans
                    buy_obj = trans1_obj


                if sell_obj.unlinked_quantity <= buy_obj.unlinked_quantity:
                    quantity = sell_obj.unlinked_quantity
                
                elif sell_obj.unlinked_quantity >= buy_obj.unlinked_quantity:
                    quantity = buy_obj.unlinked_quantity

                buy_price = quantity * buy_obj.usd_spot
                sell_price = quantity * sell_obj.usd_spot

                profit = sell_price - buy_price

                
                table_data.append({
                'name': trans.name, 
                'trans_type': trans.trans_type.capitalize(),
                'symbol': trans.symbol,
                'time_stamp': trans.time_stamp, 
                'usd_spot': trans.usd_spot, 
                'quantity': trans.quantity,
                'quantity_unlinked': trans.unlinked_quantity,
                'usd_total': trans.usd_total,
                'profit': profit})

            return table_data


    # Output to Table 1
    @app.callback(
        Output('table1', 'data'),
        Input('main_scatter', 'clickData'),
        Input('asset-checklist', 'value'),
        Input('view-checklist', 'value'),
        Input('view-dropdown', 'value'))
    def update_table1(clickData, assetValues, viewValues, viewValue):
        if viewValue is None:
            raise PreventUpdate
        
        ctx = dash.callback_context
        print(f"update_table1 was triggered by {ctx.triggered[0]['prop_id']}")

        if ctx.triggered[0]['prop_id'] == 'main_scatter.clickData':
            transactions_in_view = []
            trans1_name = clickData['points'][0]['customdata']['name']

            for trans in transactions:
                if trans.name == trans1_name:
                    transactions_in_view.append(trans)
                    
            table_data = [{
                'name': trans.name, 
                'trans_type': trans.trans_type.capitalize(),
                'symbol': trans.symbol,
                'time_stamp': trans.time_stamp, 
                'usd_spot': trans.usd_spot, 
                'quantity': trans.quantity,
                'quantity_unlinked': trans.unlinked_quantity,
                'usd_total': trans.usd_total} for trans in transactions_in_view]

            return table_data
            
        else:

            transactions_in_view = []

            for trans in transactions:
                if trans.trans_type == "sell":
                    if trans.symbol in assetValues:
                        if trans.unlinked_quantity > 0.0:
                            transactions_in_view.append(trans)

            table_data = [{
                'name': trans.name,
                'trans_type': trans.trans_type.capitalize(), 
                'symbol': trans.symbol,
                'time_stamp': trans.time_stamp, 
                'usd_spot': trans.usd_spot, 
                'quantity': trans.quantity,
                'quantity_unlinked': trans.unlinked_quantity,
                'usd_total': trans.usd_total} for trans in transactions_in_view]

            return table_data

        
    # Refresh View Options on link-button click or view dropdown change
    @app.callback(
        Output('view-dropdown', 'options'),
        Input('view-dropdown', 'value'),
        Input('link-button', 'n_clicks'),
        Input('upload-data', 'contents'))
    def update_view_choices(viewValue, n_clicks, contents):

        transactions.load_views()
        if viewValue != '':
            transactions.load(filename = viewValue)
        
        return transactions.views


    # Output to Main Scatter
    @app.callback(
        Output('main_scatter', 'figure'),
        Input('view-dropdown', 'value'),
        Input('table1', "derived_virtual_selected_rows"),
        Input('linkable_table', "derived_virtual_selected_rows"),
        Input('asset-checklist', 'value'),
        Input('view-checklist', 'value'),
        State('table1', "derived_virtual_data"),
        State('linkable_table', "derived_virtual_data"),
        )
    def update_view(viewValue, derived_virtual_selected_rows1, derived_virtual_selected_rows2, assetValues, viewValues,  rows1, rows2):
        if viewValue is None:
            raise PreventUpdate

        show_links = True
        ctx = dash.callback_context

        ctx_msg = json.dumps({
            'states': ctx.states,
            'triggered': ctx.triggered,
            'inputs': ctx.inputs
        }, indent=2)

        # print(ctx_msg)

        print(f"update_view was triggered by {ctx.triggered[0]['prop_id']}")


        filtered_transactions = transactions.filter(symbols=assetValues, options=viewValues)

        figure = px.scatter(labels={'x':'USD Price Log*', 'y':'Transaction Date'}, log_y=True)

        if ctx.triggered[0]['prop_id'] == 'table1.derived_virtual_selected_rows' and len(derived_virtual_selected_rows1) > 0:
            show_links = False
            row_dict = rows1[derived_virtual_selected_rows1[0]]
            trans1_name = row_dict['name']
            
            transactions_in_view = []
            # get Trans objects from transactions
            for trans in filtered_transactions:
                if trans.name == trans1_name:
                    print(f"Trans1 Found {trans.name}")
                    trans1_obj = trans
                    transactions_in_view.append(trans)
                
            other_transactions = trans1_obj.linked_transactions

            for trans in transactions:
                if trans.name in other_transactions:
                    transactions_in_view.append(trans)

            filtered_transactions = transactions_in_view

            links = set([
            link for link in trans1_obj.links
            ])

            for link in links:

                lines_scatter = go.Scatter(
                                    x = [link.sell.time_stamp, link.buy.time_stamp],
                                    y = [link.sell.usd_total, link.buy.usd_total],
                                    showlegend=False,
                                    mode = 'lines',
                                    hoverinfo = 'skip'                          
                                )

                figure.add_trace(lines_scatter)

        if ctx.triggered[0]['prop_id'] == 'linkable_table.derived_virtual_selected_rows' and len(derived_virtual_selected_rows2) > 0:
            show_links = False
            row_dict = rows1[derived_virtual_selected_rows1[0]]
            trans1_name = row_dict['name']
            row_dict = rows2[derived_virtual_selected_rows2[0]]
            trans2_name = row_dict['name']

            transactions_in_view = []
            # get Trans objects from transactions
            for trans in transactions:
                if trans.name == trans1_name:
                    print(f"Trans1 Found {trans.name}")
                    trans1_obj = trans
                    transactions_in_view.append(trans)
                elif trans.name == trans2_name:
                    trans2_obj = trans
                    transactions_in_view.append(trans)

            


            filtered_transactions = transactions_in_view


        for trans in filtered_transactions:

            trans_trace = go.Scatter(
                                x = [trans.time_stamp],
                                y = [trans.usd_total],
                                hovertemplate = f'<b>Asset</b>: {trans.symbol}<br>'+
                                                f'<i>Type</i>: {trans.trans_type.capitalize()}<br>'+
                                                f'<i>USD Spot</i>: {locale.currency(trans.usd_spot)}<br>'+
                                                f'<i>Quantity</i>: {trans.quantity}<br>'+
                                                f'<i>Total in USD</i>: {locale.currency(trans.usd_total)}<br>',
                                mode = 'markers',
                                showlegend=False,
                                customdata = [{'name': trans.name, 'links': trans.linked_transactions}],
                                marker = dict(color=colors[trans.trans_type], size=10)
                            )

            figure.add_trace(trans_trace)

        if show_links:
            # Get Links from transactions objects and add links to Scatter
            links = set([
                    link 
                    for trans in filtered_transactions
                    for link in trans.links
                    ])

            for link in links:

                lines_scatter = go.Scatter(
                                    x = [link.sell.time_stamp, link.buy.time_stamp],
                                    y = [link.sell.usd_total, link.buy.usd_total],
                                    showlegend=False,
                                    mode = 'lines',
                                    hoverinfo = 'skip'                          
                                )

                figure.add_trace(lines_scatter)

        figure.update_layout(title='Transactions Scatter my dude!')
        return figure


    # # Displays first transaction pie chart
    @app.callback(
        Output('trans1-pie', 'figure'),
        Input('main_scatter', 'clickData'),
        State('view-dropdown', 'value'))
    def generate_chart(clickData, viewValue):
        if clickData is None:
            raise PreventUpdate

        trans1_name =  clickData['points'][0]['customdata']['name']

        # get Trans objects from transactions
        for trans in transactions:
            # print(trans.name)
            if trans.name == trans1_name:
                print(f"Trans1 Found {trans.name}")
                trans1_obj = trans

        quantity = trans1_obj.quantity
        unlinked_quantity = trans1_obj.unlinked_quantity
        linked_quantity = quantity - unlinked_quantity
        
        names = ['Unlinked']

        values = [unlinked_quantity]
        
        for link in trans1_obj.links:
            values.append(link.quantity)
            print(link.other_transaction(trans1_obj))
            names.append(link.other_transaction(trans1_obj))


        figure = px.pie(
                        names=names, 
                        values=values, 
                        title=f"Type: {trans.trans_type.capitalize()}, Quantity: {trans.quantity}, Date: {trans.time_stamp}",
                        color=names,
                        color_discrete_map={'Unlinked':'darkblue'}
                        )
        
        figure.update_traces(textposition='inside', textinfo='percent+value')
                
        return figure


    # Displays linked transaction(s) pie chart(s)
    @app.callback(
        Output('linked-pies', 'children'),
        [Input('main_scatter', 'clickData'),
        Input('view-dropdown', 'value')])
    def generate_charts(clickData, viewValue):
        if viewValue is None or clickData is None:
            raise PreventUpdate
        
        
        output = []
        # Get Links from transactions objects
        
        trans1_name =  clickData['points'][0]['customdata']['name']

        for trans in transactions:
            if trans.name == trans1_name:
                print(f"Trans1 Found {trans.name}")
                trans1_obj = trans


        other_transactions = trans1_obj.linked_transactions
        
        # Get other transactions
        other_pies = []

        for trans in transactions:
            for other_trans in other_transactions:
                if other_trans == trans.name:
                    other_pies.append(trans)
            
        if len(other_pies) > 0:
            i = 0
            for trans in other_pies:

                quantity = trans.quantity
                unlinked_quantity = trans.unlinked_quantity
                linked_quantity = quantity - unlinked_quantity

                names = ['Unlinked']
                values = [unlinked_quantity]
                
                for link in trans1_obj.links:
                    values.append(link.quantity)
                    print(link.other_transaction(trans1_obj))
                    names.append(link.other_transaction(trans1_obj))

                figure = px.pie(
                                names=names, 
                                values=values, 
                                title=f"Type: {trans.trans_type.capitalize()}, Quantity: {trans.quantity}, Date: {trans.time_stamp}",
                                color=names,
                                color_discrete_map={'Unlinked':'darkblue'})
                
                figure.update_traces(textposition='inside', textinfo='percent+value')
                output.append(dcc.Graph(id='other-graph'+str(i), figure=figure))

                i += 1

            return output



    ## debug/example callbacks Bruh
    @app.callback(
        Output('hover-data', 'children'),
        Input('main_scatter', 'hoverData'))
    def display_hover_data(hoverData):
        return json.dumps(hoverData, indent=2)

    @app.callback(
        Output('click-data', 'children'),
        Input('main_scatter', 'clickData'))
    def display_click_data(clickData):
        return json.dumps(clickData, indent=2)
        
    @app.callback(
        Output('selected-data', 'children'),
        Input('main_scatter', 'selectedData'))
    def display_selected_data(selectedData):
        return json.dumps(selectedData, indent=2)
    
    return app.server




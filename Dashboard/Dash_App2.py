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



# Creates the Layout of the webpage
layout = html.Div(className="right_col", role="main", children=[
    

    html.Div(
        id="linkable_table_link_text", 
        children="This will Change to PNL",
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'textAlign': 'center',
            'margin': '10px'
        }),
        html.Button(
            id='link-button',
            n_clicks=0,
            children='Link Selected Transactions',
            style={
                'width': '30%',
                'height': '60px',
                'lineHeight': '60px',
                'textAlign': 'center',
                'margin': '10px'
            }
        ),  

    # html.P("Price Range"),
    # dcc.RangeSlider(
    #     id='range-slider',
    #     min=0, max=8000, step=100, marks={4000: "aye!"}),
    
    

    # The Div that holds the tables
    html.Div([
    
        html.Div([
            html.P(id="table1-text", children="Sells with Unlinked Quantity"),
            dash_table.DataTable(
                id='sells_table',
                columns=[
                    {"name": 'Name', "id": 'name'},
                    {"name": "Type", "id": "trans_type", "type": "text"},
                    {"name": "Asset", "id": "symbol", "type": "text"},
                    {"name": 'Time Stamp', "id": 'time_stamp', "type": 'datetime'},
                    {"name": "Quantity", "id": "quantity"},
                    {"name": "Quantity Unlinked", "id": "quantity_unlinked"},
                    {"name": "USD Spot", "id": "usd_spot", "type": 'numeric', 'format': money},
                    {"name": "Quantity In USD", "id": "usd_total", "type": 'numeric', 'format': money}],
                style_cell={'textAlign': 'left'},
                editable=True,
                row_selectable="single",
                sort_action="native",
                page_size=10,
                data=[{'time_stamp': 'Super Profitable Time Stamp!', 'usd_total': "Big Dolla Dolla Bills!"}]
                )], className='six columns'),
    
        html.Div([
            html.P(id="linked_table-text", children="Linked Transactions"),
            dash_table.DataTable(
                id='linked_table',
                columns=[
                    {"name": 'Name', "id": 'name'},
                    {"name": "Type", "id": "trans_type", "type": "text"},
                    {"name": "Asset", "id": "symbol", "type": "text"},
                    {"name": 'Time Stamp', "id": 'time_stamp', "type": 'datetime'},
                    {"name": "Quantity", "id": "quantity"},
                    {"name": "Quantity Unlinked", "id": "quantity_unlinked"},
                    {"name": "USD Spot", "id": "usd_spot", "type": 'numeric', 'format': money},
                    {"name": "Quantity In USD", "id": "usd_total", "type": 'numeric', 'format': money},
                    {"name": "Link Profitability USD", "id": "profit", "type": 'numeric', 'format': money}
                    ],
                style_cell={'textAlign': 'left'},
                editable=True,
                row_selectable="single",
                sort_action="native",
                page_size=10,
                data=[{'time_stamp': 'Super Profitable Time Stamp!', 'usd_total': "Big Dolla Dolla Bills!"}]
                ), 
            
            html.P(id="linkable_table-text", children="Transactions that can be linked"),
            dash_table.DataTable(
                id='linkable_table',
                columns=[
                    {"name": 'Name', "id": 'name'},
                    {"name": "Type", "id": "trans_type", "type": "text"},
                    {"name": "Asset", "id": "symbol", "type": "text"},     
                    {"name": 'Time Stamp', "id": 'time_stamp', "type": 'datetime'},
                    {"name": "Quantity", "id": "quantity"},
                    {"name": "Quantity Unlinked", "id": "quantity_unlinked"},
                    {"name": "USD Spot", "id": "usd_spot", "type": 'numeric', 'format': money},
                    {"name": "Quantity In USD", "id": "usd_total", "type": 'numeric', 'format': money},
                    {"name": "Link Profitability USD", "id": "profit", "type": 'numeric', 'format': money}
                    ],
                style_cell={'textAlign': 'left'},
                editable=True,
                row_selectable="single",
                sort_action="native",
                data=[{'time_stamp': 'Super Profitable Time Stamp!', 'usd_total': "Big Dolla Dolla Bills!"}]
                ), 
                
               ], className='six columns'),
                

    ], className="row"),

    html.Div([
        
        html.Div([
            html.H3('Selected Transaction'),
            dcc.Graph(id='trans1-pie')
        ], className="six columns"),
        
        
        html.Div([
            html.H3('Linked Transactions'),
            html.Pre(id='linked-pies')
        ], className="six columns"),
    
    ], className="row"),


    # Debug Layout Below 
    html.Div(className='row', children=[
        html.Div([
            dcc.Markdown("""
                **Hover Data**

                Mouse over values in the graph.
            """),
            html.Pre(id='hover-data', style=styles['pre']),
        ], className='three columns'),

        html.Div([
            dcc.Markdown("""
                **Click Data**

                Click on points in the graph.
            """),
            html.Pre(id='click-data', style=styles['pre']),
        ], className='three columns'),

        html.Div([
            dcc.Markdown("""
                **Selection Data**

                Choose the lasso or rectangle tool in the graph's menu
                bar and then select points in the graph.

                Note that if `layout.clickmode = 'event+select'`, selection data also
                accumulates (or un-accumulates) selected data if you hold down the shift
                button while clicking.
            """),
            html.Pre(id='selected-data', style=styles['pre']),
        ], className='three columns'),

        html.Div([
            dcc.Markdown("""
                **Zoom and Relayout Data**

                Click and drag on the graph to zoom or click on the zoom
                buttons in the graph's menu bar.
                Clicking on legend items will also fire
                this event.
            """),
            html.Pre(id='relayout-data', style=styles['pre']),
        ]),

        html.Div(id='intermediate-value', style={'display': 'none'})
    ])

])



transactions = Transactions()

url_base = '/dash/app2/'

def Add_Dash(server):
    app = Dash(server=server, url_base_pathname=url_base)
    apply_layout_with_auth(app, layout)


    # sells table Text
    @app.callback(
        Output('table1-text', 'children'),
        Input('main_scatter', 'clickData')
    )
    def table1_text_update(clickData):
        if clickData is None:
            raise PreventUpdate

        return "Selected Transaction"


    # Output to sells table
    @app.callback(
        Output('sells_table', 'data'),
        Input('main_scatter', 'clickData'),
    )
    def update_sells_table(clickData):

        ctx = dash.callback_context
        print(f"update_table1 was triggered by {ctx.triggered[0]['prop_id']}")



        transactions_in_view = []

        for trans in transactions:
            if trans.trans_type == "sell":
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

        




    # Update Linkable Table
    @app.callback(
        Output('linked_table', 'data'),
        Input('sells_table', "derived_virtual_data"),
        Input('sells_table', "derived_virtual_selected_rows")
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
        State('sells_table', "derived_virtual_data"),
        State('sells_table', "derived_virtual_selected_rows"),
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
        Input('sells_table', "derived_virtual_data"),
        Input('sells_table', "derived_virtual_selected_rows"),
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
        Input('sells_table', "derived_virtual_selected_rows"),
        Input('linkable_table', "derived_virtual_selected_rows"),
        Input('asset-checklist', 'value'),
        Input('view-checklist', 'value'),
        State('sells_table', "derived_virtual_data"),
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




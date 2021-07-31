

// Sidebar
$(document).ready(function() {

});


// HODL Accounting 
$(document).ready(function() {

    var table = $('#eh_stats_datatable').DataTable({
        "pageLength": 50,
        select: {
            style: 'single'
        },
    });

    $('#eh_stats_datatable tbody').on( 'click', 'tr', function () {
        console.log( table.row( this ).data() );
        var asset = table.row( this ).data()[0]
        var buys = table.row( this ).data()[1]
        var sells = table.row( this ).data()[2]
        var sent = table.row( this ).data()[3]
        var hodl = table.row( this ).data()[8]
        var needs_classification = buys - sells
        var min_hodl = buys - sent
        var hodl_text = $('#eh_options').text('')
        var Sold_or_Lost = buys - hodl
        var needs_classification_hodl = Sold_or_Lost - sells
        if (hodl == "N/A") {
        
            hodl_text.append(asset + ' Selected')
            hodl_text.append("<br>Buys: " + buys + " - Sells: " + sells + " = Needs_Classification: " + needs_classification)
            
            if (needs_classification < 0) { 
                hodl_text.append("<br>Looks like you have more sells than buys. You can add buys manually or import additonal from CSV.")
                
             }

            if (min_hodl >= 0) {
                hodl_text.append("<br>If Converting Sends to Sells minimum HODL is " + min_hodl)
            }

        } else {
            $("#submit_hodl_button").text("Change HODL")

            hodl_text.append(asset + ' Selected')
            hodl_text.append("<br>Buys: " + buys + " - HODL: " + hodl + " = Sold_or_Lost: " + Sold_or_Lost)
            hodl_text.append("<br>Sold_or_Lost: " + Sold_or_Lost + " - Sells: " + sells + " = Needs_Classification: " + needs_classification_hodl)
            if (needs_classification_hodl <= .0019) {  hodl_text.append("<br> Pretty close to 0, might be best to leave it as-is.")}
            hodl_text.append("<br>We can clarify by converting our earliest sends into sells, or converting our earliest buys into lost")
            
            $('#convert_text').text("Enter Up to " + needs_classification_hodl + ":" )

        }

    });


    $("#submit_hodl_button").click(function(){

        $.ajax({
            type: "POST",
            url: "/wizards/hodl_info",
            data: JSON.stringify({
                'quantity': $('#hodl_quantity').val(),
                'asset': $('#eh_stats_datatable').DataTable().row( {selected:true} ).data()
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                location.reload()
            },   
        });
    });

    $("#sends_to_sells_button").click(function(){
        $.ajax({
            type: "POST",
            url: "/wizards/sends_to_sells",
            data: JSON.stringify({
                'quantity': $('#convert_quantity').val(),
                'asset': $('#eh_stats_datatable').DataTable().row( {selected:true} ).data()
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                location.reload()
            },   
        });
    });


    $("#buys_to_lost_button").click(function(){

        $.ajax({
            type: "POST",
            url: "/wizards/buys_to_lost",
            data: JSON.stringify({
                'quantity': $('#convert_quantity').val(),
                'asset': $('#eh_stats_datatable').DataTable().row( {selected:true} ).data()
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                location.reload()
            },   
        });
    });

});


// Auto Link Page
$(document).ready(function() {
    var table = $('#al_stats_datatable').DataTable({
        select: {
            style: 'single'
        },
    });


    $('#al_stats_datatable tbody').on( 'click', 'tr', function () {
        
 
        $.ajax({
            type: "POST",
            url: "/wizards/auto_link_pre_check",
            data: JSON.stringify({
                'row_data': table.row( this ).data()
              }),  

            contentType: 'application/json',
            success: function (data) {
                console.log(data)

                $('#al_options').html(data['message'])
            
            },   
        });

    } );

    $("#link_w_fifo").click(function(){
        $.ajax({
            type: "POST",
            url: "/wizards/auto_link_asset",
            data: JSON.stringify({
                'algo': 'fifo',
                'asset': $('#al_stats_datatable').DataTable().row( {selected:true} ).data()
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                
                location.reload()
            },   
        });

    });

    $("#link_w_filo").click(function(){
        $.ajax({
            type: "POST",
            url: "/wizards/auto_link_asset",
            data: JSON.stringify({
                'algo': 'filo',
                'asset': $('#al_stats_datatable').DataTable().row( {selected:true} ).data()
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                alert(data)
                location.reload()
            },   
        });
    });



} );


// stats page code
$(document).ready(function() {
    
    // Init Start datetimepicker
    $("#start_date").datetimepicker({
        format: "dd MM yyyy - hh:ii",
        linkField: "mirror_field_start",
        linkFormat: "yyyy-mm-dd hh:ii",
    });

    // init end_date datetimepicker
    $("#end_date").datetimepicker({
        format: "dd MM yyyy - hh:ii",
        linkField: "mirror_field_end",
        linkFormat: "yyyy-mm-dd hh:ii"

    });

    // on start_date change
    $("#start_date").datetimepicker().on('changeDate', function(ev){
        // console.log($('#start_date').data().datetimepicker.date)
        // console.log($('#mirror_field_start').val())

        $.ajax({
            type: "POST",
            url: "/stats/date_range",
            data: JSON.stringify({
                'start_date': $('#mirror_field_start').val(),
                'end_date': $('#mirror_field_end').val()
                }),  

            contentType: 'application/json',
            success: function (data) {
                console.log(data)
                
                $('#statspage_stats_datatable').DataTable().clear();
                $('#statspage_stats_datatable').DataTable().rows.add(data['stats_table_rows']).draw();

                $('#stats_table_title').text('All Asset Stats for ' + data['date_range']['start_date'] + ' - ' + data['date_range']['end_date'])
                $('#detailed_stats_title').text('Detailed Asset Stats for ' + data['date_range']['start_date'] + ' - ' + data['date_range']['end_date'])

            },   
        });
    });
                        

    // on end_date change
    $("#end_date").datetimepicker().on('changeDate', function(ev){
        console.log($('#end_date').data().datetimepicker.date)
        console.log($('#mirror_field_end').val())

        $.ajax({
            type: "POST",
            url: "/stats/date_range",
            data: JSON.stringify({
                'start_date': $('#mirror_field_start').val(),
                'end_date': $('#mirror_field_end').val()
                }),  

            contentType: 'application/json',
            success: function (data) {
                // console.log(data)
                
                $('#statspage_stats_datatable').DataTable().clear();
                $('#statspage_stats_datatable').DataTable().rows.add(data['stats_table_rows']).draw();

                $('#stats_table_title').text('All Asset Stats for ' + data['date_range']['start_date'] + ' - ' + data['date_range']['end_date'])
                $('#detailed_stats_title').text('Detailed Asset Stats for ' + data['date_range']['start_date'] + ' - ' + data['date_range']['end_date'])

            },   
        });
    });


    // init tables
    var table = $('#statspage_stats_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#statspage_detailed_datatable').DataTable({
        "pageLength": 50,
        select: {
            style: 'single'
        },
    });

    $('#statspage_links_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#statspage_sells_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#statspage_buys_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#statspage_stats_datatable tbody').on( 'click', 'tr', function () {
        console.log( table.row( this ).data() );
        
        
        $.ajax({
            type: "POST",
            url: "/stats/selected_asset",
            data: JSON.stringify({
                'row_data': table.row( this ).data(),
                'start_date': $('#mirror_field_start').val(),
                'end_date': $('#mirror_field_end').val()
                }),  

            contentType: 'application/json',
            success: function (data) {

                console.log(data)
                
                $('#statspage_detailed_datatable').DataTable().clear();
                $('#statspage_detailed_datatable').DataTable().rows.add(data['detailed_stats']).draw();
                
                $('#statspage_links_datatable').DataTable().clear();
                $('#statspage_links_datatable').DataTable().rows.add(data['linked']).draw();

                $('#statspage_sells_datatable').DataTable().clear();
                $('#statspage_sells_datatable').DataTable().rows.add(data['sells']).draw();

                $('#statspage_buys_datatable').DataTable().clear();
                $('#statspage_buys_datatable').DataTable().rows.add(data['buys']).draw();
                    
            },   
        });
    } );


} );


// history page code
$(document).ready(function() {

    var table = $('#history_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    
    $("#load_button").click(function(){
        $.ajax({
            type: "POST",
            url: "/history/load",
            data: JSON.stringify({
                'data': $('#history_datatable').DataTable().row( {selected:true} ).data(),
                
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                location.reload()
            },   
        });
    });


    $("#revert_button").click(function(){

        $.ajax({
            type: "POST",
            url: "/history/revert",
            data: JSON.stringify({
                'data': $('#history_datatable').DataTable().row( {selected:true} ).data(),
                
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                location.reload()

            },   
        });
    });

    $("#delete_button").click(function(){

        $.ajax({
            type: "POST",
            url: "/history/delete",
            data: JSON.stringify({
                'data': $('#history_datatable').DataTable().row( {selected:true} ).data(),
                
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                location.reload()
            },   
        });
    });


} );

// export page code
$(document).ready(function() {

    $('#export_datepicker').daterangepicker({
        timePicker: true,
        showDropdowns: true,
        startDate: moment().subtract(10, 'years'),
        endDate: moment().startOf('hour'),
        locale: {
          format: 'M/DD hh:mm A'
        }
      });

    $('#export_datepicker').on('apply.daterangepicker', function(ev, picker) {
        // console.log(picker.startDate.format('YYYY-MM-DD'));
        // console.log(picker.endDate.format('YYYY-MM-DD'));
        
        $.ajax({
            type: "POST",
            url: "/stats/date_range",
            data: JSON.stringify({
                'start_date': picker.startDate,
                'end_date': picker.endDate
                }),  

            contentType: 'application/json',
            success: function (data) {
                // console.log(data)
                
                $('#exportpage_stats_datatable').DataTable().clear();
                $('#exportpage_stats_datatable').DataTable().rows.add(data['stats_table_rows']).draw();

                $('#stats_table_title').text('All Asset Stats for ' + data['date_range']['start_date'] + ' - ' + data['date_range']['end_date'])

            },   
        });
    });


    $('#exportpage_stats_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#exportpage_stats_datatable tbody').on( 'click', 'tr', function () {
        console.log( table.row( this ).data() );
        $.ajax({
            type: "POST",
            url: "/stats/selected_asset",
            data: JSON.stringify({
                'row_data': table.row( this ).data(),
                'start_date': $('#export_datepicker').data('daterangepicker')['startDate'],
                'end_date': $('#export_datepicker').data('daterangepicker')['endDate']
                }),  

            contentType: 'application/json',
            success: function (data) {

                console.log(data)
                
                $('#statspage_detailed_datatable').DataTable().clear();
                $('#statspage_detailed_datatable').DataTable().rows.add(data['detailed_stats']).draw();
            },   
        });
    } );


    $("#export_button").click(function(){
        $.ajax({
            type: "POST",
            url: "/export/save",
            data: JSON.stringify({
                'data': $('#exportpage_stats_datatable').DataTable().row( {selected:true} ).data(),      
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                alert("Saving Export as" + data)
            },   
        });
    });

});




// Add and Manage Links Page
$(document).ready(function() {
    
    
    $('#addlinks_stats_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#addlinks_sells_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#linked_datatable').DataTable({
        select: {
            style: 'single'
        },
    });

    $('#linkable_datatable').DataTable({
        select: {
            style: 'single'
        },
    });


    $('#addlinks_stats_datatable tbody').on( 'click', 'tr', function () {
        console.log( $('#addlinks_stats_datatable').DataTable().row( this ).data() );

        $.ajax({
            type: "POST",
            url: "/wizards/selected_asset",
            data: JSON.stringify({
                'row_data': $('#addlinks_stats_datatable').DataTable().row( this ).data(),
                'start_date': '',
                'end_date': '',
                'unlinked_remaining': $('#checkbox_unlinked').is(':checked')
                }),  

            contentType: 'application/json',
            success: function (data) {

                console.log(data)
                
                
                $('#addlinks_sells_datatable').DataTable().clear();
                $('#addlinks_sells_datatable').DataTable().rows.add(data['sells']).draw();

                    
            },   
        });

    });


    $('#addlinks_sells_datatable tbody').on( 'click', 'tr', function () {
        console.log( $('#addlinks_sells_datatable').DataTable().row( this ).data() );
 
        $.ajax({
            type: "POST",
            url: "/wizards/linkable_data",
            data: JSON.stringify({
                'row_data': $('#addlinks_sells_datatable').DataTable().row( this ).data() 
              }),  

            contentType: 'application/json',
            success: function (data) {
                console.log(data)
                
                $('#linked_datatable').DataTable().clear();
                $('#linked_datatable').DataTable().rows.add(data['linked']).draw();
                
                $('#linkable_datatable').DataTable().clear();
                $('#linkable_datatable').DataTable().rows.add(data['linkable']).draw();

                $('#unlinkable_datatable').DataTable().clear();
                $('#unlinkable_datatable').DataTable().rows.add(data['unlinkable']).draw();
                   
            },   
        });
    } );

    $("#link_button").click(function(){
        // alert($('#linkable_datatable').DataTable().row( {selected:true} ).data());
        // alert($('#sells_datatable').DataTable().row( {selected:true} ).data());
        $.ajax({
            type: "POST",
            url: "/wizards/link_button",
            data: JSON.stringify({
                'sell_data': $('#addlinks_sells_datatable').DataTable().row( {selected:true} ).data(),
                'buy_data': $('#linkable_datatable').DataTable().row( {selected:true} ).data(),
                
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                alert("Posting a new link!")
                $('#sells_datatable').DataTable().clear();
                $('#sells_datatable').DataTable().rows.add(data).draw();
                location.reload()
            },   
        });
    });


} );


// Import Transactions Page

$(document).ready(function() {

    $('#import_datatable').DataTable({
        "pageLength": 25,
        select: {
            style: 'single'
        },
    });

} );

// Add and Manage Transactions Page
$(document).ready(function() {
    
    $('#add_transactions_stats_datatable').DataTable({
        "pageLength": 25,
        select: {
            style: 'single'
        },
    });

    $('#add_transactions_sells_datatable').DataTable({
        "pageLength": 10,
        select: {
            style: 'single'
        },
    });

    $('#add_transactions_buys_datatable').DataTable({
        "pageLength": 10,
        select: {
            style: 'single'
        },
    });

    $('#add_transactions_stats_datatable tbody').on( 'click', 'tr', function () {
        
        
        $.ajax({
            type: "POST",
            url: "/wizards/add_transactions_selected_asset",
            data: JSON.stringify({
                'row_data':  $('#add_transactions_stats_datatable').DataTable().row( this ).data(),
                }),  

            contentType: 'application/json',
            success: function (data) {
               
                $('#add_transactions_sells_datatable').DataTable().clear();
                $('#add_transactions_sells_datatable').DataTable().rows.add(data['sells']).draw();
                
                $('#add_transactions_buys_datatable').DataTable().clear();
                $('#add_transactions_buys_datatable').DataTable().rows.add(data['buys']).draw();

                $('#add_transactions_sends_datatable').DataTable().clear();
                $('#add_transactions_sends_datatable').DataTable().rows.add(data['sends']).draw();

                    
            },   
        });
    } );


    $("#sells_delete_button").click(function(){
        $.ajax({
            type: "POST",
            url: "/wizards/delete",
            data: JSON.stringify({
                'row_data': $('#add_transactions_sells_datatable').DataTable().row( {selected:true} ).data(),
                'asset': $('#add_transactions_stats_datatable').DataTable().row( {selected:true} ).data(),
                'type': 'sell'
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                alert(data)
                location.reload()
            },   
        });
    });


    $("#buys_delete_button").click(function(){
        $.ajax({
            type: "POST",
            url: "/wizards/delete",
            data: JSON.stringify({
                'row_data': $('#add_transactions_buys_datatable').DataTable().row( {selected:true} ).data(),
                'asset': $('#add_transactions_stats_datatable').DataTable().row( {selected:true} ).data(),
                'type': 'buy'
              }),  
            dataType: "json",
            contentType: 'application/json',
            success: function (data) {
                alert(data)
                location.reload()
            },   
        });
    });

} );
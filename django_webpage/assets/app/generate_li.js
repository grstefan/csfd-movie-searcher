var filterButton = ''
var page = 0
$("a#button_1").on('click', function(){
     window.location = "http://127.0.0.1:8000/search@strana-0@%20@0";
});

$("a#button_2").on('click', function(){
    var avg = 0
     if ($('#avg').is(":checked"))
    {
        avg = 1
    }
     var str = $("#search_box").val()
     window.location = "search@strana-0@" + str + '@' + avg.toString();
});

$("a#button_3").on('click', function(){
     var str = $("#search_box").val();
     page = 0
    var avg = 0
     if (filterButton == 'Hodnotenie'){
          var from = $("#gte").val()
          if (from == '') {
              from = '0'
          }
          var to = $("#lte").val()
          if (to == '') {
              to = '100'
          }
          window.location = 'search@strana-0@' + str + '@hodnotenie@' + from + '@' + to;
     }
     else if (filterButton == 'Herci') {
         var fuz = 0

         if ($('#fuzzy').is(":checked"))
        {
            fuz = 1
        }
         if ($('#avg').is(":checked"))
        {
            avg = 1
        }
         window.location = 'search@strana-0@' + str + '@herci@' + fuz.toString() + '@' + avg.toString();
     }
     else {
        if ($('#avg').is(":checked"))
        {
            avg = 1
        }
         window.location = 'search@strana-0@' + str+ '@' + avg.toString();
     }
});


$('#filter').change(function (e) {
    filterButton = e.target.value;
});


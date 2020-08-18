var cList = $('ul.list-group')

$( "#search_box" ).keyup(function(event) {
    var el = $( "#search_box" ).val()
    var cList = $('ul.list-group')
    cList.empty()
    var sss = $.getJSON('/complete@' + el, function(result){
        $.each(result, function(i, field){
            var li = $('<li/>')
                .attr('onclick','autocomplete(this.id)')
                .attr('id', field)
                .addClass('list-group-item d-flex justify-content-between align-items-center')
                .text(field)
                .appendTo(cList)
        });
    });

});

function autocomplete(str)
{
    $( "#search_box" ).val(str)
    $("#liiist").css('display', 'none')
}

$( "#search_box" ).focus(function(event) {

    $("#liiist").css('display', 'block')
    var el = $( "#search_box" ).val()
    var cList = $('ul.list-group')
    cList.empty()
    var sss = $.getJSON('/complete@' + el, function(result){
        $.each(result, function(i, field){
            var li = $('<li/>')
                .attr('onclick','autocomplete(this.id)')
                .attr('id', field)
                .addClass('list-group-item d-flex justify-content-between align-items-center')
                .text(field)
                .appendTo(cList)
        });
    });
});

$("#all").click(function () {
    $("#liiist").css('display', 'none')
});
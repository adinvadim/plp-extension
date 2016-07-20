$('#university-filter span.text').html($('#id_university option:selected').text());
$('#session-filter span.text').html($('#id_session option:selected').text());
$('.f-publish-btn').click(function(e) {
    $(this).attr('disabled', 'disabled').parents('tr').find('.f-reject-btn').attr('disabled', 'disabled');
    push_change($(this).data('feedback'), true);
});
$('.f-reject-btn').click(function(e) {
    $(this).attr('disabled', 'disabled').parents('tr').find('.f-publish-btn').attr('disabled', 'disabled');
    push_change($(this).data('feedback'), false);
});

$('.paginator-link').click(function(e) {
    e.preventDefault();
    var href = $(this).attr('href').slice(1).split('=');
    insertParam(href[0], href[1]);
});
function insertParam(key, value) {
    key = encodeURI(key); value = encodeURI(value);
    var kvp = document.location.search.substr(1).split('&');
    var i=kvp.length; var x;
    while(i--) {
        x = kvp[i].split('=');

        if (x[0]==key)
        {
            x[1] = value;
            kvp[i] = x.join('=');
            break;
        }
    }
    if(i<0) {kvp[kvp.length] = [key,value].join('=');}
    document.location.search = kvp.join('&');
}
function push_change(feedback, accept) {
    $.post(REQUEST_URL, {'feedback': feedback, 'accept': accept});
}

let isOpen = false, $msg, $title, $cookie
    loc = window.location,
    url = `${loc.protocol}//${loc.hostname}:${loc.port}/gen_sentence`;

$(function () {    
    $msg = $('#msg');
    $title = $('.title');
    $cookie = $('#cookie');
       
    $('body').click(function () {
        if (isOpen) {
            $cookie.attr('src', '../static/images/close.jpg');
            $title.html('Our AI has placed your fortune inside the cookie. <br />Click to open and view it!');            
            $msg.find('p').text('');
            $msg.animate({
                height: '0px',
                opacity: 0
            }, 500);
        }
        else {
            $cookie.attr('src', '../static/images/spinner.gif');          
            
            $msg.animate({
                height: '100px',
                opacity: 1
            }, 500);
            query('');
        }
        isOpen = !isOpen;
    });
})


function query(last) {
    $.ajax({
        type: 'POST',
        url: url,   
        data: { word: last },  
        dataType: 'json',
        success: function (data) {            
            let end = data.end;
            let current = $msg.find('p').text();
            $msg.find('p').text(current + ' ' + data.result);            
            let words = data.result.split(' ');
            let last = words[words.length-1];
            if (!end) {                
                query(last);
            }
            else {
                $title.html('Want more? Click again to get another cookie! <br /> &nbsp');
                $cookie.attr('src', '../static/images/open.jpg');
            }
        },        
    });
}

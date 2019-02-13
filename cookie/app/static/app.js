let isOpen = false, $msg, $loader;

$(function () {    
    $msg = $('#msg');
    $loader = $('#loader');
    $loader.hide();
    let $cookie = $('#cookie'),
        $title = $('.title');

    $('body').click(function () {
        if (isOpen) {
            $cookie.attr('src', '../static/images/close.jpg');
            $title.html('Our AI has placed your fortune inside the cookie. <br />Click to open and view it!');            

            $msg.animate({
                height: '0px',
                opacity: 0
            }, 500);
        }
        else {
            $cookie.attr('src', '../static/images/open.jpg');
            $title.html('Want more? Click again to get another cookie! <br /> &nbsp');
            
            let loc = window.location;
            let url = `${loc.protocol}//${loc.hostname}:${loc.port}/gen_sentence`;
            $.ajax({
                type: "POST",
                url: url,          
                beforeSend: function() {
                    $loader.show();
                },
                complete: function(){
                    $loader.hide();
                },  
                success: onSuccess,
                dataType: "json"
            });
        }
        isOpen = !isOpen;
    });
})


function onSuccess(data) {
    let msg = data.result;
    $msg.find('p').text(msg);
    $msg.animate({
        height: '100px',
        opacity: 1
    }, 500);
}

/**
 * Created by anderson on 01/04/15.
 */
$(document).ready(function(){
    //time em milisegundos
    var timer = $.timer(function(){
        $.ajax({
            url: "/khipu/parametros/body",
            type: 'POST',
            context: $("#body_list_parametros"),
            beforeSend:function(){
                $("#dialog_loading_body").css({"height": "70px",
                                                "width": "70px",
                                                "display": "block"});
            },
            success: function(data){
                this.html(" ")
                this.append(data);
                $("#dialog_loading_body").css({"display": "none"});
            }
        });
    });
    timer.set({time: 600000, autostart: true});
    timer.play();
    //imer.stop();
});
/**
 * Created by anderson on 28/03/15.
 */

$(document).ready(function($){
    function criarprojeto(){
                var dados = $("#formdd").serialize()
                console.log("aqui")
                $.ajax({
                    url: "/khipu/criarprojeto",
                    type: 'POST',
                    data: dados,
                    beforeSend:function(){
                        dialog.dialog( "close" );
                        dialog_loading.dialog( "open" );
                    },
                    success: function(data){
                        console.log("CriarProjeto")
                        $("#tab").html(" ")
                        $("#tab").append(data);

                        /*$("#nome_projeto").html("<p style='font-family:verdana;'><em>"+ data.nome_projeto + "<em></p>")
                        $("#chave").html("<p style='font-family:verdana; font-size:10px;'><em>"+ data.chave.slice(0,100) +
                        "<em></br>"+ data.chave.slice(100) + "</p>")
                        $("#data_ativacao").html("<p style='font-family:verdana;'><em>"+ data.data_ativacao + "<em></p>")
                        $("#ativadopor").html("<p style='font-family:verdana;'><em>"+ data.ativado_por + "<em></p>")
                        */
                        dialog_loading.dialog( "close" )
                        $("#meualert").css("display", "block")
                    }
                });
                return true;
            }

    var dialog = $("#dialog_formm").dialog({
                autoOpen: false,
                modal: true,
                buttons:{
                    "Criar Projeto": criarprojeto,
                    Cancel: function() {
                        //form[ 0 ].reset();
                        dialog_loading.dialog( "close");
                        dialog.dialog( "close" );
                        window.location.replace("http://0.0.0.0:6543");
                    }
                },
                close: function() {
                    form[ 0 ].reset();
                    //dialog.dialog( "close" );
                    //window.location.replace("http://0.0.0.0:6543");
                    //allFields.removeClass( "ui-state-error" );
                }

    });

    var dialog_loading = $("#dialog_loading").dialog({
        autoOpen: false,
        modal: true,
        width: 180,
        height: 200
    });

    form = dialog.find( "form" ).on( "submit", function( event ) {
                event.preventDefault();
                criarprojeto();
    });

    $(".ui-dialog-titlebar-close").remove(); //Removendo o botão de fechar do dialog.

    dialog.dialog( "open" ); //Abrindo o dialog.
});

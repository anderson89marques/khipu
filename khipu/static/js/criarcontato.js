/**
 * Created by anderson on 27/03/15.
 */
jQuery(document).ready(function($){
            jQuery("#botao").click(function() {
                var l = jQuery("input[type=checkbox]:checked");
                //alert(""+ l[0].value);
                if (l[0] !== undefined && l !== "") {

                    var dados = jQuery("#formcontato").serialize();
                    var i;
                    dados += "&grupos="
                    for (i = 0; i < l.length; i++) {
                        dados += "" + l[i].value + ","
                    }

                    alert(dados)
                    jQuery.ajax({
                        url: "/salvarcontatos",
                        type: 'POST',
                        data: dados,
                        //context: jQuery("#divlistgrupos"),
                        success: function (data) {
                            //this.html(" ")
                            //this.append(data);
                            jQuery("#formcontato");
                            alert("Criado com sucesso!!");
                        }
                    });
                }else{
                    alert("Selecione um grupo")
                }
            });
            var form;

            function criargrupo(){
                var dados = $("#formd").serialize()
                jQuery.ajax({
                    url: "/criargrupo",
                    type: 'POST',
                    data: dados,
                    context: jQuery("#divlistgrupos"),
                    success: function(data){
                        this.html(" ")
                        this.append(data);
                        dialog.dialog( "close" );
                        /*alert("");*/
                    }
                });
                return true;
            }

            var dialog = $("#dialog_form").dialog({
                autoOpen: false,
                height: 300,
                width: 350,
                modal: true,
                buttons:{
                    "Criar grupo": criargrupo,
                    Cancel: function() {
                        dialog.dialog( "close" );
                    }
                },
                close: function() {
                    form[ 0 ].reset();
                    //allFields.removeClass( "ui-state-error" );
                }
            });

             form = dialog.find( "form" ).on( "submit", function( event ) {
                 event.preventDefault();
                 criargrupo();
             });

            jQuery("#criargrupo").click(function(event){
                dialog.dialog( "open" );
                //alert("Criar Grupo")
            });

        });
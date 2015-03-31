/**
 * Created by anderson on 27/03/15.
 */
jQuery(document).ready(function(){
            var i;
            var dados;
            jQuery("#jstree").jstree({"plugins" : [ "checkbox" ]});
            jQuery('#jstree').on("changed.jstree", function (e, data) {
                console.log(data.selected);
                //console.log(data.selected[i].slice(0,5));
                //criei um objeto jQuery para colocar os ids das pessoas selecionadas e posteriormente, a mesagem a ser enviada
                dados = {};
                var cont=0; //pra adicionar no objeto com uma ordem certinha. ex: 0,1,2 e não 1,2,4 por exemplo.
                for(i=0; i < data.selected.length; i++){
                    if( !(data.selected[i].slice(0,5) === "grupo")){
                        dados[cont] = data.selected[i];
                        cont++;
                    }
                }
                console.log(dados);
            });
            // 8 interact with the tree - either way is OK
            jQuery('button').on('click', function () {
              jQuery('#jstree').jstree(true).select_node('child_node_1');
              jQuery('#jstree').jstree('select_node', 'child_node_1');
              jQuery.jstree.reference('#jstree').select_node('child_node_1');
            });

            jQuery("#botaomsg").click(function(e){
                var msg = jQuery("#textmensagem").val();
                console.log(msg)
                dados["men"] = msg; //adicionando a mensagem no objeto que contém também os ids das pessoas que iram recebe-lá
                jQuery.ajax({url:"/mensagem/enviarmensagem",
                    data: dados,
                    type:"POST",
                    success: function(data){
                        alert(data.mensagem)
                    }
                });
            });
});

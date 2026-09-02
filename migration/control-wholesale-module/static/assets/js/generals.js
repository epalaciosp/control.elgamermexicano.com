$('select').select2();
$('.select2-selection').css('height','43px')

function getCookie(name) {
    const cookie = document.cookie
        .split(';')
        .map(function (item) { return item.trim(); })
        .find(function (item) { return item.startsWith(name + '='); });
    return cookie ? decodeURIComponent(cookie.substring(name.length + 1)) : null;
}

function getCsrfToken() {
    const cookieToken = getCookie('csrftoken');
    if (cookieToken) {
        return cookieToken;
    }
    const input = document.querySelector('[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
}

function csrfPost(url, data) {
    return $.ajax({
        url: url,
        type: 'POST',
        data: data,
        headers: {'X-CSRFToken': getCsrfToken()}
    });
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        const safeMethod = /^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type);
        if (!safeMethod && !settings.crossDomain) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        }
    }
});

function showWhatsappError(xhr) {
    let message = 'No fue posible enviar el mensaje por WhatsApp.';
    if (xhr.status === 403) {
        message = 'La sesión expiró. Recarga la página e intenta nuevamente.';
    } else if (xhr.responseText && xhr.responseText.length < 300) {
        message = xhr.responseText;
    }
    alert(message);
}

function showCutError(xhr) {
    let message = 'No fue posible cortar el servicio.';
    if (xhr.status === 403) {
        message = 'La sesión expiró o no tienes permiso. Recarga la página e intenta nuevamente.';
    } else if (xhr.status === 405) {
        message = 'La página tiene una versión anterior. Recárgala por completo e intenta nuevamente.';
    } else if (xhr.responseText && xhr.responseText.length < 300) {
        message = xhr.responseText;
    }
    alert(message);
}

$('body').on("submit", "form" , function(event){
        $(this).find('input[type="submit"]').prop("disabled", true)
})
$(document).ready(function() {
    $('.table-normal').DataTable( {
          responsive: true,
          ordering: true,
          stateSave: true,
          language: {
            processing:     "Procesamiento en curso...",
            search:         "Buscar&nbsp;:",
            lengthMenu:     "Mostrar _MENU_ &eacute;l&eacute;mentos",
            info:           "Mostrar de elelemento _START_ al _END_,     Total _TOTAL_ ",
            infoEmpty:      "Visualización del elemento 0 a 0 de 0 artículos",
            infoFiltered:   "(filtrados _MAX_ elementos del total)",
            infoPostFix:    "",
            loadingRecords: "Procesamiento en curso...",
            zeroRecords:    "No hay elementos para mostrar",
            emptyTable:     "No se encotraron elementos",
            paginate: {
                first:      "Primera",
                previous:   "Anterior",
                next:       "Próxima",
                last:       "Ültima"
            },
            aria: {
                sortAscending:  ": activar para ordenar la columna en orden ascendente",
                sortDescending: ": activar para ordenar la columna en orden descendente"
            }
        }
    });

    $('.table-no-cache').DataTable( {
          responsive: true,
          ordering: true,
          order: [[8, 'desc']],
          stateSave: false,
          language: {
            processing:     "Procesamiento en curso...",
            search:         "Buscar&nbsp;:",
            lengthMenu:     "Mostrar _MENU_ &eacute;l&eacute;mentos",
            info:           "Mostrar de elelemento _START_ al _END_,     Total _TOTAL_ ",
            infoEmpty:      "Visualización del elemento 0 a 0 de 0 artículos",
            infoFiltered:   "(filtrados _MAX_ elementos del total)",
            infoPostFix:    "",
            loadingRecords: "Procesamiento en curso...",
            zeroRecords:    "No hay elementos para mostrar",
            emptyTable:     "No se encotraron elementos",
            paginate: {
                first:      "Primera",
                previous:   "Anterior",
                next:       "Próxima",
                last:       "Ültima"
            },
            aria: {
                sortAscending:  ": activar para ordenar la columna en orden ascendente",
                sortDescending: ": activar para ordenar la columna en orden descendente"
            }
        }
    });


});

$("#myModal").on("click", ".close-modal", function () {
   window.location.href = '/count/sales/list';
});


function convertFormToJSON(form) {
  return $(form)
    .serializeArray()
    .reduce(function (json, { name, value }) {
      json[name] = value;
      return json;
    }, {});
}


//function get_charges_sales(username){
//
//    $('#search_inter_dates').click(function(event){
//		event.preventDefault()
//		initial_date = $('#id_init_date').val()
//		final_date = $('#id_final_date').val()
//
//		if (username != ""){
//            $.get('/count/sales/'+username+'/'+initial_date+'/'+final_date, function(data){
//                $('#sales-list').html(data)
//            })
//		}else{
//		    $.get('/count/sales/'+initial_date+'/'+final_date, function(data){
//			    $('#sales-list').html(data)
//		    })
//		}
//
//	})
//}



$( function() {

    // There's the gallery and the trash
    var $gallery = $( "#gallery" ),
      $trash = $( "#trash" );

    // Let the gallery items be draggable
    $( "li", $gallery ).draggable({
      cancel: "a.ui-icon", // clicking an icon won't initiate dragging
      revert: "invalid", // when not dropped, the item will revert back to its initial position
      containment: "document",
      helper: "clone",
      cursor: "move"
    });

    // Let the trash be droppable, accepting the gallery items
    $trash.droppable({
      accept: "#gallery > li",
      classes: {
        "ui-droppable-active": "ui-state-highlight"
      },
      drop: function( event, ui ) {
        Add_platform( ui.draggable );
      }
    });

    // Let the gallery be droppable as well, accepting items from the trash
    $gallery.droppable({
      accept: "#trash li",
      classes: {
        "ui-droppable-active": "custom-state-active"
      },
      drop: function( event, ui ) {
        recycleImage( ui.draggable );
      }
    });

    // Image deletion function
    var recycle_icon = "<a href='link/to/recycle/script/when/we/have/js/off' title='Recycle this image' class='ui-icon ui-icon-refresh'>Recycle image</a>";

    function Add_platform( $item ) {
      $item.fadeOut(function() {
        var $list = $( "ul", $trash ).length ?
        $( "ul", $trash ) :
        $( "<ul class='gallery ui-helper-reset'/>" ).appendTo( $trash );

        $item.find( "a.ui-icon-trash" ).remove();
        $item.append( recycle_icon ).appendTo( $list ).fadeIn(function() {
          $item.animate({ width: "165px" })
          platform_name = $item.attr('platform_name')
          $("input[name='platforms'][value='"+platform_name+"']").prop("checked", true);
        });
      });
    }

    // Image recycle function
    var trash_icon = "<a href='link/to/trash/script/when/we/have/js/off' title='Delete this image' class='ui-icon ui-icon-trash'>Delete image</a>";
    function recycleImage( $item ) {
      $item.fadeOut(function() {
        $item
          .find( "a.ui-icon-refresh" )
            .remove()
          .end()
          .css( "width", "165px")
          .find( "img" )
            .css( "height", "150px" )
          .end()
          .appendTo( $gallery )
          .fadeIn();
         platform_name = $item.attr('platform_name')
         $("input[name='platforms'][value='"+platform_name+"']").prop("checked", false);

      });
    }

    // Image preview function, demonstrating the ui.dialog used as a modal window

    // Resolve the icons behavior with event delegation
    $( "ul.gallery > li" ).on( "click", function( event ) {
      var $item = $( this ),
        $target = $( event.target );
      if ( $target.is( "a.ui-icon-trash" ) ) {
        Add_platform( $item );
      } else if ( $target.is( "a.ui-icon-refresh" ) ) {
        recycleImage( $item );
      }
      return false;
    });
} );


$('.platforms').on("change", "#id_platform" , function(){

      $('#profiles-content').html('')
      platform_id = $(this).val()
      const formPurpose = $(this).closest('form').data('purpose');
      const purposeQuery = formPurpose ? '?purpose=' + encodeURIComponent(formPurpose) : '';
      $.get('/count/create-pins-profiles/platform/'+platform_id)
       .done(function( data ) {
           $('#profiles').html(data)
      });
      $.get('/count/select-plan-by-platform/'+platform_id+purposeQuery)
       .done(function( data ) {
            $('#plans').html(data)
            var count_options = $("#id_plan option").length;
            if (count_options == 0){
                $.get('/count/get-profiles-available/'+platform_id )
                   .done(function( data ) {
                       $('#profiles-content').html(data)
                 });
            }
      });
})

function create_sale(){

    $('.platforms').on("change", "#id_plan" , function(){
      plan_id = $(this).val()
      $.get('/count/get-profiles-available/plan/'+plan_id )
        .done(function( data ) {
          $('#profiles-content').html(data)
      });

    })
}

function create_count(){

    $('.platforms').on("change", "#id_plan" , function(){
      plan_id = $(this).val()
      $.get('/count/create-pins-profiles/plan/'+plan_id)
       .done(function( data ) {
           $('#profiles').html(data)
      });

    })
}



$('body').off("click.cutService", ".cut-profile")
    .on("click.cutService", ".cut-profile", function(event){
      event.preventDefault();
      const button = $(this);
      const idProfile = button.attr('id_profile');
      const idSale = button.attr('id_sale');

      if (!window.confirm('¿Deseas cortar completamente este servicio y liberar el perfil?')) {
          return;
      }

      button.prop('disabled', true);
      csrfPost('/count/cut-profile/' + idSale + '/' + idProfile)
       .done(function(data) {
           alert(data);
           location.reload();
       })
       .fail(function(xhr) {
           showCutError(xhr);
           button.prop('disabled', false);
       });
    });

$('body').on("click", ".change-profile-sale" , function(){

     sale_id = $(this).attr('id_sale')
    $.get('/count/change-profile-sale/'+sale_id)
       .done(function( data ) {
           $('.modal-body').html(data)
           $("#myModal").modal({
                show: true,
                escapeClose: false,
                clickClose: false
                })
       })
       $("#myModal").on('hide.bs.modal', function (e) {
           location.reload();
        });

});



$(".owner-profile").on("click", function() {

      id_profile = $(this).attr('id_profile');
      id_sale = $(this).attr('id_sale');
      $.get('/count/owner-profile/'+id_sale+'/' +id_profile )
       .done(function( data ) {
           alert(data)
           location.reload();
       });
})



$(".table-list_count").on("click", ".change-password" , function(){
    count_id = $(this).attr('id_count')
    $.get('/count/change-password/'+count_id)
      .done(function( data ) {
            $('.modal-body').html(data)
            $('.modal-title').text("Solicitud")
            $('.modal-footer').hide()
            $("#myModal").modal({
                show: true,
                escapeClose: false,
                clickClose: false
                })
            $('.change-pass').click(function(e){
              e.preventDefault()
              json = convertFormToJSON($('.change-password-form'))
              $.post('/count/change-password/'+count_id, json)
                .done(function( data ) {
                  $('.modal-body').html(data)
              })
            })
            $("#myModal").on('hide.bs.modal', function (e) {
              location.reload();
            });
        });

})


$(".table-list-count-to-expire").on("click", ".change-date-limit" , function(){
    count_id = $(this).attr('id_count')
    $.get('/count/change-date-limit/'+count_id)
      .done(function( data ) {
            $('.modal-body').html(data)
            $('.modal-title').text("Solicitud")
            $('.modal-footer').hide()
            $('#id_date_limit').attr('type','date')
            const date = new Date();
            let day = date.getDate();
            let month = date.getMonth() + 1;
            let year = date.getFullYear();
            let currentDate = `${day}/${month}/${year}`;
            $('#id_date_limit').attr('min',currentDate)
            $("#myModal").modal({
                show: true,
                escapeClose: false,
                clickClose: false
                })
            $('.change-date-limit').click(function(e){
              e.preventDefault()
              json = convertFormToJSON($('.change-date-limit-form'))
              format_currenday = `${year}-${month}-${day}`;
              const fechaInput = new Date(json.date_limit);
              console.log(date)
              console.log(fechaInput)
              if ( date >= fechaInput){
                $('#id_date_limit').val("")
                alert('Fecha invalida, tiene que ser mayor al dia de hoy    ')
              }else{
                  $.post('/count/change-date-limit/'+count_id, json)
                    .done(function( data ) {
                      $('.modal-body').html(data)
                  })
              }
            })
            $("#myModal").on('hide.bs.modal', function (e) {
              location.reload();
            });
        });

})


function send_message(url, data ){

    $('body').off("click.whatsapp", ".send-message")
    $('body').on("click.whatsapp", ".send-message" , function(){
        const button = $(this)
        button.prop('disabled', true)

        $.ajax({
            url: url,
            type: "POST",
            dataType: "text",
            data: JSON.stringify(data),
            contentType: "application/json",
            headers: {"X-CSRFToken": getCsrfToken()},
            success: function (response) {

                alert(response)
                window.location.href = "/user/list-customer";
            },
            error: function (xhr) {
                showWhatsappError(xhr)
                button.prop('disabled', false)
            }
        });
        $("#myModal").on('hide.bs.modal', function (e) {
          location.reload();
        });
    });
}

function count_functions(){


     $('body').off("click.cancelService", ".calcel-sale")
       .on("click.cancelService", ".calcel-sale", function(event){
         event.preventDefault();
         const button = $(this);
         const saleId = button.attr('sale');

         if (!window.confirm('¿Deseas cortar completamente este servicio y liberar el perfil?')) {
             return;
         }

         button.prop('disabled', true);
         csrfPost('/count/sale/cancel-sale/' + saleId)
            .done(function(data) {
                alert(data);
                location.reload();
            })
            .fail(function(xhr) {
                showCutError(xhr);
                button.prop('disabled', false);
            });
       });

     $(".renew").click(function(e){
        e.preventDefault()
        months = $('#months').val()
        if(months != ""){
            $(".sales").submit()
        }else{
            alert("Debe ingresar los meses de renovación")
        }
     })
     $(".update").click(function(e){
        e.preventDefault()
        $(".customer").submit()
     })

     function visibleRenewInputs(){
         const tableInputs = $('#customer-services-table tbody tr:visible .renew_input');
         return tableInputs.length ? tableInputs : $('.renew_input:visible');
     }

     function syncRenewalPanel(){
         const hasSelection = visibleRenewInputs().filter(':checked').length > 0;
         $('.renewal-panel, .renewal-controls').toggle(hasSelection);
     }

     function syncRenewAllCheckbox(){
         const inputs = visibleRenewInputs();
         const selected = inputs.filter(':checked').length;
         $('#renew_all_list')
             .prop('checked', inputs.length > 0 && selected === inputs.length)
             .prop('indeterminate', selected > 0 && selected < inputs.length);
     }

     // DataTables detaches and reattaches rows while searching or paginating.
     // Delegated events keep renewal controls working after every redraw.
     $('body').off('change.customerRenew', '.renew_input')
       .on('change.customerRenew', '.renew_input', function(){
           syncRenewalPanel();
           syncRenewAllCheckbox();
       });

     $('body').off('change.customerRenewAll', '#renew_all_list')
       .on('change.customerRenewAll', '#renew_all_list', function(){
           visibleRenewInputs().prop('checked', $(this).prop('checked'));
           syncRenewalPanel();
           syncRenewAllCheckbox();
       });

     $('#customer-services-table').off('draw.dt.customerRenew')
       .on('draw.dt.customerRenew', function(){
           syncRenewalPanel();
           syncRenewAllCheckbox();
       });


     $('body').on("click", ".change-password" , function(){
        count_id = $(this).attr('id_count')
        $.get('/count/edit-count-data/count/'+count_id)
          .done(function( data ) {
                $('.modal-body').html(data)
                $('.modal-title').text("Solicitud")
                $('.modal-footer').hide()
                $("#myModal").modal({
                    show: true,
                    escapeClose: false,
                    clickClose: false
                    })
                $('.change-pass').click(function(e){
                  e.preventDefault()
                  json = convertFormToJSON($('.change-password-form'))
                  $.post('/count/edit-count-data/count/'+count_id, json)
                    .done(function( data ) {
                      $('.modal-body').html(data)
                  })
                })
                $("#myModal").on('hide.bs.modal', function (e) {
                  location.reload();
                });
            });
          });


     $('body').off("click.changeSaleOpen", ".change-sale")
       .on("click.changeSaleOpen", ".change-sale" , function(event){
        event.preventDefault()
        const saleId = $(this).attr('id_sale')
        $.get('/count/edit-sale-data/'+saleId)
          .done(function( data ) {
                $('.modal-body').html(data)
                $('.modal-title').text("Editar fechas de venta")
                $('.modal-footer').hide()
                $("#myModal").modal({
                    show: true,
                    escapeClose: false,
                    clickClose: false
                    })
                $("#myModal").on('hide.bs.modal', function (e) {
                  location.reload();
                });
            });
       });

     // Delegation keeps this active when validation replaces the modal HTML.
     // The explicit form action also makes the non-JavaScript fallback safe.
     $('body').off("submit.changeSale", ".change-sale-form")
       .on("submit.changeSale", ".change-sale-form", function(event){
          event.preventDefault()
          const form = $(this)
          const button = form.find('.changer-sale')
          const endpoint = form.attr('action')
          button.prop('disabled', true).text('Guardando...')
          csrfPost(endpoint, convertFormToJSON(form))
            .done(function(data) {
              $('.modal-body').html(data)
            })
            .fail(function(xhr) {
              const message = xhr.responseText || 'No se pudo actualizar la fecha.'
              $('.modal-body').prepend(
                $('<div>', {class: 'alert alert-danger', text: message})
              )
              button.prop('disabled', false).text('Guardar')
            })
       });
}

function change_password(){

    $('body').on("click", ".change-password" , function(){

        count_id = $(this).attr('id_count')
        $.get('/count/change-password/count/'+count_id)
          .done(function( data ) {
                $('.modal-body').html(data)
                $('.modal-title').text("Solicitud")
                $('.modal-footer').hide()
                $("#myModal").modal({
                    show: true,
                    escapeClose: false,
                    clickClose: false
                    })
                $('.change-pass').click(function(e){
                  e.preventDefault()
                  json = convertFormToJSON($('.change-password-form'))
                  $.post('/count/change-password/count/'+count_id, json)
                    .done(function( data ) {
                      $('.modal-body').html(data)
                  })
                })
                $("#myModal").on('hide.bs.modal', function (e) {
                  location.reload();
                });
            });
          });

      $('body').off("click.deleteCount", ".delete-count")
        .on("click.deleteCount", ".delete-count", function(event){
            event.preventDefault();
            const button = $(this);
            const countId = button.attr('id_count');
            const confirmed = window.confirm(
                "¿Deseas borrar definitivamente esta cuenta y todos sus perfiles?"
            );

            if (!confirmed) {
                return;
            }

            button.prop('disabled', true);
            csrfPost('/count/' + countId + '/delete/')
                .done(function(data) {
                    alert(data);
                    location.reload();
                })
                .fail(function(xhr) {
                    let message = "No fue posible eliminar la cuenta.";
                    if (xhr.status === 403) {
                        message = "La sesión expiró o no tienes permiso para eliminar cuentas.";
                    } else if (xhr.responseText && xhr.responseText.length < 300) {
                        message = xhr.responseText;
                    }
                    alert(message);
                    button.prop('disabled', false);
                });
       });

}


function change_password_email(){

    $('body').on("click", ".change-password-email" , function(){

         count_id = $(this).attr('id_count')
         $.get('/count/change-password/email/'+count_id)
          .done(function( data ) {
                $('.modal-body').html(data)
                $('.modal-title').text("Solicitud")
                $('.modal-footer').hide()

                $("#myModal").modal({
                    show: true,
                    escapeClose: false,
                    clickClose: false
                })

                $('.change-pass').click(function(e){
                  e.preventDefault()
                  json = convertFormToJSON($('.change-password-form'))
                  $.post('/count/change-password/email/'+count_id, json)
                    .done(function( data ) {
                      $('.modal-body').html(data)
                  })
                })
                $("#myModal").on('hide.bs.modal', function (e) {
                    location.reload();
                });
            });
          });

}


function send_message_individual(data){

    if (window.whatsappSendInProgress) {
        return;
    }
    window.whatsappSendInProgress = true;
    const button = $(document.activeElement).closest('button');
    const originalButtonHtml = button.html();
    button.prop('disabled', true).html('<i class="mdi mdi-loading mdi-spin"></i> Enviando...');

    $.ajax({
        url: '/count/send-whatsapp-message',
        type: "POST",
        dataType: "text",
        data: JSON.stringify(data),
        contentType: "application/json",
        headers: {'X-CSRFToken': getCsrfToken()},
        success: function (response) {
            button.html('<i class="mdi mdi-check"></i> Enviado');
            window.setTimeout(function () {
                button.prop('disabled', false).html(originalButtonHtml);
            }, 1600);
        },
        error: function (xhr) {
            showWhatsappError(xhr)
            button.prop('disabled', false).html(originalButtonHtml);
        },
        complete: function () {
            window.whatsappSendInProgress = false;
        }
    });

}

function send_message_expired(data){

    $.ajax({
        url: '/count/send-whatsapp-expired',
        type: "POST",
        dataType: "text",
        data: JSON.stringify(data),
        contentType: "application/json",
        headers: {'X-CSRFToken': getCsrfToken()},
        success: function (response) {
            $("#"+response).text("Enviado");
        },
        error: function (xhr) {
            showWhatsappError(xhr)
        }
    });

}

$(document).ready(function() {

  $('input[type="submit"]').click( function(e) {
    e.preventDefault();
    $.ajax( {
      type: "POST",
      url: "{{ form_target }}",
      data: $("form").serialize(),
      success: function( response ) {
        $( "div.success" ).fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
      },
      error: function( response ) {
        $( "div.failure" ).fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
      }
    });
    return false;
  });
});

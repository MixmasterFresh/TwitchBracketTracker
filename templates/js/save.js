$(document).ready(function() {

  $('form').submit( function(e) {
    e.preventDefault();
    console.log(e.target.action)
    $.ajax( {
      type: "POST",
      url: e.target.action,
      data: $(this).serialize(),
      success: function( response ) {
        $( "span.success" ).css('display', 'block').fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
      },
      error: function( response ) {
        console.log(response)
        $( "span.failure" ).text(response.responseText).css('display', 'block').fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
      }
    });
    return false;
  });
});

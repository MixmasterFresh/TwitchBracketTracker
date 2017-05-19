$("#record").click(function(e) {
    e.preventDefault();
    if(e.target.value == "ON"){
        $.ajax({
            type: "GET",
            url: "/admin/stop_recording/{{match.id}}",
            data: {},
            success: function(result) {
                e.target.value = "OFF";
                e.target.classList.remove('recording');
                e.target.innerText = "Record";
            },
            error: function(result) {
                alert(result.responseText);
                console.log(result);
            }
        });
    }else{
        $.ajax({
            type: "GET",
            url: "/admin/start_recording/{{match.id}}",
            data: {},
            success: function(result) {
                e.target.value = "ON";
                e.target.innerText = "Stop Recording";
                e.target.classList.add('recording');
            },
            error: function(result) {
                alert(result.responseText);
                console.log(result);
            }
        });
    }
});

$('#delete').click(function(e) {
    e.preventDefault();
    var result = confirm("Are you sure that you\nwant to delete this video?");
    if (result) {
        $.ajax({
            type: "GET",
            url: "/admin/delete_video/{{match.id}}",
            data: {},
            success: function(result) {
                $( "div.success" ).fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
            },
            error: function(result) {
                alert(result.responseText);
                console.log(result);
            }
        });
    }
});

$(document).ready(function() {
  $('input[type="checkbox"]').on('change', function() {
    $('input[type="checkbox"]').not(this).prop('checked', false);
  });
});


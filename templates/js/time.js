if (!sessionStorage.getItem('timezone')) {
  var tz = jstz.determine() || 'UTC';
  sessionStorage.setItem('timezone', tz.name());
}
var currTz = sessionStorage.getItem('timezone');

// References to DOM elements
var inputTime = document.querySelector("#input-time");
var output = document.querySelector("#local");

function localizeTime(theTime) {
  var date = moment().format("YYYY-MM-DD");
  var stamp = date + "T" + theTime + "Z";
  // Create a Moment.js object
  var momentTime = moment(stamp);
  // Adjust using Moment Timezone
  var tzTime = momentTime.tz(currTz);
  // Format the time back to normal
  return tzTime.format('h:mm a');
}

$(document).ready( function(){
  $('.time').each(function(i, obj) {
    obj.innerHTML = localizeTime(obj.getAttribute("value"))
  });

  $('.timezone').each(function(i, obj) {
    obj.innerHTML = moment.tz(sessionStorage.getItem('timezone')).format('z [(UTC ]Z[)]');
  });
});

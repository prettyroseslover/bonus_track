$(document).ready(function() {
	$('form').on('submit', function(event) {
	  $.ajax({
		 data : {
			Name : $('#Name').val(),
			Telegram: $('#Telegram').val(),
			msg_text: $('#msg_text').val(),
				},
			type : 'POST',
			url : '/telegram'
		   })
	   .done(function(data) {
		setTimeout(function() {
				// Done Functions
				th.trigger("reset");
			}, 1000);
		 $('#output').text(data.output).show();
		 $('#Name').val('');
		 $('#Telegram').val('');
		 $('#msg_text').val('');
		 document.getElementById("myModal").style.display = "none";
		 //$("#popup1").hide();

	 });
	 event.preventDefault();
	 });
});

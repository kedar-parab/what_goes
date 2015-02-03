<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.0/jquery.min.js"></script>
<script type="text/javascript" >
	$(function() {
		$(".submit").click(function() {
			$('.success').fadeIn(200).show();
			/*var name = $("#name").val();
			var username = $("#username").val();
			var password = $("#password").val();
			var gender = $("#gender").val();
			var dataString = 'name='+ name + '&username=' + username + '&password=' + password + '&gender=' + gender;

			if(name=='' || username=='' || password=='' || gender=='')
				{
				$('.success').fadeOut(200).hide();
				$('.error').fadeOut(200).show();
				}
			else*/
			//{}
			var dataString = 'test=123';
				$.ajax({
					type: "POST",
					url: "vote",
					data: dataString,
					success: function(){
						$('.success').fadeIn(200).show();
						$('.error').fadeOut(200).hide();
					}
				});
			//}
			return false;
		});
	});
</script>
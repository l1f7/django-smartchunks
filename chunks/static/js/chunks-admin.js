(function($){
	$(document).ready(function($){
		var field = '-chunk_type';

		// choose builder from text as current widget builder
		$('.chunks-type').each(function(){
			var typeInput = $(this);
			var prefix = $(this).attr('name').replace(field, '');
			$('*[name^="' + prefix + '-content"]').each(function(){
				var re = new RegExp('chunk\=([A-Za-z0-9\-\_]+)');
				var builder = re.exec($(this).val());
				if(builder != null && builder.length > 1){
					$('option', typeInput).removeAttr('selected');
					typeInput.val(builder[1]);
					return false;
				}
			});
		});

		// change builder type
		$('.chunks-type').change(function(){
			var bldrId = $(this).val();
			var inline = bldrId.length > 0 ? 'chunk=' + bldrId : '';
			var prefix = $(this).attr('name').replace(field, '');

			$('*[name^="' + prefix + '-content"]').each(function(){
				var re = new RegExp('chunk\=[A-Za-z0-9\-\_]+');
				var data = $(this).val().replace(re, inline);

				if(data.indexOf(inline) < 0){
					$(this).val(inline + '\n' + data);
				}else{
					$(this).val(data);
				}
			});
		});
	});
})(django.jQuery);
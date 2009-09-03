var letters = 'ABCDEFGHIJKLMNOPQRTSUVWXYZ ';
var goodkeys = [9,32,37,38,39,40];
$(function(){
	$('input.puzzlechar').keyup(function(event){
		$(this).val(this.value.toUpperCase());
		var idp = this.id.split('_'); // char,y,x
		var x = idp[2];
		var y = idp[1];
		switch (event.keyCode) {
			case 9: // tab
				//if (event.shiftKey) { x--; } else { x++; }
				break;
			case 32: // space
				$(this).val('#').parent('td').toggleClass('blocked');
				break;
			case 37: // left
				x--;
				break;
			case 38: // up
				y--;
				break;
			case 39: // right
				x++;
				break;
			case 40: // down
				y++;
				break;
			default:
				x++;
		}
		if (x>maxx) {
			x=1;
			y++;
		} else if (x<1) {
			x=maxx;
			y--;
		}
		if (y>maxy) {
			y=1;
		} else if (y<1) {
			y=maxy;
		}
		if ( ( (event.keyCode > 64) && (event.keyCode < 91) ) || ( goodkeys.indexOf(event.keyCode) !== -1 ) ) {
			$('#char_'+y+'_'+x).focus().select();
		} else {
			$(this).val('');
		}
		event.preventDefault();
		return true;
	});
});

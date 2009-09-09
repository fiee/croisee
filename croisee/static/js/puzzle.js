var letters = 'ABCDEFGHIJKLMNOPQRTSUVWXYZ ';
var goodkeys = [9,32,37,38,39,40,27];

function getWord(x,y,maxx,maxy) {
	/*
	 * parameters are relative to the grid
	 * x, y = position of query in the grid, 1-based
	 * maxx, maxy = size of the grid
	 * 
	 * xpos, ypos = position of the query, relative to word, 0-based
	 * 
	 */
	var horiz='';
	var vert='';
	var letter = '';
	var xpos = x-1;
	var ypos = y-1;
	for (i=1; i<=maxx; i++) {
		letter = $('#char_'+y+'_'+i).val()
		if (letter == '') {
			letter = '_';
		} 
		if (letter == '.') {
			if (i < x) {
				horiz = '';
				xpos = x-i-1;
			} else if (i > x) {
				break;
			}
		} else {
			horiz += letter;
		}
	}
	for (i=1; i<=maxy; i++) {
		letter = $('#char_'+i+'_'+x).val();
		if (letter == '') {
			letter = '_';
		} 
		if (letter == '.') {
			if (i<y) {
				vert = '';
				ypos = y-i-1;
			} else if (i>y) {
				break;
			}
		} else {
			vert += letter;
		}
	}
	var query = '/ajax/'+horiz+','+xpos+'/'+vert+','+ypos+'/';
	return $.get(query, {}, function(data){
		console.log(data);
		$('#result').html(data);
	}, 'html');
	// TODO: make result clickable and insert on click, then requery
}

$(function(){
	var maxx = Number($('input#maxx').val());
	var maxy = Number($('input#maxy').val());
	$('input.puzzlechar').keyup(function(event){
		//console.log(event.keyCode);
		event.preventDefault();
		$(this).val(this.value.toUpperCase());
		var idp = this.id.split('_'); // char,y,x
		var x = idp[2];
		var y = idp[1];
		switch (event.keyCode) {
			case 9: // tab
				//if (event.shiftKey) { x--; } else { x++; }
				break;
			case 32: // space
				$(this).val('.').parent('td').toggleClass('blocked');
				x++;
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
			case 27: // escape
				// TODO: change to other key
				console.log(getWord(x,y,maxx,maxy));
				break;
			default:
				$(this).parent('td').removeClass('blocked');
				x++;
		}
		if (x>maxx) {
			x=1;
			//y++;
		} else if (x<1) {
			x=maxx;
			//y--;
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
		return true;
	});
	$('input.numeric').keyup(function(event){
		event.preventDefault();
		var num = Number(this.value);
		if (isNaN(num)) num=0;
		$(this).val(num);
	});
});

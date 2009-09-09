var letters = 'ABCDEFGHIJKLMNOPQRTSUVWXYZ ';
var goodkeys = [9,32,37,38,39,40,46,51,191];
var modifiers = [16,17,18,91];

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
		$('#result').html(data);
	}, 'html');
	// TODO: make result clickable and insert on click
}

function renumberPuzzle(x,y,maxx,maxy,reset) {
	var id = '#num_'+y+'_'+x;
	if (reset||$(id).html()) {
		$(id).html('');
	} else {
		$(id).html('#');
	}
	var num=1;
	for (cy=1; cy<=maxy; cy++) {
		for (cx=1; cx<=maxx; cx++) {
			var nf = $('#num_'+cy+'_'+cx);
			if (nf.html()) {
				nf.html(num++);
			}
		}
	}
}

$(function(){
	var maxx = Number($('input#maxx').val());
	var maxy = Number($('input#maxy').val());
	$('input.puzzlechar').keypress(function(event){
		/* handle character keys A-Z */
		if ( modifiers.indexOf(event.keyCode) < 1 ) { // no modifiers except shift
			event.preventDefault();
			if ((65 <= event.which && event.which <= 65 + 25) 
				|| (97 <= event.which && event.which <= 97 + 25)) {
		        var c = String.fromCharCode(event.which).toUpperCase();
				$(this).val(c);
				//console.log(event.keyCode, c);
			}
			return false;
		}
	});
	$('input.puzzlechar').keyup(function(event){
		/* handle any other keys */
		//console.log(event.keyCode, 'UP');
		var idp = this.id.split('_'); // char,y,x
		var x = idp[2];
		var y = idp[1];
		switch (event.keyCode) {
			case 8: // backspace
				$(this).val('');
				x--;
				break;
			case 9: // tab
				//if (event.shiftKey) { x--; } else { x++; }
				break;
			case 32: // space
				$(this).val('.').parent('td').toggleClass('blocked');
				renumberPuzzle(x,y,maxx,maxy,true);
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
			case 46: // forward delete
				$(this).val('');
				x++;
				break;
			case 51: // number sign #
				renumberPuzzle(x,y,maxx,maxy,false);
				break;
			case 191: // escape
				getWord(x,y,maxx,maxy);
				break;
			default:
				$(this).parent('td').removeClass('blocked');
				if (event.shiftKey) { y++; } else { x++; }
		}
		if (x>maxx) {
			x=1;
		} else if (x<1) {
			x=maxx;
		}
		if (y>maxy) {
			y=1;
		} else if (y<1) {
			y=maxy;
		}
		event.preventDefault();
		if ( modifiers.indexOf(event.keyCode) == -1 ) {
			$('#char_'+y+'_'+x).focus().select();
		}
		return true;
	});
	$('input.numeric').keyup(function(event){
		/* handle numeric input fields */
		event.preventDefault();
		var num = Number(this.value);
		if (isNaN(num)) num=0;
		$(this).val(num);
	});
});

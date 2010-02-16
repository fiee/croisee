var letters = 'ABCDEFGHIJKLMNOPQRTSUVWXYZ ';
var goodkeys = [9,32,37,38,39,40,46,51,191];
var modifiers = [16,17,18,91];

function getWord(x,y,maxx,maxy) {
	/*
	 * parameters are relative to the grid
	 * x, y 			= position of query in the grid, 1-based
	 * maxx, maxy 		= size of the grid
	 * xstart, ystart 	= start of the word, relative to the grid, 1-based
	 * xpos, ypos 		= position of the query, relative to word, 0-based
	 * 
	 */
	$('#result').html('');
	var horiz='';
	var vert='';
	var letter = '';
	var xpos = x-1;
	var ypos = y-1;
	var xstart = 0;
	var ystart = 0;
	for (i=1; i<=maxx; i++) {
		letter = $('#char_'+y+'_'+i).val()
		if (letter == '') {
			letter = '_';
		} 
		if (letter == '.') {
			if (i < x) {
				horiz = '';
				xpos = x-i-1;
				xstart = i;
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
				ystart = i;
			} else if (i>y) {
				break;
			}
		} else {
			vert += letter;
		}
	}
	var query = '/ajax/'+horiz+','+xpos+'/'+vert+','+ypos+'/';
	var context = {};
	var count = 0;
	$('input.dictionary-checkbox:checked').each(function(i){
		context[this.id] = true;
		count++;
	});
	if (count==0) {
		$('#result').html('<p class="error">Chose a dictionary!</p>'); // TODO: i18n
		return;
	}
	return $.post(query, context, function(data){
		$('#result').html(data);
		$('#result dl.resultlist span.word').click(function(event){
			/* fill words in grid */
			var word = $(this).html();
			if ($(this).hasClass('horizontal')) {
				for (i=0; i<word.length; i++) {
					$('#char_'+y+'_'+(i+xstart+1)).val(word[i]);
				}
			} else if ($(this).hasClass('vertical')) {
				for (i=0; i<word.length; i++) {
					$('#char_'+(i+ystart+1)+'_'+x).val(word[i]);
				}
			} else {
				alert('Code error! Word is neither horizontal nor vertical!');
			}
			getWord(x,y,maxx,maxy);
			$('#char_'+y+'_'+x).focus();
		});
	}, 'html');
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

	/*
	 * Safari/Mac doesn't send keyPress for control keys (arrows, esc).
	 * Mozilla doesn't send an usable keyUp for visible chars (?, #)
	 */
	
	$('input.puzzlechar').keypress(function(event){
		//console.log('PR', event, 'key='+event.keyCode, 'char='+event.charCode, 'which='+event.which);
		if (event.metaKey || event.ctrlKey) return true;
		var idp = this.id.split('_'); // char,y,x
		var x = idp[2];
		var y = idp[1];
		/* handle character keys A-Z */
		event.preventDefault();
		if ((65 <= event.which && event.which <= 65 + 25) ||
		(97 <= event.which && event.which <= 97 + 25)) {
			var c = String.fromCharCode(event.which).toUpperCase();
			$(this).val(c);
		//console.log(event.keyCode, c);
		} else
		if (event.which==35)  renumberPuzzle(x,y,maxx,maxy,false);
		else
		if (event.which==63) getWord(x,y,maxx,maxy);
		return false;
	});
	
	$('input.puzzlechar').keyup(function(event){
		if (event.metaKey || event.ctrlKey) return true;
		/* handle any other keys */
		var idp = this.id.split('_'); // char,y,x
		var x = idp[2];
		var y = idp[1];
		//console.log('UP', event, 'key='+event.keyCode, 'char='+event.charCode, 'which='+event.which);
		switch (event.which) {
			case 8: // backspace
				$(this).val('');
				$(this).parent('td').removeClass('blocked');
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
				$(this).parent('td').removeClass('blocked');
				x++;
				break;
			default:
				$(this).parent('td').removeClass('blocked');
				if (event.shiftKey) {
					y++;
				}
				else {
					x++;
				}
		} // switch
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
		if (event.metaKey || event.ctrlKey) return true;
		/* handle numeric input fields */
		event.preventDefault();
		var num = Number(this.value);
		if (isNaN(num)) num=0;
		$(this).val(num);
	});
});

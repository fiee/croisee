var letters = 'ABCDEFGHIJKLMNOPQRTSUVWXYZ ';
var stop_char = '.';
var goodkeys = [9, 32, 37, 38, 39, 40, 46, 51, 191];
var modifiers = [16, 17, 18, 91];

function getWord(x, y, maxcol, maxrow){
    /*
     * lookup words that fit the letters at the crossing x, y
     * 
     * parameters:
     * x, y 			    = position of query in the grid, 0-based
     * maxcol, maxrow 		= size of the grid
     * 
     * internals:
     * xstart, ystart = start of the word, relative to the grid, 0-based
     * xpos, ypos 		= position of the query, relative to word, 0-based
     *
     */
    $('#result').html('');
    var horiz = '';
    var vert = '';
    var letter = '';
    var xpos = x;
    var ypos = y;
    var xstart = 0;
    var ystart = 0;
    /* collect word horizontally */
    for (i = 0; i <= maxcol; i++) {
        letter = $('#char_' + y + '_' + i).val()
        if (letter==''||letter==' ') { letter = '_'; }
        if (letter == stop_char) {
            if (i < x) {
                horiz = '';
                xpos = x - i;
                xstart = i+1;
            }
            else 
                if (i > x) {
                    break;
                }
        }
        else {
            horiz += letter;
        }
    }
    /* collect word vertically */
    for (i = 0; i <= maxrow; i++) {
        letter = $('#char_' + i + '_' + x).val();
        if (letter==''||letter==' ') { letter = '_'; }
        if (letter == stop_char) {
            if (i < y) {
                vert = '';
                ypos = y - i;
                ystart = i+1;
            }
            else 
                if (i > y) {
                    break;
                }
        }
        else {
            vert += letter;
        }
    }
    
    if (horiz.indexOf('_')==-1 && vert.indexOf('_')==-1) {
      console.log('No search necessary for', horiz, vert);
      return false;
    }
    
    /* send query */
    var query = '/ajax/' + horiz + ',' + xpos + '/' + vert + ',' + ypos + '/';
    //console.log(xstart, ystart, xpos, ypos, query);
    return $.post(query, check_dictionaries(), function(data){
        $('#result').html(data); // display results
        if ($('table.puzzle').length > 0) {
          activate_resultlist(x, y, maxcol, maxrow, xstart, ystart);
        } else {
          $('dl.resultlist .word').attr('title', '');
        }
    }, 'html');
}

function check_dictionaries(){
    var context = {};
    var dict_count = 0;
    /* check for selected dictionaries */
    $('input.dictionary-checkbox:checked').each(function(i){
        context[this.id] = true;
        dict_count++;
    });
    if (dict_count == 0) {
        $('#result').html('<p class="error">Please select at least one dictionary!</p>'); // TODO: i18n
    }
    return context;
}

function renumberPuzzle(x, y, maxcol, maxrow, reset){
    var id = '#num_' + y + '_' + x;
    if (reset || $(id).html()) {
        $(id).html('');
    }
    else {
        $(id).html('#');
    }
    var num = 1;
    for (cy = 0; cy <= maxrow; cy++) {
        for (cx = 0; cx <= maxcol; cx++) {
            var nf_id = '#num_' + cy + '_' + cx;
            var nf = $(nf_id);
            if (nf.html()) {
                nf.html(num);
                $('input'+nf_id).val(num);
                num++;
            }
        }
    }
    $('input#maxnum').val(num-1);
}

function activate_resultlist(x, y, maxcol, maxrow, xstart, ystart){
  /*
   * parameters:
   * x,y = cursor position
   */
  $('#result dl.resultlist span.word').click(function(event){
    /* on click fill word into grid */
    var word = $(this).html();
    if ($(this).hasClass('horizontal')) {
        for (i = 0; i < word.length; i++) {
            $('#char_' + y + '_' + (i + xstart)).val(word[i]);
        }
    }
    else if ($(this).hasClass('vertical')) {
        for (i = 0; i < word.length; i++) {
            $('#char_' + (i + ystart) + '_' + x).val(word[i]);
        }
    } else {
        alert('Code error! Word is neither horizontal nor vertical!');
    }
    getWord(x, y, maxcol, maxrow); // update result list
    $('#char_' + y + '_' + x).focus();
  });
  /* enable copy of searchterm to cloze search */
  $('span.searchterm').click(function(event){
    $('input#cloze_searchterm').val($(this).html());
  });
}

function search_handler(event){
  var word = $('input#cloze_searchterm').val();
  word = word.toUpperCase().replace(/[^A-Z\*_]/g, '');
  var query = '/ajax/' + word + '/';
  $('input#cloze_searchterm').val(word);
  if (!word) { return false; }
  $.post(query, check_dictionaries(), function(data){
      $('#result').html(data); // display results
      //activate_resultlist(focus_x, focus_y, maxcol, maxrow, 0,0);
      $('dl.resultlist .word').attr('title', '');
  }, 'html');
  return false; // don't propagate
}

$(function(){
    var maxcol = Number($('input#maxcol').val())-1;
    var maxrow = Number($('input#maxrow').val())-1;
    var focus_x = 0;
    var focus_y = 0;
    
    /* enable save puzzle button */
    $('input#save_puzzle').click(function(event){
      $('form#grid #dicts').append($('input.dictionary-checkbox'));
      document.forms['grid'].submit();
    });

    /* enable ajax processing of cloze search */
    $('input#cloze_search_submit').click(search_handler);
    /* disable submit on return key */
    $('form#cloze_search').submit(search_handler);
        
    /* restore blocked cells from saved grids */
    $('input.puzzlechar').each(function(index){
      if ($(this).val()==stop_char) {$(this).parent('td').addClass('blocked');}
    });
    
    /*
     * Safari/Mac doesn't send keyPress for control keys (arrows, esc).
     * Mozilla doesn't send an usable keyUp for visible chars (?, #)
     */
    $('input.puzzlechar').keypress(function(event){
        //console.log('PRESS', event, 'key='+event.keyCode, 'char='+event.charCode, 'which='+event.which);
        if (event.metaKey || event.ctrlKey) 
            return true;
        var idp = this.id.split('_'); // char,y,x
        var x = idp[2];
        var y = idp[1];
        focus_x = x;
        focus_y = y;
        /* handle character keys A-Z */
        event.preventDefault();
        if ((65 <= event.which && event.which <= 65 + 25) ||
        (97 <= event.which && event.which <= 97 + 25)) {
            var c = String.fromCharCode(event.which).toUpperCase();
            $(this).val(c);
            //console.log(event.keyCode, c);
        }
        else 
            if (event.which == 35) 
                renumberPuzzle(x, y, maxcol, maxrow, false);
            else 
                if (event.which == 63) {
                    getWord(x, y, maxcol, maxrow);
                }
        return false;
    });
    
    $('input.puzzlechar').keyup(function(event){
        if (event.metaKey || event.ctrlKey) 
            return true;
        /* handle any other keys */
        var idp = this.id.split('_'); // char,y,x
        var x = idp[2];
        var y = idp[1];
        focus_x = x;
        focus_y = y;
        //console.log('UP', event, 'key='+event.keyCode, 'char='+event.charCode, 'which='+event.which);
        switch (event.which) {
            case 0: break; // e.g. question mark on Mozilla
            case 8: // backspace
                $(this).val('');
                $(this).parent('td').removeClass('blocked');
                x--;
                break;
            case 9: // tab
                //if (event.shiftKey) { x--; } else { x++; }
                break;
            case 32: // space
                $(this).val(stop_char).parent('td').toggleClass('blocked');
                renumberPuzzle(x, y, maxcol, maxrow, true);
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
            case 191: // question mark
                // don't move
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
        if (x > maxcol) {
            x = 0;
        }
        else 
            if (x < 0) {
                x = maxcol;
            }
        if (y > maxrow) {
            y = 0;
        }
        else 
            if (y < 0) {
                y = maxrow;
            }
        event.preventDefault();
        if (modifiers.indexOf(event.keyCode) == -1) {
            $('#char_' + y + '_' + x).focus().select();
        }
        return true;
    });
	
    $('input.numeric').keyup(function(event){
        if (event.metaKey || event.ctrlKey) 
            return true;
        /* handle numeric input fields */
        event.preventDefault();
        var num = Number(this.value);
        if (isNaN(num)) 
            num = 0;
        $(this).val(num);
    });
});

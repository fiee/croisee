//var letters = 'ABCDEFGHIJKLMNOPQRTSUVWXYZ ';
//var goodkeys = [9, 32, 37, 38, 39, 40, 46, 51, 191];
var modifiers = [16, 17, 18, 91];
var stop_char = '.';
var line_sep = '\n';
var focus_x = 0;
var focus_y = 0;
var DEBUG = false;

function chars2text(maxcol, maxrow) {
  /*
   * collect single chars from puzzle grid into one text string
   */
  var text = '';
  for (var y=0; y <= maxrow; y++) {
    for (var x=0; x <= maxcol; x++) {
      text += $('#char_'+y+'_'+x).val() || '_';
    }
    text += line_sep;
  }
  $('input#text_id').val(text);
  return text;
}

function text2chars() {
  /*
   * spread single chars from puzzle text into character cells
   */
  var lines = $('input#text_id').val();
  if (!lines) { return false; }
  lines = lines.replace(/_/g, ' ').split(line_sep);
  for (var y=0; y <= lines.length; y++) {
    if (!lines[y]) return false;
    var line = lines[y].split('');
    for (var x=0; x <= line.length; x++) {
      $('#char_'+y+'_'+x).val(line[x]);
    }
  }
  return true;
}

function spread_nums() {
  /*
   * spread word start numbers from hidden input into grid
   * return object { num : [y,x,num] }
   */
  var nums = $('input#numbers_id').val();
  var dict = {};
  if (!nums) { return dict; }
  nums = nums.split(',');
  for (var n=0; n < nums.length; n++) {
    var np = nums[n].split('.');
    if (np.length != 3) { return false; }
    np[0] = Number(np[0]);
    np[1] = Number(np[1]);
    np[2] = Number(np[2])-1;
    $('#num_'+np[0]+'_'+np[1]).html(np[2]+1);
    dict[np[2]] = np;
  }
  return dict;
}

function fill_questions(maxcol, maxrow, dict) {
  /*
   * fill question fields from saved data (hidden field) and solution words
   * 
   * dict from spread_nums
   */
  var quests = $('input#questions_id').val() || ''; 
  quests = quests.split('\n');
  if (DEBUG) {
    console.log('fill_questions H, V, dict', quests, dict);
  }
  var ok = [];
  for (var i=0; i < quests.length; i++) {
    if (quests[i]>'') {
      var qst = quests[i].split('::'); // num::dir::word
      if (DEBUG) {
        console.log('fill questions:', i, qst);
      }
      qst[0] = Number(qst[0]);
      var coords = dict[qst[0]]
      if (qst[2]) { //} && coords) {
        add_question(coords[1], coords[0], maxcol, maxrow, qst[1], qst[0], qst[2]);
        ok.push(qst[1]+'_'+qst[0]);
      }
    }
  }
  ok.sort();
  if (DEBUG) {
    console.log('fill_questions ok:', ok);
  }
  /* fill missing questions with solution word */
  for (num in dict) {
    var t = dict[num];
    if (DEBUG) console.log('fill_questions', num, t);
    if ($.inArray('h_'+num, ok)==-1) add_question(t[1], t[0], maxcol, maxrow, 'h', num);
    if ($.inArray('v_'+num, ok)==-1) add_question(t[1], t[0], maxcol, maxrow, 'v', num);
  }
}

function find_words(x, y, maxcol, maxrow, direction) {
    /*
     * find words _starting_ at x, y (e.g. from number position)
     * return [horizontal,vertical]
     * 
     * parameters:
     * x, y           = position of query in the grid, 0-based
     * maxcol, maxrow = size of the grid
     * direction      = if set to 'h' or 'v', get and return only one word ('b' or empty for both)
     */
    direction = direction[0].toLowerCase() || 'b';
    var horiz = '';
    var vert = '';
    var i = 0;
    var letter = '';
    
    if (direction != 'v') {
      /* collect word horizontally */
      for (i = x; i <= maxcol; i++) {
          letter = $('#char_' + y + '_' + i).val() || '_';
          if (letter == stop_char) { break; }
          horiz += letter;
      }
      horiz = horiz.replace(/\s/g, '_');
    }
    
    if (direction != 'h') {
      /* collect word vertically */
      for (i = y; i <= maxrow; i++) {
          letter = $('#char_' + i + '_' + x).val() || '_';
          if (letter == stop_char) { break; }
          vert += letter;
      }
      vert = vert.replace(/\s/g, '_');
    }
    
    switch (direction) {
      case 'b': return [horiz,vert];
      case 'h': return horiz;
      case 'v': return vert;
      default:  return null;
    } 
}

function lookup_word(x, y, maxcol, maxrow){
    /*
     * lookup words that fit the letters at the crossing x, y
     * 
     * parameters:
     * x, y 			    = position of query in the grid, 0-based
     * maxcol, maxrow = size of the grid
     * 
     * internals:
     * xstart, ystart = start of the word, relative to the grid, 0-based
     * xpos, ypos     = position of the query, relative to word, 0-based (crossing)
     * 
     * the code is mostly a duplication of find_words, but we need to collect more data than there
     */
    $('#result').html('');

    var horiz = '';
    var vert = '';
    var xpos = x;
    var ypos = y;
    var xstart = 0;
    var ystart = 0;
    var i = 0;
    var letter = '';
     
    /* collect word horizontally */
    for (i = 0; i <= maxcol; i++) {
      letter = $('#char_' + y + '_' + i).val() || '_';
      if (letter == stop_char) {
        /* now there's the stop char at i,y */
        if (i < x) {
            horiz = '';
            xpos = x - i - 1;
            xstart = i+1;
        } else if (i > x) {
            break;
        }
      } else {
        horiz += letter;
      }
    }
    horiz = horiz.replace(/\s/g, '_');
    
    /* collect word vertically */
    for (i = 0; i <= maxrow; i++) {
      letter = $('#char_' + i + '_' + x).val() || '_';
      if (letter == stop_char) {
        /* now there's the stop char at x,i */
        if (i < y) {
            vert = '';
            ypos = y - i - 1;
            ystart = i+1;
        } else if (i > y) {
            break;
        }
      } else {
        vert += letter;
      }
    }
    vert = vert.replace(/\s/g, '_');
    
    if (horiz.indexOf('_') == -1 && vert.indexOf('_') == -1) {
      console.log(interpolate(gettext('No search necessary for %s/%s'), [horiz, vert]));
      return false;
    }
    
    /* send query */
    var query = '/ajax/' + horiz + ',' + xpos + '/' + vert + ',' + ypos + '/';
    //if (DEBUG) console.log(x, y, maxcol, maxrow, xstart, ystart, xpos, ypos, query);
    var dicts = check_dictionaries();
    if (!dicts) return false;
    return $.post(query, dicts, function(data){
        $('#result').html(data); // display results
        if ($('table.puzzle').length > 0) {
          activate_resultlist(x, y, maxcol, maxrow, xstart, ystart);
        } else {
          $('dl.resultlist .word').attr('title', '');
        }
    }, 'html');
}

function check_dictionaries(){
  /*
   * check if there are any dictionaries selected and return {dict_id:true}
   */
    var context = {};
    var dict_count = 0;
    $('input.dictionary-checkbox:checked').each(function(i){
        context[this.id] = true;
        dict_count++;
    });
    if (dict_count === 0) {
        // TODO: gettext()
        $('#dict_error').removeClass('hidden').show(500).delay(7000).hide(500);
    }
    return context;
}

function renumber_puzzle(x, y, maxcol, maxrow, reset){
    /*
     * set a new number at x, y and renew all word start numbers
     * fill hidden numbers form fields
     * 
     * params:
     * x, y: coordinates of grid field, 0-based
     * maxcol, maxrow: size of grid
     * reset (boolean): if true, unset the number // TODO: obsolete, just check content?
     * 
     */
    var oldnums = $('input#numbers_id').val();
    var insertpos = 0; // list position of inserted number
    var id = '#num_' + y + '_' + x; // id of new numbered field (i.e. of number div)
    if (reset || $(id).html()) {
        // we're removing a number
        insertpos = Number($(id).html());
        $(id).html('');
        reset = true;
    }
    else {
        $(id).html('#'); // gets replaced by number later
        reset = false;
    }
    var nums = []; // list of coordinates with numbers
    var num = 1; // start number
    for (var cy = 0; cy <= maxrow; cy++) {
        for (var cx = 0; cx <= maxcol; cx++) {
            var nf_id = '#num_' + cy + '_' + cx;
            var nf = $(nf_id);
            var content = nf.html();
            if (content) { // if number field contains anything, nf.html() doesn’t work here, if it’s '#'!
                nf.html(num);
                nums.push(cy + '.' + cx + '.' + num);
                if ((content=='#')||(oldnums.indexOf(cy + '.' + cx + '.') == -1)) {
                  insertpos = num;
                }
                num++;
            }
        }
    }
    num--;
    insertpos--;
    if (DEBUG) {
      console.log('renumber_puzzle | x=',x,'y=',y,'num=',num,'insertpos=',insertpos,'nums=',nums);
    }
    if (insertpos < 0) insertpos = 0;
    if (num<0) {
      console.log('ERROR in renumber_puzzle:',insertpos,'/',num);
      return false;
    }
    $('input#maxnum_id').val(num);
    $('input#numbers_id').val(nums.join(','));

    /* question fields */
    if (reset) { // remove question
      if (DEBUG) {
        console.log('renumber, removing question at',insertpos,'/',num);
      }
      $('#question_h_'+insertpos).remove();
      $('#question_v_'+insertpos).remove();
      // decrease following numbers
      $.each(['h','v'], function(index,dir) {
        for (var i=insertpos; i<=num; i++){
          var nnr = i-1;
          var oid = '_'+dir+'_'+i;
          var nid = '_'+dir+'_'+nnr;
          var div = $('#question'+oid);
          if (div.length==1) {
            if (DEBUG) {
              console.log('renumber', div.attr('id'), 'as', nid);
            }
            div.attr('id','question'+nid);
            nid = 'qst'+nid; 
            div.children('#qst'+oid).attr({'id':nid, 'name':nid});
            div.find('label').attr('for', nid).html(i);
          }
        }
      });
    } else { // add question
      if (DEBUG) {
        console.log('renumber, adding question at',insertpos,'/',num);
      }
      // increase following numbers
      $.each(['h','v'], function(index,dir) {
        for (var i=num; i>=insertpos; i--){
          var nnr = i+1;
          var oid = '_'+dir+'_'+i;
          var nid = '_'+dir+'_'+nnr;
          var div = $('#question'+oid);
          if (div.length==1) {
            if (DEBUG) {
              console.log('renumber', div.attr('id'), 'as', nid);
            }
            div.attr('id','question'+nid);
            nid = 'qst'+nid; 
            div.children('#qst'+oid).attr({'id':nid, 'name':nid});
            div.find('label').attr('for', nid).html(nnr+1);
          }
        }
      });
      add_question(x, y, maxcol, maxrow, 'h', insertpos, '', true);
      add_question(x, y, maxcol, maxrow, 'v', insertpos, '', true);
    }
}

function add_question(x, y, maxcol, maxrow, direction, num, word, lookup) {
  /*
   * clone question field template
   * 
   * parameters:
   * x,y:       position of word start in grid (0-based)
   * direction: h or v (horizontal or vertical)
   * num:       number of question (0-based)
   * word:      question value, defaults to word in grid (expensive!)
   * lookup:    fill solution from dictionary? default=false (expensive!)
   */
  direction = direction[0].toLowerCase() || 'h';
  if (direction=='h') {
    if ((x > 0) && ($('input#char_'+y+'_'+(x-1)).val() != stop_char)) return false;
  } else {
    if ((y > 0) && ($('input#char_'+(y-1)+'_'+x).val() != stop_char)) return false;
  }
  num = Number( num );
  word = word || find_words(x, y, maxcol, maxrow, direction);
  lookup = lookup || false;
  var clone = $('div#question_template').clone();
  var id = 'qst_'+direction+'_'+num;
  clone.attr('id','question_'+direction+'_'+num).find('label').attr('for', id).html(num+1);
  clone.children('input').attr({'name':id, 'id':id}).val(word);

  if ($('div#questions_list_'+direction+' div.question').length === 0) {
    clone.appendTo($('div#questions_list_'+direction));
  } else {
    // find previous element
    var found = -1;
    for (var i=0; i<num; i++) {
      if ($('#question_'+direction+'_'+i).length==1) { found=i; }
    }
    if (found >= 0) {
      $('#question_'+direction+'_'+found).after(clone);
    } else {
      $('div#questions_list_'+direction+' h3').after(clone);
    }
  }
  clone.removeClass('hidden');
  if (lookup===true) {
    // get solution from dictionary
    var query = '/ajax/' + word + '/';
    $('input#cloze_searchterm').val(word);
    $.post(query, check_dictionaries(), function(data){
        $('#result').html(data); // display results
        $('dl.resultlist .word').attr('title', '');
        var solution = $('dl.resultlist span.word:contains("'+word+'")').parent('dt').next('dd').html();
        if (solution) { $('input#'+id).val(solution); }
    }, 'html');
  }

  if (num > Number($('input#maxnum_id').val())) $('input#maxnum_id').val(num);
  if (DEBUG) {
    console.log('add_question',x,y,direction,num,word);
  }
  return clone;
}

function copy_questions_to_save() {
  /*
   * collect questions fields and add them to the submission
   */
    var maxnum = $('input#maxnum_id').val() || 0;
    var sols_v = [];
    var quests = [];
    $('#questions_form input.question').each(function(index){
      if ($(this).val()) {
        var idp = $(this).attr('id').split('_'); // #qst_h_0
        var val = idp[2]+'::'+idp[1]+'::'+$(this).val();
        quests.push(val);
      }
    });
    $('input#questions_id').val(quests.join('\n'));
    if (DEBUG) {
      console.log('copy questions:', $('input#questions_id').val());
    }
    return maxnum;
}

function activate_resultlist(x, y, maxcol, maxrow, xstart, ystart){
  /*
   * make words in search result clickable to insert them into the grid
   * 
   * parameters:
   * x,y = cursor position
   */
  $('#result dl.resultlist span.word').click(function(event){
    /* on click fill word into grid */
    var word = $(this).html();
    var i = 0;
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
        alert(gettext('Code error! Word is neither horizontal nor vertical!'));
    }
    lookup_word(x, y, maxcol, maxrow); // update result list
    $('#char_' + y + '_' + x).focus();
    chars2text(maxcol, maxrow);
  });
  /* enable copy of searchterm to cloze search */
  $('span.searchterm').click(function(event){
    $('input#cloze_searchterm_id').val($(this).html());
  });
}

function searchhandler(event){
  /*
   * handler for search field
   */
  var word = $('input#cloze_searchterm_id').val();
  word = word.toUpperCase().replace(/[^A-Z\*_]/g, '');
  var query = '/ajax/' + word + '/';
  $('input#cloze_searchterm_id').val(word);
  if (!word) { return false; }
  $.post(query, check_dictionaries(), function(data){
      $('#result').html(data); // display results
      $('dl.resultlist .word').attr('title', '');
  }, 'html');
  return false; // don't propagate
}

function clear_grid(){
  /* delete all grid contents */
  $('input.puzzlechar').val('');
  $('div.puzzlenum').html('');
  $('td.puzzlecell').removeClass('blocked focus');
  $('input#text_id').val('');
  $('input#maxnum_id').val(0);
}

function set_focus(x, y){
  /* set focus on puzzle cell */
  focus_x = x;
  focus_y = y;
  $('td.puzzlecell').removeClass('focus');
  $('td.puzzlecell#cell_'+y+'_'+x).addClass('focus');
  $('#char_'+y+'_'+x).focus().select();
}

function init_puzzle(maxcol, maxrow) {
  /* initialize puzzle grid and questions at page load */
  text2chars();
  fill_questions(maxcol, maxrow, spread_nums());
}

function ___INIT___(){} // bookmark for jQuery’s anonymous init function

$(function(){
    var maxcol = Number($('form#puzzle_form input#width_id').val())-1;
    var maxrow = Number($('form#puzzle_form input#height_id').val())-1;
    
    init_puzzle(maxcol, maxrow);
    
    /* toolbar init: disable normal link behaviour */
    $('.toolbar a').click(function(event){
      event.preventDefault();
      //if (DEBUG) console.log($(this).attr('href'));
      return false;      
    });
    /* enable new puzzle button */
    $('#tb_new_puzzle').click(function(event){
      $('#dialog_new_puzzle').dialog();
    });
    /* enable save puzzle button/menu */
    $('#tb_save_puzzle').click(function(event){
      /* append dictionary settings from other form */
      $('form#puzzle_form #dicts').append($('input.dictionary-checkbox'));
      copy_questions_to_save();
      chars2text(maxcol, maxrow);
      document.forms.puzzle.submit();
    });
    /* enable load button */
    $('#tb_load_puzzle').click(function(event){
      // TODO: dialog
      window.location.href='/puzzle/list';
      return true;
    });
    /* enable clear button */
    $('#tb_clear_puzzle').click(function(event){
      $('#dialog_clear_confirm').dialog({
        modal:true,
        resizable:false,
        buttons:{
          'Clear': function(){
            clear_grid();
            $(this).dialog('close');            
          },
          'Cancel': function(){
            $(this).dialog('close');
          },
        },
      });
    });
    /* enable help button */
    $('#tb_help, #menu_help').click(function(event){
      $('#dialog_keys_help').dialog();
    });

    /* enable ajax processing of cloze search */
    $('#cloze_search_submit').click(searchhandler);
    /* disable submit on return key */
    $('form#cloze_search_form').submit(searchhandler);

    /* enable dictionary button */
    $('#tb_dicts').click(function(event){
      $('#dialog_dicts').dialog({
        resizable: false,
        modal: true,
        buttons:{
          'Ok': function(){ $(this).dialog('close'); },
        }
      });
    });
    /* enable check/uncheck all dictionaries */
    $('#dic_all').toggle(
      function(){
        $('#dialog_dicts input.dictionary-checkbox').prop('checked', true);
      },
      function(){
        $('#dialog_dicts input.dictionary-checkbox').prop('checked', false);
      }
    );
        
    /* restore blocked cells from saved grids */
    $('input.puzzlechar').each(function(index){
      if ($(this).val()==stop_char) {$(this).parent('td').addClass('blocked');}
    });
    
    /*
     * Safari/Mac doesn't send keyPress for control keys (arrows, esc).
     * Mozilla doesn't send an usable keyUp for visible chars (?, #)
     */
    $('input.puzzlechar').keypress(function(event){
        //if (DEBUG) console.log('PRESS', event, 'key='+event.keyCode, 'char='+event.charCode, 'which='+event.which);
        if (event.metaKey || event.ctrlKey) 
            return true;
        var idp = this.id.split('_'); // char,y,x
        var x = idp[2];
        var y = idp[1];
        set_focus(x, y);
        /* handle character keys A-Z */
        event.preventDefault();
        if ((65 <= event.which && event.which <= 65 + 25) ||
        (97 <= event.which && event.which <= 97 + 25)) {
            var c = String.fromCharCode(event.which).toUpperCase();
            $(this).val(c);
            //if (DEBUG) console.log(event.keyCode, c);
        }
        else 
            if (event.which == 35) // # number sign
                renumber_puzzle(x, y, maxcol, maxrow, false);
            else 
                if (event.which == 63) { // question mark
                    lookup_word(x, y, maxcol, maxrow);
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
        //if (DEBUG) console.log('UP', event, 'key='+event.keyCode, 'char='+event.charCode, 'which='+event.which);
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
            case 16: // shift
                break;
            case 32: // space
                if ($(this).val()==stop_char) {
                    $(this).val('').parent('td').removeClass('blocked');
                } else {
                    $(this).val(stop_char).parent('td').addClass('blocked');
                }
                //renumber_puzzle(x, y, maxcol, maxrow, true);
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
        /* check coordinates to stay within grid */
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
          set_focus(x, y);
        }
        return true;
    });
	  
	  /* only allow numbers in numeric input fields, e.g. "new puzzle" form */
    $('input.numeric').keyup(function(event){
        if (event.metaKey || event.ctrlKey || event.which==9) 
            return true;
        /* handle numeric input fields */
        event.preventDefault();
        var num = Number(this.value);
        if (isNaN(num)) 
            num = 0;
        $(this).val(num);
    });
});

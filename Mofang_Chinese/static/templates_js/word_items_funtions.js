function searchArrayFilter(item_list){
    translation_search_field = document.getElementById("translation search field");
    hieroglyph_search_field = document.getElementById("hieroglyph search field");
    val1 = translation_search_field.value;
    val2 = hieroglyph_search_field.value;
    name_vals = ["translation", "hieroglyph"];
    ret_array = [];
    if (val1 != "" || val2 != ""){
        for (var i = 0; i < item_list.length; i++) {
            if ( (val1 == "" || item_list[i].translation.includes(val1) ) &&
                (val2 == "" || item_list[i].hieroglyph.includes(val2)) ){
                ret_array.push(item_list[i]);
            }
        }
    } else {
        ret_array = item_list;
    }
    return ret_array;
}

function sortButtonClick(event){
    button_type = event.target.id;
    current_item_list = searchArrayFilter(items_lists[filter_button_state]);
    if (button_type == "alphabet_translation-sort-button"){
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = firstItem.translation.toUpperCase();
              const string2 = secondItem.translation.toUpperCase();
              if (string1 < string2) {return -1;}
              if (string1 > string2) {return 1;}
              return 0;
        });
    } else if (button_type == "rev_alphabet_translation-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = firstItem.translation.toUpperCase();
              const string2 = secondItem.translation.toUpperCase();
              if (string1 < string2) {return 1;}
              if (string1 > string2) {return -1;}
              return 0;
        });
    } else if (button_type == "alphabet_hieroglyph-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = firstItem.hieroglyph.toUpperCase();
              const string2 = secondItem.hieroglyph.toUpperCase();
              if (string1 < string2) {return -1;}
              if (string1 > string2) {return 1;}
              return 0;
        });
    } else if (button_type == "rev_alphabet_hieroglyph-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = firstItem.hieroglyph.toUpperCase();
              const string2 = secondItem.hieroglyph.toUpperCase();
              if (string1 < string2) {return 1;}
              if (string1 > string2) {return -1;}
              return 0;
        });
    } else if (button_type == "time-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = parseInt(firstItem.id);
              const string2 = parseInt(secondItem.id);
              if (string1 < string2) {return -1;}
              if (string1 > string2) {return 1;}
              return 0;
        });
    } else if (button_type == "rev_time-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = parseInt(firstItem.id);
              const string2 = parseInt(secondItem.id);
              if (string1 < string2) {return 1;}
              if (string1 > string2) {return -1;}
              return 0;
        });
    }
    pagerUpdate();
}

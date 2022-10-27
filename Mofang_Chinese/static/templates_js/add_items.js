function searchArrayFilter(item_list){
    search_field = document.getElementById("search field");
    if (search_field){
        val1 = search_field.value;
    } else {
        val1 = "";
    }
    ret_array = [];
    if (val1 != ""){
        for (var i = 0; i < item_list.length; i++) {
            if (item_list[i][button_texts[text_button_state]].includes(val1)){
                ret_array.push(item_list[i]);
            }
        }
    } else {
        ret_array = item_list;
    }
    return ret_array;
}

function showButtons(){
    current_item_list = searchArrayFilter(items_lists[filter_button_state]);
    current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1),
        max_items_number_on_one_page * current_page);
    current_page_max_number = page_numbers[filter_button_state];

    if ((current_page_item_list[0] == "")){
        current_page_item_list = [];
    }
    if (current_page_item_list.length == 0 && current_page > current_page_max_number) {
        current_page = current_page_max_number;
        current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1),
            max_items_number_on_one_page * current_page);
    }
    createItemButtons(current_page_item_list);
    if (current_page_max_number > 1){  // f
        createPageButtons();
    }
}

//function sortButtonClick(event){
//    button_type = event.target.id;
//    current_item_list = searchArrayFilter(items_lists[filter_button_state]);
//    if (button_type == "alphabet_translation-sort-button"){
//        current_item_list.sort((firstItem, secondItem) => {
//              const translation1 = firstItem[button_texts[text_button_state]].toUpperCase(); // ignore upper and lowercase
//              const translation2 = secondItem[button_texts[text_button_state]].toUpperCase(); // ignore upper and lowercase
//              if (translation1 < translation2) {return -1;}
//              if (translation1 > translation2) {return 1;}
//              return 0;
//        });
//    } else if (button_type == "rev_alphabet_translation-sort-button") {
//        current_item_list.sort((firstItem, secondItem) => {
//              const translation1 = firstItem[button_texts[text_button_state]].toUpperCase(); // ignore upper and lowercase
//              const translation2 = secondItem[button_texts[text_button_state]].toUpperCase(); // ignore upper and lowercase
//              if (translation1 < translation2) {return 1;}
//              if (translation1 > translation2) {return -1;}
//              return 0;
//        });
//    } else if (button_type == "time-sort-button") {
//        current_item_list.sort((firstItem, secondItem) => {
//              const translation1 = parseInt(firstItem["id"]); // ignore upper and lowercase
//              const translation2 = parseInt(secondItem["id"]); // ignore upper and lowercase
//              if (translation1 < translation2) {return -1;}
//              if (translation1 > translation2) {return 1;}
//              return 0;
//        });
//    } else if (button_type == "rev_time-sort-button") {
//        current_item_list.sort((firstItem, secondItem) => {
//              const translation1 = parseInt(firstItem["id"]); // ignore upper and lowercase
//              const translation2 = parseInt(secondItem["id"]); // ignore upper and lowercase
//              if (translation1 < translation2) {return 1;}
//              if (translation1 > translation2) {return -1;}
//              return 0;
//        });
//    }
//    current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1),
//        max_items_number_on_one_page * current_page);
//    current_page_max_number = page_numbers[filter_button_state];
//
//    if ((current_page_item_list[0] == "")){
//        current_page_item_list = [];
//    }
//    if (current_page_item_list.length == 0 && current_page > current_page_max_number) {
//        current_page = current_page_max_number;
//        current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
//    }
//    createItemButtons(current_page_item_list);
//    if (current_page_max_number > 1){  // f
//        createPageButtons();
//    }
//}

function filterButtonClick(event){
    filter_button_state = (filter_button_state + 1) % items_lists.length;
    filter_button.innerText = filter_button_innerTexts[filter_button_state];
    showButtons();
}

//function javascriptList(list){
//    if (!list) {return [];}
//    list = list.split(";;;");
//    for (let i = 0; i < list.length; i += 1){
//        list_word = list[i].split(";");
//        list[i] = { "id": list_word[0],
//                    "name": list_word[1],
//                    "email": list_word[2],
//                    "creator": list_word[3],
//                  };
//    }
//    return list;
//}

function itemButtonClick(event){
    prev_name = event.target.name
    if (prev_name == "added_item") {
        // alert(event.target.style.cssText);
        event.target.name = "not_added_item";
        event.target.classList.remove("added-item");
        event.target.classList.add("not-added-item");
        // event.target.style = event.target.style.cssText + "background-color: var(--red)";
        bool_added_items[parseInt(event.target.value, 10)] = 0;
    } else {
        event.target.name = "added_item";
        event.target.classList.remove("not-added-item");
        // event.target.style = event.target.style.cssText + "background-color: var(--green)";
        event.target.classList.add("added-item");
        bool_added_items[parseInt(event.target.value, 10)] = 1;
    }
}

function createItemButtons(item_list){
    for (let i = 0; i < max_items_number_on_one_page; i += 1) {
        prev_but = document.getElementById("item_button " + i.toString())
        if (prev_but != null){prev_but.remove();}
    }
    if (item_list.length == 0){
        document.getElementById("items-not-found-heading").hidden = false;
        return;
    } else {
        document.getElementById("items-not-found-heading").hidden = true;
    }
    for (let i = 0; i < item_list.length; i += 1) {
        column = document.getElementById("column " + (i % column_number).toString());
        column.style = "flex: " + (100 / column_number).toString() + "%";
        item_button = document.createElement("button");
        item_button.id = "item_button " + i.toString();
        item_button.type = "button";
        item_button.addEventListener("click", itemButtonClick, false);
        item_button.classList.add("btn");
        item_button.classList.add("btn-primary");
        button_id = item_list[i]["id"];
        item_button.value = button_id;
        if (bool_added_items[button_id] == 1){
            // item_button.style = "min-width: 250px; background-color: green";
            item_button.classList.add("added-item")
            bool_added_items[button_id] = 1;
            item_button.name = "added_item";
        } else {
            // item_button.style = "min-width: 250px; background-color: #007bff";
            item_button.classList.add("not-added-item")
            bool_added_items[button_id] = 0;
            item_button.name = "not_added_item";
        }
        item_button.classList.add("user-word-button");
        item_button.innerText = item_list[i][button_texts[text_button_state]];
        column.appendChild(item_button);
    }
}

function createOnePageButton(row, text, onClickFunction){
    page_button = document.createElement("button");
    page_button.onclick = onClickFunction;
    page_button.id = "page_button " + text;
    page_button.classList.add("btn");
    page_button.classList.add("btn-primary");
    if (text == current_page){
        page_button.classList.add("current_page_button")
    } else {
        page_button.classList.add("page_button");
    }
    page_button.innerText = text;
    row.appendChild(page_button);
}

function deletePageButtons(){
    prev_but = document.getElementById("page_button <<");
    if (prev_but != null){prev_but.remove();}
    prev_but = document.getElementById("page_button <");
    if (prev_but != null){prev_but.remove();}

    for (let i = 1; i < page_numbers[0] + 1; i++){
        prev_but = document.getElementById("page_button " + i.toString());
        if (prev_but != null){prev_but.remove();}
    }

    prev_but = document.getElementById("page_button >>");
    if (prev_but != null){prev_but.remove();}
    prev_but = document.getElementById("page_button >");
    if (prev_but != null){prev_but.remove();}
}

function pageButtonNumberFunction(event){
    current_page = parseInt(event.target.innerText, 10);
    current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
    createItemButtons(current_page_item_list);
    if (current_page_max_number > 1){
        createPageButtons();
    }
}

function pageButtonFunctions(button_text){
    if (button_text == "<<"){
        return function(event){
            current_page = 1;
            current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
            createItemButtons(current_page_item_list);
            if (current_page_max_number > 1){
                createPageButtons();
            }
        };
    } else if (button_text == "<"){
        return function(event){
            if (current_page != 1) {
                current_page -= 1;
                current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
                createItemButtons(current_page_item_list);
                if (current_page_max_number > 1){createPageButtons();}
            }
        };
    } else if (button_text == ">"){
        return function(event) {
            if (current_page != current_page_max_number) {
                current_page += 1;
                current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
                createItemButtons(current_page_item_list);
                if (current_page_max_number > 1){  // f
                    // alert("creating page buttons");
                    createPageButtons();
                }
            }
        }
    } else if (button_text == ">>"){
        return function(event){
            current_page = current_page_max_number;
            current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
            createItemButtons(current_page_item_list);
            if (current_page_max_number > 1){  // f
                // alert("creating page buttons");
                createPageButtons();
            }
        };
    }
}

function createPageButtons(){
    deletePageButtons();
    if (current_page_max_number > 1){
        pages_row = document.getElementById("pages-row");
        createOnePageButton(pages_row, "<<", pageButtonFunctions("<<"));
        createOnePageButton(pages_row, "<", pageButtonFunctions("<"));

        if ((current_page_max_number - current_page) <= 6 && (current_page_max_number - current_page) >= 0) {
            if (current_page_max_number >= 9){
                for (let i = (current_page_max_number - 9); i < current_page_max_number; i++){
                    createOnePageButton(pages_row, i + 1, pageButtonNumberFunction);
                }
            } else {
                for (let i = 0; i < current_page_max_number; i++){
                    createOnePageButton(pages_row, i + 1, pageButtonNumberFunction);
                }
            }
        } else {
            if (current_page == 1) {
                if (current_page_max_number < 9){
                    for (let i = 0; i < current_page_max_number; i ++){
                        createOnePageButton(pages_row, i + 1, pageButtonNumberFunction);
                    }
                } else {
                    for (let i = 0; i < 9; i ++){
                        createOnePageButton(pages_row, i + 1, pageButtonNumberFunction);
                    }
                }
            } else {
                for (let i = (current_page - 2); i < (current_page + 7); i++) {
                    createOnePageButton(pages_row, i + 1, pageButtonNumberFunction);
                }
            }
        }
        createOnePageButton(pages_row, ">", pageButtonFunctions(">"));
        createOnePageButton(pages_row, ">>", pageButtonFunctions(">>"));
    }
}

function onSubmitButtonClick(event){
    form_res = document.getElementById("form-res");
    for (let i = 0; i < bool_added_items.length; i++){
        if (bool_added_items[i] != 0 && bool_added_items[i] != 1) {
            bool_added_items[i] = 0;
        }
    }
    form_res.value = bool_added_items;
}

function onSearchChange(event){
        if (event.key != "Control"){
            current_item_list = searchArrayFilter(items_lists[filter_button_state]);
            showButtons();
        }
    }

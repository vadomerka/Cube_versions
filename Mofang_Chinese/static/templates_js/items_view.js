function pageNumberCount(item_array) {  // функция высчитывает количество страниц для данного списка объектов
    page_num = Math.floor(item_array.length / max_items_number_on_one_page) + 1;
    if (item_array.length > 0 && item_array.length % max_items_number_on_one_page == 0) {
        page_num = Math.floor(item_array.length / max_items_number_on_one_page);
    }
    return page_num;
}

function pagerUpdate() {  // функция высчитывает список предметов на странице и сколько всего страниц с этим списком
    current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1),
        max_items_number_on_one_page * current_page);
    current_page_max_number = pageNumberCount(current_item_list);
    if ((current_page_item_list[0] == "")) {
        current_page_item_list = [];
    }
    if (current_page_item_list.length == 0 && current_page > current_page_max_number) {
        current_page = current_page_max_number;
        current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1),
            max_items_number_on_one_page * current_page);
    }
    deletePageButtons();
    createItemButtons(current_page_item_list);
    if (current_page_max_number > 1) {
        createPageButtons();
    }
}

function showButtons() {  // функция обновляет текущий список объектов
    current_item_list = searchArrayFilter(items_lists[filter_button_state]);
    pagerUpdate();
}

function filterButtonClick(event) {  // функция меняет состояние переменной фильтра, а затем обновляет список
    filter_button_state = (filter_button_state + 1) % items_lists.length;
    filter_button.innerText = filter_button_innerTexts[filter_button_state];
    showButtons();
}

function createOnePageButton(row, text, onClickFunction) {  // функция создает одну кнопку для пейджинга
    page_button = document.createElement("button");
    page_button.onclick = onClickFunction;
    page_button.id = "page_button " + text;
    page_button.classList.add("btn-primary");
    if (text == current_page){
        page_button.classList.add("current-page-button")
    } else {
        page_button.classList.add("page-button");
    }
    page_button.innerText = text;
    row.appendChild(page_button);
}

function deletePageButtons() {  // функция удаляет все предыдущие кнопки пейджера, если они есть
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

function pageButtonNumberFunction(event) {  // функция меняет текущую страницу на ту, что была записана на кнопке пейджера
    current_page = parseInt(event.target.innerText, 10);
    showButtons();
}

function pageButtonFunctions(button_text) {  // функция возвращает функции для специальных кнопок пейджера
    if (button_text == "<<"){
        return function(event){
            current_page = 1;
            current_page_item_list = current_item_list.slice(max_items_number_on_one_page * (current_page - 1), max_items_number_on_one_page * current_page);
            createItemButtons(current_page_item_list);
            if (current_page_max_number > 1){
                createPageButtons();
            }
        };
    } else if (button_text == "<") {
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
                if (current_page_max_number > 1) {
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
                createPageButtons();
            }
        };
    }
}

function createPageButtons() {  // функция создает кнопки пейджера
    deletePageButtons();
    if (current_page_max_number > 1){
        start_page_buttons_container = document.getElementById("start-page-buttons-container");
        nums_page_buttons_container = document.getElementById("nums-page-buttons-container");
        end_page_buttons_container = document.getElementById("end-page-buttons-container");
        createOnePageButton(start_page_buttons_container, "<<", pageButtonFunctions("<<"));
        createOnePageButton(start_page_buttons_container, "<", pageButtonFunctions("<"));

        if ((current_page_max_number - current_page) <= 6 && (current_page_max_number - current_page) >= 0) {
            if (current_page_max_number >= 9){
                for (let i = (current_page_max_number - 9); i < current_page_max_number; i++){
                    createOnePageButton(nums_page_buttons_container, i + 1, pageButtonNumberFunction);
                }
            } else {
                for (let i = 0; i < current_page_max_number; i++){
                    createOnePageButton(nums_page_buttons_container, i + 1, pageButtonNumberFunction);
                }
            }
        } else {
            if (current_page == 1) {
                if (current_page_max_number < 9){
                    for (let i = 0; i < current_page_max_number; i ++){
                        createOnePageButton(nums_page_buttons_container, i + 1, pageButtonNumberFunction);
                    }
                } else {
                    for (let i = 0; i < 9; i ++){
                        createOnePageButton(nums_page_buttons_container, i + 1, pageButtonNumberFunction);
                    }
                }
            } else {
                for (let i = (current_page - 2); i < (current_page + 7); i++) {
                    createOnePageButton(nums_page_buttons_container, i + 1, pageButtonNumberFunction);
                }
            }
        }
        createOnePageButton(end_page_buttons_container, ">", pageButtonFunctions(">"));
        createOnePageButton(end_page_buttons_container, ">>", pageButtonFunctions(">>"));
    }
}

function searchArrayFilter(item_list) {  //  функция ищет объекты, в тексте которых присутвует нужная строка
    search_field = document.getElementById("search-field");
    val = search_field.value.toUpperCase();
    ret_array = [];
    if (val != ""){
        for (var i = 0; i < item_list.length; i++) {
            if (item_list[i][button_texts[text_button_state]].toUpperCase().includes(val)){
                ret_array.push(item_list[i]);
            }
        }
    } else {
        ret_array = item_list;
    }
    return ret_array;
}

function sortButtonClick(event) {  // функция сортирует массив объектов
    button_type = event.target.id;
    if (button_type == "alphabet-sort-button"){
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = firstItem[button_texts[text_button_state]].toUpperCase();
              const string2 = secondItem[button_texts[text_button_state]].toUpperCase();
              if (string1 < string2) {return -1;}
              if (string1 > string2) {return 1;}
              return 0;
        });
    } else if (button_type == "rev_alphabet-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = firstItem[button_texts[text_button_state]].toUpperCase();
              const string2 = secondItem[button_texts[text_button_state]].toUpperCase();
              if (string1 < string2) {return 1;}
              if (string1 > string2) {return -1;}
              return 0;
        });
    } else if (button_type == "time-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = parseInt(firstItem["id"]);
              const string2 = parseInt(secondItem["id"]);
              if (string1 < string2) {return -1;}
              if (string1 > string2) {return 1;}
              return 0;
        });
    } else if (button_type == "rev_time-sort-button") {
        current_item_list.sort((firstItem, secondItem) => {
              const string1 = parseInt(firstItem["id"]);
              const string2 = parseInt(secondItem["id"]);
              if (string1 < string2) {return 1;}
              if (string1 > string2) {return -1;}
              return 0;
        });
    }
    pagerUpdate();
}

function deleteItemButtons(){  // функция удаляет предыдущие кнопки объектов
    prev_containers = document.getElementsByClassName("item-container");
    for (var i = 0; i < prev_containers.length; i++) {
        if (prev_containers[i] != null){
            prev_containers[i].remove();
            i--;
        }
    }
}

function createItemButtons(item_list) {  // функция создает кнопки объектов
    deleteItemButtons();
    if (item_list.length == 0) {
        document.getElementById("items-not-found-heading").hidden = false;
        return;
    } else {
        document.getElementById("items-not-found-heading").hidden = true;
    }
    for (let i = 0; i < item_list.length; i++){
        column = document.createElement("div")
        column.id = "item-container " + (i).toString();
        column.classList.add("item-container");

        item_button = document.createElement("a");
        item_button.id = "item_button " + i.toString();
        item_button.type = "button";
        item_button.href = "/profile/" + item_list[i].id;
        item_button.classList.add("btn");
        item_button.classList.add("btn-primary");
        item_button.classList.add("item-button");

        button_id = item_list[i].id;
        item_button.classList.add("user-item-button");
        item_button.innerText = item_list[i][button_texts[text_button_state]];

        column.appendChild(item_button);
        document.getElementById("items-row").appendChild(column);
    }
}

function onSearchChange(event) {  // функция обновляет текущий список объектов при изменении поля
    if (event.key != "Control"){
        current_item_list = searchArrayFilter(items_lists[filter_button_state]);
        showButtons();
    }
}

function onTextChangeButtonClick(event) {  // изменяет текст, который показывается на кнопках
    text_button_state = (text_button_state + 1) % button_texts.length;
    event.target.innerText = ["Включить просмотр почт", "Включить просмотр имен"][text_button_state];
    showButtons();
}


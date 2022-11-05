function itemButtonClick(event){
    prev_name = event.target.name
    if (prev_name == "added_item") {
        event.target.name = "not_added_item";
        event.target.classList.remove("added-item");
        event.target.classList.add("not-added-item");
        bool_added_items[parseInt(event.target.value, 10)] = 0;
    } else {
        event.target.name = "added_item";
        event.target.classList.remove("not-added-item");
        event.target.classList.add("added-item");
        bool_added_items[parseInt(event.target.value, 10)] = 1;
    }
}

function createEmptyItemButton(num, item_list) {
    column = document.createElement("div")
    column.id = "item-container " + (num).toString();
    column.classList.add("item-container");

    item_button = document.createElement("button");
    item_button.id = "item_button " + num.toString();
    item_button.type = "button";
    item_button.addEventListener("click", itemButtonClick, false);
    item_button.classList.add("btn");
    item_button.classList.add("btn-primary");
    item_button.classList.add("item-button");
    item_button.classList.add("user-item-button");
    button_id = item_list[num].id;
    item_button.value = button_id;
    if (bool_added_items[button_id] == 1) {
        item_button.classList.add("added-item")
        bool_added_items[button_id] = 1;
        item_button.name = "added_item";
    } else {
        item_button.classList.add("not-added-item")
        bool_added_items[button_id] = 0;
        item_button.name = "not_added_item";
    }
    return item_button
}

function createItemButtons(item_list){
    deleteItemButtons();
    if (item_list.length == 0) {
        document.getElementById("items-not-found-heading").hidden = false;
        return;
    } else {
        document.getElementById("items-not-found-heading").hidden = true;
    }
    for (let i = 0; i < item_list.length; i++){
        item_button = createEmptyItemButton(i, item_list);
        item_button.innerText = item_list[i][button_texts[text_button_state]];

        column.appendChild(item_button);
        document.getElementById("items-row").appendChild(column);
    }
}

function onSubmitButtonClick(event){
    form_res = document.getElementById("form-res");
    for (let i = 0; i < bool_added_items.length; i++){
        if (bool_added_items[i] != 0 && bool_added_items[i] != 1) {
            bool_added_items[i] = 0;
        }
    }
    // alert(bool_added_items);
    form_res.value = bool_added_items;
}

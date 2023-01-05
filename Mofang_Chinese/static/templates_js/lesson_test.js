function shuffle(array) {
  let currentIndex = array.length,  randomIndex;
  while (currentIndex != 0) {
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;
    [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
  }
  return array;
}

function resultsCheck(array){
    is_true = true;
    for (let i = 0; i < array.length; i++){
        if (!array[i]){
            is_true = false;
        }
    }
    return is_true;
}

function audioButtonClick(event){
    if (!task_audio.paused){task_audio.pause(); task_audio.currentTime = 0;}
    else {task_audio.play();}
    audio_playing = !audio_playing;
}

function buttonsDelete(){
    prev_but = document.getElementById("task-field-canvas");
    if (prev_but != null){prev_but.remove();}
    prev_but = document.getElementById("task-field-image");
    if (prev_but != null){prev_but.remove();}
    prev_but = document.getElementById("audio_but");
    if (prev_but != null){prev_but.hidden = true} // аудио кнопку удалять нельзя
    for (var i = 0; i < answer_button_number; i++) {
        prev_but = document.getElementById(i.toString());
        if (prev_but != null){prev_but.remove();}
    }
}

function showMistakes(){
    buttonsDelete();
    mistakes_holder = document.getElementById("mistakes-holder");
    mistakes_holder.hidden = false;
    mistakes_count = 0
    for (let i = 0; i < results.length; i++) {
        if (!results[i]) {
            mistakes_count += 1;
            word_id = lesson[i][lesson[i].length - 1];
            mistake_but = document.createElement("button");
            mistake_but.id = word_id.toString();
            mistake_but.innerText = lesson[i][0] + ' ' + lesson[i][1];
            mistake_but.classList.add("btn");
            mistake_but.classList.add("btn-main");
            mistake_but.classList.add("item-button");
            mistakes_holder.appendChild(mistake_but);
        }
    }
    if (mistakes_count == 0) {
        document.getElementById("mistakes-text").innerText = "Вы не совершили ни одной ошибки!";
    }
}

function sendTestReasults(){
    document.getElementById("test-header").innerText = "Вы прошли проверку знаний!";
    document.getElementById("bottom-t-first-layer").hidden = true;
    document.getElementById("bottom-t-second-layer").hidden = false;

    json_results = ``;
    word_ids = ``;
    for (let i = 0; i < results.length; i++){
        if (results[i]){
            json_results += `1.`;
        } else {
            json_results += `0.`;
        }
        word_ids += lesson[i][lesson[i].length - 1] + '.';
    }

    next_trainer_button = document.getElementById("next-trainer");
    if (next_trainer_button) {
        next_trainer_button.hidden = false;
        next_trainer_button.addEventListener("click", async function(event){
        const response = await fetch(result_url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: `{
           "id": "{{ test.id }}",
           "words": "` + word_ids + `",
           "results": "` + json_results + `"
          }`,
        });

            response.json().then(data => {
              console.log(data);
            });
        }, false)
    }
    back_to_lesson = document.getElementById("back-to-lesson")
    back_to_lesson.addEventListener("click", async function(event){

        const response = await fetch(result_url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: `{
           "id": "{{ test.id }}",
           "words": "` + word_ids + `",
           "results": "` + json_results + `"
          }`,
        });

        response.json().then(data => {
          console.log(data);
        });
    }, false)
}

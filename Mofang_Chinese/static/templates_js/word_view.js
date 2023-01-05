function onPlayButtonClick(event) {
    if (main_sound != "none"){
        if (main_sound.isPlaying){main_sound.stop();}
        else {
            main_sound.play();
        }
    }
}

function buttonsScreenUpdate(){
    playButton = document.getElementById("playButton");
    playButton.addEventListener("click", onPlayButtonClick, false);
    playButton.style.left = Math.round(width / 2) - play_button_size / 2 + "px";
    playButton.style.top = Math.round(height / 2) - half_cube_size - play_button_size * 2 + "px";
}

function screenUpdateCheck(){
    width = parent.innerWidth;
    height = parent.innerHeight;

    buttonsScreenUpdate();

    // without updating of the camara the cube proportions break
    camera = new THREE.PerspectiveCamera( size_of_scene, width / height, 0.1, 5 );  // camera perspective
    camera.position.z = camera_z;
    // without updating of the renderer the three.js window breaks
    renderer.setSize( width, height );  // cube lesson size on the screen
    renderer.setClearColor("#01131E");
    document.body.appendChild( renderer.domElement );
    renderer.render( scene, camera );

    scene.add( cube );

    // limit dots
    half_cube_size = Math.round((height * size_coef) / 2);
    cube_screen_cords = {"up left": [Math.round(width / 2) - half_cube_size, Math.round(height / 2) - half_cube_size],
                        "up right": [Math.round(width / 2) + half_cube_size, Math.round(height / 2) - half_cube_size],
                        "down left": [Math.round(width / 2) - half_cube_size, Math.round(height / 2) + half_cube_size],
                        "down right": [Math.round(width / 2) + half_cube_size, Math.round(height / 2) + half_cube_size]};
}

function changeSides(side, text_ang){
    geometry = new THREE.BoxGeometry( cube_scene_size, cube_scene_size, cube_scene_size );
    const loader = new THREE.TextureLoader();
    var filepath = "images/";
    if (side == "up") {
        if (text_ang == 90) {text_ang = 270;}
        else if (text_ang == 270) {text_ang = 90;}  // иначе слова вверх ногами
        materials[2] = new THREE.MeshBasicMaterial({map: cubeViewSideText(up_text, text_ang, up_color, "up")});
    }
    if (side == "down") {
        materials[3] = new THREE.MeshBasicMaterial({map: cubeViewSideText(down_text, text_ang, down_color, "down")});
    }
    old_rot_x = cube.rotation.x
    old_rot_y = cube.rotation.y
    old_rot_z = cube.rotation.z
    scene.remove(cube);
    //alert("Hy");
    cube = new THREE.Mesh(geometry, materials);
    cube.rotation.x = old_rot_x;
    cube.rotation.y = old_rot_y;
    cube.rotation.z = old_rot_z;
    scene.add( cube );
    // scene.overrideMaterial = new THREE.MeshBasicMaterial({map: loader.load(front_img)});
    // alert(front_img)
    // limit dots
    half_cube_size = Math.round((height * size_coef) / 2);
    cube_screen_cords = {"up left": [Math.round(width / 2) - half_cube_size, Math.round(height / 2) - half_cube_size],
                        "up right": [Math.round(width / 2) + half_cube_size, Math.round(height / 2) - half_cube_size],
                        "down left": [Math.round(width / 2) - half_cube_size, Math.round(height / 2) + half_cube_size],
                        "down right": [Math.round(width / 2) + half_cube_size, Math.round(height / 2) + half_cube_size]};
}

function undefinedAudioCheck(side){
    // alert(side.slice(8, 17));
    if (side.slice(8, 17) == "undefined"){
        // alert("undefined");
        document.getElementById("playButton").disabled = true;
    } else {
        document.getElementById("playButton").disabled = false;
    }
}

function buf_check(side, x, y, buffer_size){
    if (side == "up"){
        in_x = (x >= cube_screen_cords['up left'][0] && x <= cube_screen_cords['up right'][0]);
        y_buf_limit = cube_screen_cords["up left"][1] - (half_cube_size * buffer_size);
        in_y = (y >= y_buf_limit && y <= cube_screen_cords['up left'][1]);
        big_bufer = (in_x && in_y);

        left_limit = cube_screen_cords['up left'][0] + (half_cube_size * buffer_size);
        right_limit = cube_screen_cords['up right'][0]  - (half_cube_size * buffer_size);
        in_x = ((x >= left_limit && x <= right_limit));
        up_limit = cube_screen_cords["up left"][1];
        down_limit = (cube_screen_cords['up left'][1] + (half_cube_size * buffer_size));
        in_y = (y >=  up_limit && y <= down_limit);
        small_bufer =  (in_x && in_y);

        return big_bufer || small_bufer;
    }
    if (side == "down"){
        in_x = (x >= cube_screen_cords['up left'][0] && x <= cube_screen_cords['up right'][0]);
        up_limit = cube_screen_cords["down left"][1];
        down_limit = cube_screen_cords["down left"][1] + (half_cube_size * buffer_size);
        in_y = (y >= up_limit && y <= down_limit);
        big_bufer = (in_x && in_y);

        left_limit = cube_screen_cords['up left'][0] + (half_cube_size * buffer_size);
        right_limit = cube_screen_cords['up right'][0]  - (half_cube_size * buffer_size);
        in_x = (x >= left_limit && x <= right_limit);
        up_limit = cube_screen_cords["down left"][1] - (half_cube_size * buffer_size);
        down_limit = cube_screen_cords['down left'][1];
        in_y = (y >=  up_limit && y <= down_limit);
        small_bufer =  (in_x && in_y);
        return big_bufer || small_bufer;
    }
    if (side == "left"){
        left_limit = cube_screen_cords['up left'][0] - (half_cube_size * buffer_size);
        in_x = (x >=  left_limit && x <= cube_screen_cords['up left'][0]);
        in_y = (y >= cube_screen_cords["up left"][1] && y <= cube_screen_cords["down left"][1]);
        big_bufer = (in_x && in_y);

        left_limit = cube_screen_cords['up left'][0];
        right_limit = cube_screen_cords['up left'][0] + (half_cube_size * buffer_size);
        in_x = (x >= left_limit && x <= right_limit);
        up_limit = cube_screen_cords["up left"][1] + (half_cube_size * buffer_size);
        down_limit = cube_screen_cords['down left'][1] - (half_cube_size * buffer_size);
        in_y = (y >=  up_limit && y <= down_limit);
        small_bufer =  (in_x && in_y);
        return big_bufer || small_bufer;
    }
    if (side == "right"){
        right_limit = cube_screen_cords['up right'][0] + (half_cube_size * buffer_size);
        in_x = (x >= cube_screen_cords["up right"][0] && x <= right_limit);
        in_y = (y >= cube_screen_cords["up right"][1] && y <= cube_screen_cords["down right"][1]);
        big_bufer = (in_x && in_y);

        right_limit = cube_screen_cords['up right'][0];
        left_limit = cube_screen_cords['up right'][0] - (half_cube_size * buffer_size);
        in_x = (x >= left_limit && x <= right_limit);
        up_limit = cube_screen_cords["up right"][1] + (half_cube_size * buffer_size);
        down_limit = cube_screen_cords['down right'][1] - (half_cube_size * buffer_size);
        in_y = (y >=  up_limit && y <= down_limit);
        small_bufer =  (in_x && in_y);
        return big_bufer || small_bufer;
    }
}

function rotateUp() {
    if (angle_of_rotation_y == 0){  // и куб при этом стоял на месте
        if (cube_sides_y[current_side_y] != "up"){  // если это не сторона up
            angle_of_rotation_y = Math.PI * 0.5;  // крутимся
            current_side_y = (current_side_y + 1) % 4;  // измененяем сторону
            if (cube_sides_y[current_side_y] == "x side" && cube_sides_x[current_side_x] == "front"){
                changeAudio("front");
            }
            if (cube_sides_y[current_side_y] == "x side" && cube_sides_x[current_side_x] == "left"){
                changeAudio("left");
            }
            if (cube_sides_y[current_side_y] == "x side" && cube_sides_x[current_side_x] == "right"){
                changeAudio("right");
            }
            if (cube_sides_y[current_side_y] == "up"){  // если уже на стороне up
                changeSides("up", 90 * current_side_x);  // поворочиваем картинку на стороне up
                changeAudio("up");  // меняем аудио на сторону up
            }
        }
    }
}

function rotateDown() {
    if (angle_of_rotation_y == 0){
        if (cube_sides_y[current_side_y] != "down"){
            angle_of_rotation_y = -Math.PI * 0.5;
            current_side_y -= 1;
            if (current_side_y == -1){current_side_y = 3};
            if (cube_sides_y[current_side_y] == "x side" && cube_sides_x[current_side_x] == "front"){
                changeAudio("front");
            }
            if (cube_sides_y[current_side_y] == "x side" && cube_sides_x[current_side_x] == "left"){
                changeAudio("left");
            }
            if (cube_sides_y[current_side_y] == "x side" && cube_sides_x[current_side_x] == "right"){
                changeAudio("right");
            }
            if (cube_sides_y[current_side_y] == "down"){
                changeSides("down", 90 * current_side_x);
                changeAudio("down");
            }
        }
    }
}

function rotateRight() {
    if (angle_of_rotation_x == 0){
        if (cube_sides_x[current_side_x] != "right"){
            if ((cube_sides_y[current_side_y] != "down") && (cube_sides_y[current_side_y] != "up")){
                angle_of_rotation_x = -Math.PI * 0.5;
                current_side_x = (current_side_x + 1) % 4;
                if (cube_sides_y[current_side_y] == "x side"){
                    if (cube_sides_x[current_side_x] == "front"){
                        changeAudio("front");
                    }
                    if (cube_sides_x[current_side_x] == "right"){
                        changeAudio("right");
                    }
                }
            }
        }
    }
}

function rotateLeft() {
    if (angle_of_rotation_x == 0){
        if (cube_sides_x[current_side_x] != "left"){
            if ((cube_sides_y[current_side_y] != "down") && (cube_sides_y[current_side_y] != "up")){
                angle_of_rotation_x = Math.PI * 0.5;
                current_side_x -= 1;
                if (current_side_x == -1){current_side_x = 3};
                if (cube_sides_y[current_side_y] == "x side"){
                    if (cube_sides_x[current_side_x] == "front"){
                        changeAudio("front");
                    }
                    if (cube_sides_x[current_side_x] == "left"){
                        changeAudio("left");
                    }
                }
            }
        }
    }
}

function mouseListenerCubeRotation(e) {
    if (e.which == 1){
        mousex = e.clientX;
        mousey = e.clientY;
        // size of press zone 30%
        buffer_coef = 0.3

        if (buf_check("up", mousex, mousey, buffer_coef)){  // если пользователь нажал вверх
            rotateUp();
        }
        else if (buf_check("down", mousex, mousey, buffer_coef)){
            rotateDown();
        }
        else if (buf_check("right", mousex, mousey, buffer_coef)){
            rotateRight();
        }
        else if (buf_check("left", mousex, mousey, buffer_coef)){
            rotateLeft();
        }
    }
}

function arrowsCubeRotation(e) {
    if (e.key == "ArrowUp") {
        console.log("Up");
        rotateUp();
    } else if (e.key == "ArrowDown") {
        console.log("Down");
        rotateDown();
    } else if (e.key == "ArrowRight") {
        console.log("Right");
        rotateRight();
    } else if (e.key == "ArrowLeft") {
        console.log("Left");
        rotateLeft();
    }
    // console.log(e.key);
    // console.log(arrowsCubeRotation);
}

function cubeRotation(){
    if (angle_of_rotation_x > 0){
        if (angle_of_rotation_x > speed_of_rotation_x) {
            cube.rotation.y += speed_of_rotation_x;
            angle_of_rotation_x -= speed_of_rotation_x;
        }
        else {
            cube.rotation.y += angle_of_rotation_x;
            angle_of_rotation_x = 0;
        }
    }
    if (angle_of_rotation_x < 0){
        if (angle_of_rotation_x < -speed_of_rotation_x){
            cube.rotation.y -= speed_of_rotation_x;
            angle_of_rotation_x += speed_of_rotation_x;
        } else {
            cube.rotation.y += angle_of_rotation_x;
            angle_of_rotation_x = 0;
        }
    }
    if (angle_of_rotation_y > 0){
        if (angle_of_rotation_y > speed_of_rotation_y) {
            cube.rotation.x += speed_of_rotation_y;
            angle_of_rotation_y -= speed_of_rotation_y;
        }
        else {
            cube.rotation.x += angle_of_rotation_y;
            angle_of_rotation_y = 0;
        }
    }
    if (angle_of_rotation_y < 0){
        if (angle_of_rotation_y < -speed_of_rotation_y){
            cube.rotation.x -= speed_of_rotation_y;
            angle_of_rotation_y += speed_of_rotation_y;
        } else {
            cube.rotation.x += angle_of_rotation_y;
            angle_of_rotation_y = 0;
        }
    }
}

function render() {
    requestAnimationFrame( render );
    cubeRotation();
    screenUpdateCheck();
    // debug();
}

function imageSideText(text, color){
    const cv = document.createElement( 'canvas' );
    cube_width = 1000
    cv.width = cube_width;
    cv.height = cube_width;
    ctx = cv.getContext( '2d' );
    ctx.fillStyle = '#fefefe';
    ctx.fillRect( 0, 0, cv.width, cv.height );

    if (hints_enabled){
        ctx = addTopGrd(ctx, cube_width, 50);
        ctx = addBottomGrd(ctx, cube_width, 50);
        ctx = addLeftGrd(ctx, cube_width, 50);
    }

    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    symbol_size_const = 0.6;
    font_size = Math.round(cube_width / ((text.length + 1) * symbol_size_const));
    max_font_size = 150;
    if (font_size > max_font_size) {font_size = max_font_size;}
    ctx.font = 'bold ' + font_size + 'px Monospace';
    ctx.fillText(text, cube_width / 2, 0.825 * cube_width);

    new_image = document.getElementById("right_side_image");
    up_indent = 0.1 * cube_width
    down_indent = 0.2 * cube_width
    left_indent = 0.15 * cube_width
    right_indent = 0.15 * cube_width
    ctx.drawImage( new_image,
                   left_indent,
                   up_indent,
                   cube_width - right_indent - left_indent,
                   cube_width - down_indent - up_indent);

    const cvTexture1 = new THREE.Texture( cv );
    cvTexture1.needsUpdate = true;
    return cvTexture1;
}

function onHelpButtonClick(event){
    explanation_container = document.getElementById("explanation-container");
    explanation_container.hidden = !explanation_container.hidden;
    if (!explanation_container.hidden) {
        document.removeEventListener('mousedown', mouseListenerCubeRotation);
    } else {
        document.addEventListener('mousedown', mouseListenerCubeRotation);
    }
}

function onCloseButtonClick(event){
    explanation_container = document.getElementById("explanation-container");
    explanation_container.hidden = true;
    document.addEventListener('mousedown', mouseListenerCubeRotation);
}

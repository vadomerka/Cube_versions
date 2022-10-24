function lines_merger(text_arr, av_line_len){
    // объединение двух коротких слов в одну строчку через пробел, если короче average_line_len
    i = 0;
    while (i < (text_arr.length - 1)){
        if (text_arr[i + 1] == '') {text_arr.splice(i, 1);}
        if (i == 0){
            if ((text_arr[i + 1].length + text_arr[i].length + 1) < av_line_len) {
                text_arr[i] = text_arr[i] + ' ' + text_arr[i + 1];
                text_arr.splice(i + 1, 1);
                i--;
            }
        } else {
            if ((text_arr[i - 1].length + text_arr[i].length + 1) < av_line_len ||
                (text_arr[i + 1].length + text_arr[i].length + 1) < av_line_len){
                if (text_arr[i - 1].length < text_arr[i + 1].length) {
                    text_arr[i] = text_arr[i - 1] + ' ' + text_arr[i]
                    text_arr.splice(i - 1, 1);
                    i--;
                } else {
                    text_arr[i] = text_arr[i] + ' ' + text_arr[i + 1];
                    text_arr.splice(i + 1, 1);
                    i--;
                }
            }}
        i++;
    }
    return text_arr;
}

function hieroglyph_lines_merger(text_arr, av_line_len){
    i = 0; // отличается от функции lines_merger, потому что делит не пробелом, а запятой
    while (i < (text_arr.length - 1)){
        if (text_arr[i + 1] == '') {text_arr.splice(i, 1);}
        if (i == 0){
            if ((text_arr[i + 1].length + text_arr[i].length) < av_line_len) {
                text_arr[i] = text_arr[i] + text_arr[i + 1];
                text_arr.splice(i + 1, 1);
                i--;
            }
        } else {
            if ((text_arr[i - 1].length + text_arr[i].length) < av_line_len ||
                (text_arr[i + 1].length + text_arr[i].length) < av_line_len){
                if (text_arr[i - 1].length < text_arr[i + 1].length) {
                    text_arr[i] = text_arr[i - 1] + text_arr[i]
                    text_arr.splice(i - 1, 1);
                    i--;
                } else {
                    text_arr[i] = text_arr[i] + text_arr[i + 1];
                    text_arr.splice(i + 1, 1);
                    i--;
                }
            }}
        i++;
    }
    return text_arr;
}

function lines_print(ctx, text_arr, cube_width, symbol_width_coef, symbol_height_coef){
    max_line_len = 0;
    for (var i = 0; i < text_arr.length; i++) {
        if (max_line_len < text_arr[i].length) {
            max_line_len = text_arr[i].length;
        }
    }
    font_size = Math.round(cube_width / ((max_line_len + 1) * symbol_width_coef));
    max_font_size = 250
    if (font_size > max_font_size) {font_size = max_font_size;}
    symbol_height = font_size * symbol_height_coef;
    lines_number = (cube_width / symbol_height).toString().split(".")[0];
    prelines_px = (cube_width % symbol_height) / 2;
    if (lines_number % 2 != text_arr.length % 2) {
        lines_number = parseInt(lines_number) + 1;
        prelines_px -= symbol_height / 4;
    }
    ctx.font = 'bold ' + font_size + 'px Monospace';
    for (var i = 0; i < text_arr.length; i++) {
        line_num = (i + ((lines_number - text_arr.length) / 2)) / lines_number;
        ctx.fillText(text_arr[i], cube_width / 2, line_num * cube_width + prelines_px);
    }
    return ctx;
}

function cubeViewSideText(text, text_ang){
    const cv = document.createElement( 'canvas' );
    cube_width = 1000
    cv.width = cube_width //  3 * 512
    cv.height = cube_width;
    var ctx = cv.getContext( '2d' );
    ctx.save();
    ctx.rotate(text_ang * (Math.PI/180));
    if (text_ang == 90) {ctx.translate( 0, -cv.width );}
    if (text_ang == 180) {ctx.translate( -cv.width, -cv.width );}
    if (text_ang == 270) {ctx.translate( -cv.width, 0 );}
    // ctx.translate( 0, 0 );  // -cv.width
    ctx.fillStyle = '#fefefe';
    ctx.fillRect( 0, 0, cv.width, cv.height );
    ctx.fillStyle = '#129912';
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    text_words = text.split(" ");
    text_words = lines_merger(text_words, 10);
    // коэффициенты считал отношением 1000 к количеству символов в monospace помещающихся при таком-то фонте
    // например: 1000/6 = 166.6667 при font = 276, symbol_size_const = 0,603864734
    //           1000/7 = 142.9 при font = 236, symbol_size_const = 0,605326877
    ctx = lines_print(ctx, text_words, cube_width, 0.6, 1.166);
    ctx.restore();
    const cvTexture = new THREE.Texture( cv );
    cvTexture.needsUpdate = true; // otherwise all black only
    return cvTexture;
}

function cubeViewSideHieroglyphText(text, text_ang){
    const cv = document.createElement( 'canvas' );
    cube_width = 1000
    cv.width = cube_width
    cv.height = cube_width;
    var ctx = cv.getContext( '2d' );
    ctx.save();
    ctx.rotate(text_ang * (Math.PI/180));
    if (text_ang == 90) {ctx.translate( 0, -cv.width );}
    if (text_ang == 180) {ctx.translate( -cv.width, -cv.width );}
    if (text_ang == 270) {ctx.translate( -cv.width, 0 );}

    ctx.fillStyle = '#fefefe';
    ctx.fillRect( 0, 0, cv.width, cv.height );
    ctx.fillStyle = '#129912';
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    text_words = text.split("，");
    for (var i = 0; i < text_words.length - 1; i++) {
        text_words[i] += "，";
    }
    text_words = hieroglyph_lines_merger(text_words, 10);
    // считал отношением 1000 к количеству символов в monospace помещающихся при таком-то фонте
    // для иерглифов:
    // width
    // 1000/16 = 62,5 при font = 62 1
    // 1000/4 = 250 при font = 250  1
    // height
    // 334 при font = 230  1,452173913
    // 145 при font = 100  1,45
    ctx = lines_print(ctx, text_words, cube_width, 1, 1.45);
    ctx.restore();
    const cvTexture = new THREE.Texture( cv );
    cvTexture.needsUpdate = true; // otherwise all black only
    return cvTexture;
}

function task_text(canvas_to_change, text, cv_width){
    // const cv = document.createElement( 'canvas' );
    const cv = canvas_to_change;
    // console.log(text);
    // text_size = 150;
    cube_width = cv_width;
    cv.width = cv_width //  3 * 512
    cv.height = cv_width;

    var ctx = cv.getContext( '2d' );

    ctx.fillStyle = '#fefefe';
    ctx.fillRect( 0, 0, cv.width, cv.height );
    ctx.fillStyle = '#129912';
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    text_words = text.split(" ");
    text_words = lines_merger(text_words, 10);
    console.log(text_words);
    ctx = lines_print(ctx, text_words, cube_width, 0.6, 1.166);
    return cv;
}
function task_hieroglyph_text(canvas_to_change, text, cv_width){
    // const cv = document.createElement( 'canvas' );
    const cv = canvas_to_change;
    // console.log(text);
    // text_size = 150;
    cube_width = cv_width;
    cv.width = cv_width //  3 * 512
    cv.height = cv_width;

    var ctx = cv.getContext( '2d' );

    ctx.fillStyle = '#fefefe';
    ctx.fillRect( 0, 0, cv.width, cv.height );
    ctx.fillStyle = '#129912';
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    text_words = text.split("，");
    for (var i = 0; i < text_words.length - 1; i++) {
        text_words[i] += "，";
    }
    text_words = hieroglyph_lines_merger(text_words, 10);
    // считал отношением 1000 к количеству символов в monospace помещающихся при таком-то фонте
    // для иерглифов:
    // width
    // 1000/16 = 62,5 при font = 62 1
    // 1000/4 = 250 при font = 250  1
    // height
    // 334 при font = 230  1,452173913
    // 145 при font = 100  1,45
    ctx = lines_print(ctx, text_words, cube_width, 1, 1.45);
    return cv;
}

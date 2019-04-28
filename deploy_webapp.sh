# Install dependencies for this script:
# sudo apt install npm
# npm install handlebars

TARGET_JS=bathouse.minified.js
TARGET_CSS=bathouse.minified.css

# Clean (make sure loading old scripts fail)
rm webapp/*$TARGET_JS
rm webapp/*$TARGET_CSS

echo "" > tmp.$TARGET_JS
echo "" > tmp.$TARGET_CSS

# Compile templates
node node_modules/.bin/handlebars \
        -k each -k if -k selectIfEq -k media_player_formatSeconds \
        ./webapp/templates/* >> tmp.$TARGET_JS

# Minify app dependencies
minify ./webapp/js/graphs.js >> tmp.$TARGET_JS
minify ./webapp/js/templated_thing.js >> tmp.$TARGET_JS
minify ./webapp/js/scene_list.js >> tmp.$TARGET_JS
minify ./webapp/js/mqtt_device_info.js >> tmp.$TARGET_JS
minify ./webapp/js/media_player.js >> tmp.$TARGET_JS
minify ./webapp/js/lamp.js >> tmp.$TARGET_JS
minify ./webapp/js/baticueva_tv_extras.js >> tmp.$TARGET_JS
minify ./webapp/js/mfp.js >> tmp.$TARGET_JS
minify ./webapp/js/app.js >> tmp.$TARGET_JS

# Minify css files 
minify ./webapp/css/* >> tmp.$TARGET_CSS

mv tmp.$TARGET_JS  ./webapp/`md5sum tmp.$TARGET_JS  | cut -c 1-10`.$TARGET_JS
mv tmp.$TARGET_CSS ./webapp/`md5sum tmp.$TARGET_CSS | cut -c 1-10`.$TARGET_CSS

echo "Created files:"
ls webapp/*$TARGET_JS
ls webapp/*$TARGET_CSS


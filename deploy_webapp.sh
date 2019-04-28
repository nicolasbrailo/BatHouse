# sudo apt install npm
# npm install handlebars -g

# node node_modules/.bin/handlebars -k each -k if -k selectIfEq -k media_player_formatSeconds ./templates/*

TARGET_JS=bathouse.minified.js
TARGET_CSS=bathouse.minified.css

rm webapp/*$TARGET_JS
rm webapp/*$TARGET_CSS

echo "" > tmp.$TARGET_JS
echo "" > tmp.$TARGET_CSS

wget http://cdnjs.cloudflare.com/ajax/libs/dygraph/2.1.0/dygraph.min.js -qO- >> tmp.$TARGET_JS
echo "" >> tmp.$TARGET_JS
wget http://dygraphs.com/extras/smooth-plotter.js -qO- >> tmp.$TARGET_JS
wget https://code.jquery.com/jquery-3.2.1.min.js -qO- >> tmp.$TARGET_JS
wget https://cdnjs.cloudflare.com/ajax/libs/handlebars.js/4.1.1/handlebars.min.js -qO- >> tmp.$TARGET_JS

minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/js/bootstrap.min.js >> tmp.$TARGET_JS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/app.js >> tmp.$TARGET_JS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/templated_thing.js >> tmp.$TARGET_JS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/media_player/model.js >> tmp.$TARGET_JS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/mqtt_device_info/model.js >> tmp.$TARGET_JS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/lamp/model.js >> tmp.$TARGET_JS
minify ./webapp/app.js >> tmp.$TARGET_JS


wget http://cdnjs.cloudflare.com/ajax/libs/dygraph/2.1.0/dygraph.min.css -qO- >> tmp.$TARGET_CSS

minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/css/bootstrap-theme.min.css >> tmp.$TARGET_CSS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/css/bootstrap.min.css >> tmp.$TARGET_CSS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/media_player/style.css >> tmp.$TARGET_CSS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/mqtt_device_info/style.css >> tmp.$TARGET_CSS
minify ./zigbee2mqtt2flask/zigbee2mqtt2flask/webapp/things/lamp/style.css >> tmp.$TARGET_CSS
minify ./webapp/custom_styles.css >> tmp.$TARGET_CSS

mv tmp.$TARGET_JS  ./webapp/`md5sum tmp.$TARGET_JS  | cut -c 1-10`.$TARGET_JS
mv tmp.$TARGET_CSS ./webapp/`md5sum tmp.$TARGET_CSS | cut -c 1-10`.$TARGET_CSS

echo "Created files:"
ls webapp/*$TARGET_JS
ls webapp/*$TARGET_CSS


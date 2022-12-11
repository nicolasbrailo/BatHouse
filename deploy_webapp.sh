# Install dependencies for this script:
# sudo apt install npm
# npm install handlebars

TARGET_JS=bathouse.minified.js
TARGET_CSS=bathouse.minified.css
DEPLOY_PATH=webapp
MINIFY_APP=cat

PATH_OLD_JS=`ls $DEPLOY_PATH/*$TARGET_JS || echo 0000000NOOLDFILE`
PATH_OLD_CSS=`ls $DEPLOY_PATH/*$TARGET_CSS || echo 0000000NOOLDFILE`
HASH_OLD_JS=`echo $PATH_OLD_JS | cut -c8-17`
HASH_OLD_CSS=`echo $PATH_OLD_CSS | cut -c8-17`
echo "Old JS hash is $HASH_OLD_JS, old CSS hash is $HASH_OLD_CSS."

# Clean (make sure loading old scripts fail)
rm -f $DEPLOY_PATH/*$TARGET_JS
rm -f $DEPLOY_PATH/*$TARGET_CSS

echo "" > tmp.$TARGET_JS
echo "" > tmp.$TARGET_CSS

echo "Compiling Handlebar templates"
node node_modules/.bin/handlebars \
        -k each -k if -k selectIfEq -k media_player_formatSeconds \
        ./$DEPLOY_PATH/templates/* >> tmp.$TARGET_JS

echo "Minifying app .js files"
$MINIFY_APP ./$DEPLOY_PATH/js/graphs.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/templated_thing.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/scene_list.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/mqtt_device_info.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/media_player.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/lamp.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/outlet.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/baticueva_tv_extras.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/mfp.js >> tmp.$TARGET_JS
$MINIFY_APP ./$DEPLOY_PATH/js/app.js >> tmp.$TARGET_JS

# Minify css files 
echo "Minifying app .css files"
$MINIFY_APP ./$DEPLOY_PATH/css/* >> tmp.$TARGET_CSS

HASH_NEW_JS=`md5sum tmp.$TARGET_JS | cut -c 1-10`
HASH_NEW_CSS=`md5sum tmp.$TARGET_CSS | cut -c 1-10`

echo "New JS hash is $HASH_NEW_JS, new CSS hash is $HASH_NEW_CSS."
for fn in `grep $HASH_OLD_JS $DEPLOY_PATH/*.html | awk -F':' '{print $1}'`; do
    echo "Warning: $fn will break. Patching hash..."
    sed -i -e "s/$HASH_OLD_JS/$HASH_NEW_JS/g" $fn
    sed -i -e "s/$HASH_OLD_CSS/$HASH_NEW_CSS/g" $fn
    echo "Fixed!"
done

mv tmp.$TARGET_JS  ./$DEPLOY_PATH/$HASH_NEW_JS.$TARGET_JS
mv tmp.$TARGET_CSS ./$DEPLOY_PATH/$HASH_NEW_CSS.$TARGET_CSS

echo "Deployed:"
ls $DEPLOY_PATH/*$TARGET_JS
ls $DEPLOY_PATH/*$TARGET_CSS


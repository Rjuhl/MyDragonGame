#!/bin/bash
set -e

APP_NAME="MyDragonGame"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${APP_NAME}.dmg"
BACKGROUND_IMG="assets/studio_background.png"
STAGING="/tmp/${APP_NAME}_dmg_staging"
RW_DMG="/tmp/${APP_NAME}_rw.dmg"

# Window size matches background image (560x560)
WINDOW_W=560
WINDOW_H=560

# Icon positions
APP_X=140
APP_Y=280
LINK_X=420
LINK_Y=280

echo "==> Cleaning up previous staging and any stuck mounts..."
hdiutil detach "/Volumes/${APP_NAME}" 2>/dev/null || true
hdiutil detach "/Volumes/${APP_NAME} 1" 2>/dev/null || true
rm -rf "$STAGING" "$RW_DMG"
mkdir -p "$STAGING/.background"

echo "==> Copying app and creating Applications symlink..."
cp -r "$APP_PATH" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

echo "==> Copying background image..."
cp "$BACKGROUND_IMG" "$STAGING/.background/background.png"

echo "==> Calculating DMG size..."
STAGING_SIZE_MB=$(du -sm "$STAGING" | awk '{print $1}')
DMG_SIZE_MB=$(( STAGING_SIZE_MB + 50 ))
echo "    Staging size: ${STAGING_SIZE_MB}MB  DMG size (+50MB buffer): ${DMG_SIZE_MB}MB"

echo "==> Creating read-write DMG..."
hdiutil create -srcfolder "$STAGING" -volname "$APP_NAME" \
  -fs HFS+ -fsargs "-c c=16,b=4096" \
  -format UDRW -size "${DMG_SIZE_MB}m" "$RW_DMG"

echo "==> Mounting DMG..."
MOUNT_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "$RW_DMG")
DEVICE=$(echo "$MOUNT_OUTPUT" | awk '/Apple_HFS/ {print $1}')
VOLUME=$(echo "$MOUNT_OUTPUT" | grep -o '/Volumes/.*' | tail -1)
echo "    Device: $DEVICE  Volume: $VOLUME"

sleep 2

echo "==> Configuring Finder window via AppleScript..."
osascript <<APPLESCRIPT
tell application "Finder"
  tell disk "$APP_NAME"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set the bounds of container window to {400, 100, $((400 + WINDOW_W)), $((100 + WINDOW_H))}
    set viewOptions to the icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 100
    set background picture of viewOptions to POSIX file ("${VOLUME}/.background/background.png")
    set position of item "${APP_NAME}.app" of container window to {$APP_X, $APP_Y}
    set position of item "Applications" of container window to {$LINK_X, $LINK_Y}
    close
    open
    update without registering applications
    delay 2
    close
  end tell
end tell
APPLESCRIPT

echo "==> Syncing and unmounting..."
sync
hdiutil detach "$DEVICE"

echo "==> Converting to compressed read-only DMG..."
rm -f "$DMG_PATH"
hdiutil convert "$RW_DMG" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"

echo "==> Cleaning up..."
rm -rf "$STAGING" "$RW_DMG"

echo ""
echo "Done! DMG created at: $DMG_PATH"

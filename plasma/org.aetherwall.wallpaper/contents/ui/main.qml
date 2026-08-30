import QtQuick
import org.kde.plasma.plasmoid

WallpaperItem {
    id: root
    anchors.fill: parent
    property string mediaPath: root.configuration.mediaPath || ""
    property string telemetryUrl: root.configuration.telemetryPath || ""
    property string fitMode: root.configuration.fitMode || "fill"
    property bool reactiveEnabled: root.configuration.reactiveEnabled !== false
    property bool blurEnabled: root.configuration.blurEnabled !== false
    property real blurStrength: Number(root.configuration.blurStrength || 65)
    property bool showTitle: root.configuration.showTitle !== false
    property bool showClock: root.configuration.showClock !== false
    property bool showSystem: root.configuration.showSystem !== false
    property bool showMeters: root.configuration.showMeters !== false
    property bool showHistory: root.configuration.showHistory !== false
    property bool showDock: root.configuration.showDock !== false

    function imageFill() {
        if (fitMode === "fit") return Image.PreserveAspectFit
        if (fitMode === "stretch") return Image.Stretch
        return Image.PreserveAspectCrop
    }

    Rectangle { anchors.fill: parent; color: "#000000" }
    Image {
        id: wallpaperImage
        anchors.fill: parent
        source: root.mediaPath
        fillMode: root.imageFill()
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
    }
    Hud {
        anchors.fill: parent
        telemetryUrl: root.telemetryUrl
        mediaPath: root.mediaPath
        backgroundItem: wallpaperImage
        reactiveEnabled: root.reactiveEnabled
        blurEnabled: root.blurEnabled
        blurStrength: root.blurStrength
        showTitle: root.showTitle
        showClock: root.showClock
        showSystem: root.showSystem
        showMeters: root.showMeters
        showHistory: root.showHistory
        showDock: root.showDock
        visible: root.reactiveEnabled
    }

    Component.onCompleted: console.log("AetherWall v4.0.0 image wallpaper loaded:", root.mediaPath)
}

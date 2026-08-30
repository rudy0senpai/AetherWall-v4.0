import QtQuick
import QtMultimedia
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

    Rectangle { anchors.fill: parent; color: "#000000" }
    VideoOutput {
        id: videoOutput
        anchors.fill: parent
        fillMode: root.fitMode === "fit" ? VideoOutput.PreserveAspectFit : (root.fitMode === "stretch" ? VideoOutput.Stretch : VideoOutput.PreserveAspectCrop)
    }
    MediaPlayer {
        id: player
        source: root.mediaPath
        autoPlay: true
        loops: MediaPlayer.Infinite
        videoOutput: videoOutput
        audioOutput: AudioOutput { muted: true; volume: 0.0 }
        onMediaStatusChanged: if (mediaStatus === MediaPlayer.LoadedMedia || mediaStatus === MediaPlayer.BufferedMedia || mediaStatus === MediaPlayer.StalledMedia) play()
        onSourceChanged: if (source) play()
        onErrorOccurred: console.log("AetherWall video error:", error, errorString)
    }
    Hud {
        anchors.fill: parent
        telemetryUrl: root.telemetryUrl
        mediaPath: root.mediaPath
        backgroundItem: videoOutput
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

    Component.onCompleted: console.log("AetherWall v4.0.0 video wallpaper loaded:", root.mediaPath)
}

import QtQuick
import Qt5Compat.GraphicalEffects

Item {
    id: root
    property Item sourceItem
    property rect sourceRect: Qt.rect(0, 0, width, height)
    property bool enabled: true
    property real strength: 0.65
    clip: true

    ShaderEffectSource {
        id: capture
        anchors.fill: parent
        sourceItem: root.sourceItem
        sourceRect: root.sourceRect
        live: true
        hideSource: false
        recursive: false
        smooth: true
        visible: root.enabled
    }

    FastBlur {
        anchors.fill: parent
        source: capture
        radius: Math.max(0, Math.min(48, root.strength * 48))
        transparentBorder: true
        visible: root.enabled
        opacity: 0.92
    }
}

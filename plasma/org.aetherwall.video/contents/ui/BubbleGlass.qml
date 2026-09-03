import QtQuick

Item {
    id: root
    property Item sourceItem
    property rect sourceRect: Qt.rect(0, 0, width, height)
    property bool blurEnabled: true
    property real blurStrength: 0.65
    property color panelColor: "#e007101d"
    property color edgeColor: "#42ffffff"
    property color accent: "#b05cff"
    property color shadowColor: "#aa000000"
    property real radius: 22

    // A soft offset layer creates the raised / bubble-glass depth.
    Rectangle {
        anchors.fill: parent
        anchors.margins: 3
        radius: root.radius + 3
        color: root.shadowColor
        opacity: 0.55
    }

    FrostedRegion {
        anchors.fill: parent
        sourceItem: root.sourceItem
        sourceRect: root.sourceRect
        enabled: root.blurEnabled
        strength: root.blurStrength
        opacity: root.blurEnabled ? 1.0 : 0.0
    }

    Rectangle {
        anchors.fill: parent
        radius: root.radius
        color: root.panelColor
        opacity: root.blurEnabled ? 0.48 : 0.78
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: root.radius - 1
        color: "transparent"
        border.width: 1
        border.color: root.edgeColor
    }

    // Glossy top edge and lower inner reflection.
    Rectangle {
        x: root.width * 0.06; y: root.height * 0.06
        width: root.width * 0.38; height: Math.max(1, root.height * 0.012)
        radius: height
        color: "#55ffffff"
    }
    Rectangle {
        x: root.width * 0.08; y: root.height * 0.88
        width: root.width * 0.52; height: Math.max(1, root.height * 0.008)
        radius: height
        color: root.accent
        opacity: 0.18
    }
}

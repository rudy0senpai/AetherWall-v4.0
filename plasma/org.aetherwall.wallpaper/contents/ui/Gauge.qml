import QtQuick
import QtQuick.Shapes

Item {
    id: root
    property real value: 0
    property string label: ""
    property string subtext: ""
    property color accent: "#9b4bff"
    property color panelColor: "#070b17e8"
    property color textColor: "#f0f3ff"
    property color mutedColor: "#b9c3d7"
    property color trackColor: "#26304acc"
    property color gridColor: "#50556e55"
    property color edgeColor: "#ffffff30"
    property color shadowColor: "#00000099"
    property real displayValue: 0

    Behavior on displayValue { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
    Behavior on accent { ColorAnimation { duration: 700; easing.type: Easing.InOutCubic } }
    Behavior on panelColor { ColorAnimation { duration: 700; easing.type: Easing.InOutCubic } }
    Behavior on textColor { ColorAnimation { duration: 700; easing.type: Easing.InOutCubic } }
    Behavior on mutedColor { ColorAnimation { duration: 700; easing.type: Easing.InOutCubic } }
    onValueChanged: displayValue = Math.max(0, Math.min(100, Number(value) || 0))
    Component.onCompleted: displayValue = Math.max(0, Math.min(100, Number(value) || 0))

    // Depth / extrusion layer.
    Rectangle { x: width*0.045; y: height*0.055; width: root.width*0.91; height: root.height*0.91; radius: width/2; color: root.shadowColor; opacity: .65 }
    Rectangle {
        anchors.fill: parent; radius: width/2
        border.width: Math.max(1, root.height*.004); border.color: root.edgeColor
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.lighter(root.panelColor, 1.20) }
            GradientStop { position: 0.45; color: root.panelColor }
            GradientStop { position: 1.0; color: Qt.darker(root.panelColor, 1.16) }
        }
    }
    Rectangle { x: width*.08; y: height*.08; width: width*.84; height: height*.84; radius: width/2; color: "transparent"; border.width: Math.max(1, root.height*.0025); border.color: root.edgeColor; opacity: .55 }
    Rectangle { x: width*.17; y: height*.12; width: width*.48; height: height*.022; radius: height*.011; color: Qt.lighter(root.edgeColor, 1.8); opacity: .32 }

    Text { anchors.horizontalCenter: parent.horizontalCenter; y: root.height*.30; text: root.label; color: root.textColor; font.pixelSize: root.height*.085 }
    Text { anchors.horizontalCenter: parent.horizontalCenter; y: root.height*.42; text: root.displayValue.toFixed(1)+"%"; color: root.textColor; font.pixelSize: root.height*.14; font.bold: true }
    Text { anchors.horizontalCenter: parent.horizontalCenter; y: root.height*.58; text: root.subtext; color: root.mutedColor; font.pixelSize: root.height*.062 }

    Shape {
        anchors.fill: parent; preferredRendererType: Shape.CurveRenderer; layer.enabled: true; layer.samples: 4
        ShapePath { strokeColor: root.trackColor; strokeWidth: root.height*.014; fillColor: "transparent"; capStyle: ShapePath.RoundCap
            PathAngleArc { centerX: root.width/2; centerY: root.height/2; radiusX: root.width*.42; radiusY: root.height*.42; startAngle: -130; sweepAngle: 260 } }
        ShapePath { strokeColor: root.accent; strokeWidth: root.height*.026; fillColor: "transparent"; capStyle: ShapePath.RoundCap
            PathAngleArc { centerX: root.width/2; centerY: root.height/2; radiusX: root.width*.42; radiusY: root.height*.42; startAngle: -130; sweepAngle: 260*root.displayValue/100 } }
    }
    Rectangle { x: width*.50; y: height*.075; width: width*.09; height: height*.012; radius: height*.006; color: root.accent; opacity: .45; rotation: -18; transformOrigin: Item.Center }
}

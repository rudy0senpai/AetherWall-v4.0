import QtQuick
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root
    width: 360
    height: 210
    implicitWidth: 360
    implicitHeight: 210

    property real cpu: 0
    property real ram: 0
    property real battery: 0
    property real cpuTemp: -1
    property string power: "Unknown"
    property bool busy: false
    property string telemetryUrl: "http://127.0.0.1:8765/telemetry"

    function clamp(v) { return Math.max(0, Math.min(100, Number(v) || 0)); }
    function poll() {
        if (busy) return;
        busy=true;
        var xhr=new XMLHttpRequest(); xhr.open("GET", telemetryUrl+"?t="+Date.now());
        xhr.onreadystatechange=function(){
            if(xhr.readyState!==XMLHttpRequest.DONE)return;
            busy=false;
            if(xhr.status<200||xhr.status>=300)return;
            try{var d=JSON.parse(xhr.responseText);root.cpu=clamp(d.cpu);root.ram=clamp(d.ram);root.battery=clamp(d.battery);root.cpuTemp=(d.cpu_temp===null||d.cpu_temp===undefined)?-1:Number(d.cpu_temp);root.power=String(d.power||"Unknown");}catch(e){}
        }; xhr.send();
    }

    Rectangle {
        anchors.fill: parent
        radius: 24
        color: "#07101de8"
        border.width: 1
        border.color: "#ffffff48"
        layer.enabled: true
    }
    Rectangle { x: 14; y: 12; width: 110; height: 3; radius: 2; color: "#b05cff"; opacity: .7 }
    Text { x: 16; y: 24; text: "AETHERWALL"; color: "#f6f7ff"; font.pixelSize: 18; font.bold: true }
    Text { x: 16; y: 49; text: "REACTIVE SYSTEM HUD"; color: "#28c8ff"; font.pixelSize: 10; font.bold: true }
    Text { x: 205; y: 20; width: 135; horizontalAlignment: Text.AlignRight; text: clockText; color: "#f6f7ff"; font.pixelSize: 22; font.bold: true }
    Text { x: 205; y: 49; width: 135; horizontalAlignment: Text.AlignRight; text: dayText; color: "#b9c3d7"; font.pixelSize: 10 }

    Repeater {
        model: ["CPU", "RAM", "BATTERY"]
        delegate: Item {
            x: 16 + index*111; y: 79; width: 101; height: 108
            Rectangle { anchors.fill: parent; radius: 18; color: "#0b1424d8"; border.width: 1; border.color: index===0?"#b05cff":index===1?"#28c8ff":"#78ff35" }
            Text { anchors.horizontalCenter: parent.horizontalCenter; y: 15; text: modelData; color: "#f6f7ff"; font.pixelSize: 12; font.bold: true }
            Text { anchors.horizontalCenter: parent.horizontalCenter; y: 40; text: index===0?root.cpu.toFixed(1)+"%":index===1?root.ram.toFixed(1)+"%":root.battery.toFixed(1)+"%"; color: "#f6f7ff"; font.pixelSize: 21; font.bold: true }
            Rectangle { x: 13; y: 78; width: 75; height: 5; radius: 3; color: "#253149" }
            Rectangle { x: 13; y: 78; width: 75*(index===0?root.cpu:index===1?root.ram:root.battery)/100; height: 5; radius: 3; color: index===0?"#b05cff":index===1?"#28c8ff":"#78ff35" }
        }
    }
    Text { x: 16; y: 190; text: root.cpuTemp<0 ? "CPU AVG TEMP  N/A" : "CPU AVG TEMP  "+root.cpuTemp.toFixed(1)+"°C"; color: "#cbd4e7"; font.pixelSize: 10 }
    Text { x: 210; y: 190; width: 130; horizontalAlignment: Text.AlignRight; text: root.power; color: "#78ff35"; font.pixelSize: 10; font.bold: true }

    property string clockText: "00:00:00"
    property string dayText: "SUNDAY"
    Timer { interval:1000; repeat:true; running:true; triggeredOnStart:true; onTriggered:{var d=new Date();function p(n){return n<10?"0"+n:n;}root.clockText=p(d.getHours())+":"+p(d.getMinutes())+":"+p(d.getSeconds());root.dayText=["SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"][d.getDay()];} }
    Timer { interval:1000; repeat:true; running:true; triggeredOnStart:true; onTriggered:root.poll() }
}

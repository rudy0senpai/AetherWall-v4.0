import QtQuick

Item {
    id: hud
    property string telemetryUrl: ""
    property string mediaPath: ""
    property Item backgroundItem: null
    property bool reactiveEnabled: true
    property bool blurEnabled: true
    property real blurStrength: 65
    property bool showTitle: true
    property bool showClock: true
    property bool showSystem: true
    property bool showMeters: true
    property bool showHistory: true
    property bool showDock: true
    property real cpu: 0
    property real ram: 0
    property real ramUsed: 0
    property real battery: 0
    property real cpuTemp: -1
    property string power: "Unknown"
    property var history: []
    property bool connected: false
    property bool requestInFlight: false
    property real s: Math.min(width / 1600, height / 900)
    property real ox: (width - 1600*s) / 2
    property real oy: (height - 900*s) / 2
    function X(v) { return ox + v*s; }
    function Y(v) { return oy + v*s; }

    property color panelColor: "#e8070b17"
    property color textColor: "#f5f7ff"
    property color mutedColor: "#b9c3d7"
    property color accentColor: "#9b4bff"
    property color accent2Color: "#28b9ff"
    property color accent3Color: "#6eff37"
    property color gridColor: "#5550556e"
    property color trackColor: "#b8282d41"
    property color edgeColor: "#30ffffff"
    property color shadowColor: "#88000000"
    property var zoneThemes: ({})

    function clamp(v) { return Math.max(0, Math.min(100, Number(v) || 0)); }
    function tempPercent() { return cpuTemp < 0 ? 0 : clamp((cpuTemp - 25) * 100 / 75); }
    function themeValue(zone, key, fallback) {
        var z = hud.zoneThemes && hud.zoneThemes[zone] ? hud.zoneThemes[zone] : null;
        return z && z[key] ? z[key] : fallback;
    }
    function applyTheme(t) {
        if (!t) return;
        if (t.panel) panelColor=t.panel;
        if (t.text) textColor=t.text;
        if (t.muted) mutedColor=t.muted;
        if (t.accent) accentColor=t.accent;
        if (t.accent2) accent2Color=t.accent2;
        if (t.accent3) accent3Color=t.accent3;
        if (t.grid) gridColor=t.grid;
        if (t.track) trackColor=t.track;
        if (t.edge) edgeColor=t.edge;
        if (t.shadow) shadowColor=t.shadow;
        if (t.zones) zoneThemes=t.zones;
    }
    function pollTelemetry() {
        if (!telemetryUrl || requestInFlight) return;
        requestInFlight=true;
        var xhr=new XMLHttpRequest();
        var media=encodeURIComponent(mediaPath || "");
        xhr.open("GET",telemetryUrl+"?t="+Date.now()+"&media="+media);
        xhr.onreadystatechange=function(){
            if(xhr.readyState!==XMLHttpRequest.DONE)return;
            requestInFlight=false;
            if(xhr.status<200||xhr.status>=300)return;
            try{
                var d=JSON.parse(xhr.responseText);
                hud.cpu=clamp(d.cpu); hud.ram=clamp(d.ram);
                hud.ramUsed=Math.max(0,Number(d.ram_used)||0); hud.battery=clamp(d.battery);
                hud.cpuTemp=(d.cpu_temp===null || d.cpu_temp===undefined) ? -1 : Number(d.cpu_temp);
                hud.power=String(d.power||"Unknown");
                var incoming=Array.isArray(d.history)?d.history:[];
                var lastOld=hud.history.length?Number(hud.history[hud.history.length-1]):-1;
                var lastNew=incoming.length?Number(incoming[incoming.length-1]):-1;
                if(incoming.length!==hud.history.length||Math.abs(lastOld-lastNew)>.001)hud.history=incoming.slice();
                applyTheme(d.theme); hud.connected=true;
            }catch(e){ console.log("AetherWall telemetry parse error:",e); }
        };
        xhr.send();
    }

    Behavior on panelColor { ColorAnimation { duration: 650; easing.type: Easing.InOutCubic } }
    Behavior on textColor { ColorAnimation { duration: 650; easing.type: Easing.InOutCubic } }
    Behavior on mutedColor { ColorAnimation { duration: 650; easing.type: Easing.InOutCubic } }
    Behavior on accentColor { ColorAnimation { duration: 650; easing.type: Easing.InOutCubic } }
    Behavior on accent2Color { ColorAnimation { duration: 650; easing.type: Easing.InOutCubic } }
    Behavior on accent3Color { ColorAnimation { duration: 650; easing.type: Easing.InOutCubic } }

    // Reference geometry is 1600×900, matching the intended desktop composition.
    BubbleGlass { visible:hud.showTitle; x:X(42); y:Y(38); width:508*s; height:80*s; radius:22*s; sourceItem:hud.backgroundItem; sourceRect:Qt.rect(X(42),Y(38),508*s,80*s); blurEnabled:hud.blurEnabled&&hud.showTitle; blurStrength:hud.blurStrength/100; panelColor:themeValue("brand","panel",hud.panelColor); edgeColor:themeValue("brand","edge",hud.edgeColor); accent:themeValue("brand","accent",hud.accentColor); shadowColor:themeValue("brand","shadow",hud.shadowColor) }
    Text { visible:hud.showTitle; x:X(68); y:Y(51); text:"AETHERWALL"; color:themeValue("brand","text",hud.textColor); font.pixelSize:29*s; font.bold:true }
    Text { visible:hud.showTitle; x:X(68); y:Y(91); text:"REACTIVE SYSTEM HUB"; color:themeValue("brand","accent2",hud.accent2Color); font.pixelSize:15*s; font.bold:true }

    BubbleGlass { visible:hud.showClock; x:X(1200); y:Y(58); width:330*s; height:147*s; radius:22*s; sourceItem:hud.backgroundItem; sourceRect:Qt.rect(X(1200),Y(58),330*s,147*s); blurEnabled:hud.blurEnabled&&hud.showClock; blurStrength:hud.blurStrength/100; panelColor:themeValue("clock","panel",hud.panelColor); edgeColor:themeValue("clock","edge",hud.edgeColor); accent:themeValue("clock","accent",hud.accentColor); shadowColor:themeValue("clock","shadow",hud.shadowColor) }
    Text { visible:hud.showClock; x:X(1200); y:Y(68); width:330*s; horizontalAlignment:Text.AlignHCenter; text:clockText; color:themeValue("clock","text",hud.textColor); font.pixelSize:40*s; font.bold:true }
    Text { visible:hud.showClock; x:X(1200); y:Y(132); width:330*s; horizontalAlignment:Text.AlignHCenter; text:dayText; color:themeValue("clock","muted",hud.mutedColor); font.pixelSize:16*s }
    Text { visible:hud.showClock; x:X(1200); y:Y(166); width:330*s; horizontalAlignment:Text.AlignHCenter; text:dateText; color:themeValue("clock","muted",hud.mutedColor); font.pixelSize:15*s }

    // Three aligned circular meters, with consistent 245px geometry.
    Gauge { visible:hud.showMeters; x:X(58); y:Y(190); width:245*s; height:245*s; value:hud.cpu; label:"CPU"; subtext:"Live usage"; accent:themeValue("left","accent",hud.accentColor); panelColor:themeValue("left","panel",hud.panelColor); textColor:themeValue("left","text",hud.textColor); mutedColor:themeValue("left","muted",hud.mutedColor); trackColor:themeValue("left","track",hud.trackColor); edgeColor:themeValue("left","edge",hud.edgeColor); shadowColor:themeValue("left","shadow",hud.shadowColor) }
    Gauge { visible:hud.showMeters; x:X(58); y:Y(420); width:245*s; height:245*s; value:hud.ram; label:"RAM"; subtext:hud.ramUsed.toFixed(1)+" GB used"; accent:themeValue("left","accent2",hud.accent2Color); panelColor:themeValue("left","panel",hud.panelColor); textColor:themeValue("left","text",hud.textColor); mutedColor:themeValue("left","muted",hud.mutedColor); trackColor:themeValue("left","track",hud.trackColor); edgeColor:themeValue("left","edge",hud.edgeColor); shadowColor:themeValue("left","shadow",hud.shadowColor) }
    Gauge { visible:hud.showMeters; x:X(58); y:Y(650); width:245*s; height:245*s; value:hud.battery; label:"BATTERY"; subtext:hud.power; accent:themeValue("left","accent3",hud.accent3Color); panelColor:themeValue("left","panel",hud.panelColor); textColor:themeValue("left","text",hud.textColor); mutedColor:themeValue("left","muted",hud.mutedColor); trackColor:themeValue("left","track",hud.trackColor); edgeColor:themeValue("left","edge",hud.edgeColor); shadowColor:themeValue("left","shadow",hud.shadowColor) }

    BubbleGlass { visible:hud.showSystem; x:X(1190); y:Y(250); width:340*s; height:305*s; radius:22*s; sourceItem:hud.backgroundItem; sourceRect:Qt.rect(X(1190),Y(250),340*s,305*s); blurEnabled:hud.blurEnabled&&hud.showSystem; blurStrength:hud.blurStrength/100; panelColor:themeValue("system","panel",hud.panelColor); edgeColor:themeValue("system","edge",hud.edgeColor); accent:themeValue("system","accent",hud.accentColor); shadowColor:themeValue("system","shadow",hud.shadowColor) }
    Text { visible:hud.showSystem; x:X(1220); y:Y(282); text:"SYSTEM"; color:themeValue("system","text",hud.textColor); font.pixelSize:20*s; font.bold:true }

    function rowY(i) { return 326 + i*49; }
    // System bars: CPU, RAM, CPU average temperature and battery.
    Text { visible:hud.showSystem; x:X(1220); y:Y(326); text:"CPU"; color:themeValue("system","muted",hud.mutedColor); font.pixelSize:16*s }
    Text { visible:hud.showSystem; x:X(1420); y:Y(326); width:70*s; horizontalAlignment:Text.AlignRight; text:hud.cpu.toFixed(1)+"%"; color:themeValue("system","text",hud.textColor); font.pixelSize:16*s; font.bold:true }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(353); width:170*s; height:7*s; radius:4*s; color:themeValue("system","track",hud.trackColor) }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(353); width:170*s*clamp(hud.cpu)/100; height:7*s; radius:4*s; color:themeValue("system","accent",hud.accentColor); Behavior on width{NumberAnimation{duration:220;easing.type:Easing.OutCubic}} }

    Text { visible:hud.showSystem; x:X(1220); y:Y(375); text:"RAM"; color:themeValue("system","muted",hud.mutedColor); font.pixelSize:16*s }
    Text { visible:hud.showSystem; x:X(1420); y:Y(375); width:70*s; horizontalAlignment:Text.AlignRight; text:hud.ram.toFixed(1)+"%"; color:themeValue("system","text",hud.textColor); font.pixelSize:16*s; font.bold:true }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(402); width:170*s; height:7*s; radius:4*s; color:themeValue("system","track",hud.trackColor) }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(402); width:170*s*clamp(hud.ram)/100; height:7*s; radius:4*s; color:themeValue("system","accent2",hud.accent2Color); Behavior on width{NumberAnimation{duration:220;easing.type:Easing.OutCubic}} }

    Text { visible:hud.showSystem; x:X(1220); y:Y(424); text:"CPU AVG TEMP"; color:themeValue("system","muted",hud.mutedColor); font.pixelSize:16*s }
    Text { visible:hud.showSystem; x:X(1400); y:Y(424); width:90*s; horizontalAlignment:Text.AlignRight; text:hud.cpuTemp<0 ? "N/A" : hud.cpuTemp.toFixed(1)+"°C"; color:themeValue("system","text",hud.textColor); font.pixelSize:16*s; font.bold:true }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(451); width:170*s; height:7*s; radius:4*s; color:themeValue("system","track",hud.trackColor) }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(451); width:170*s*tempPercent()/100; height:7*s; radius:4*s; color:themeValue("system","accent",hud.accentColor); Behavior on width{NumberAnimation{duration:240;easing.type:Easing.OutCubic}} }

    Text { visible:hud.showSystem; x:X(1220); y:Y(473); text:"BATTERY"; color:themeValue("system","muted",hud.mutedColor); font.pixelSize:16*s }
    Text { visible:hud.showSystem; x:X(1420); y:Y(473); width:70*s; horizontalAlignment:Text.AlignRight; text:hud.battery.toFixed(1)+"%"; color:themeValue("system","text",hud.textColor); font.pixelSize:16*s; font.bold:true }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(500); width:170*s; height:7*s; radius:4*s; color:themeValue("system","track",hud.trackColor) }
    Rectangle { visible:hud.showSystem; x:X(1320); y:Y(500); width:170*s*clamp(hud.battery)/100; height:7*s; radius:4*s; color:themeValue("system","accent3",hud.accent3Color); Behavior on width{NumberAnimation{duration:220;easing.type:Easing.OutCubic}} }
    Text { visible:hud.showSystem; x:X(1220); y:Y(526); text:"POWER"; color:themeValue("system","muted",hud.mutedColor); font.pixelSize:16*s }
    Text { visible:hud.showSystem; x:X(1320); y:Y(526); width:170*s; horizontalAlignment:Text.AlignRight; text:hud.power; color:themeValue("system","text",hud.textColor); font.pixelSize:16*s; font.bold:true }

    BubbleGlass { visible:hud.showHistory; x:X(770); y:Y(585); width:380*s; height:265*s; radius:22*s; sourceItem:hud.backgroundItem; sourceRect:Qt.rect(X(770),Y(585),380*s,265*s); blurEnabled:hud.blurEnabled&&hud.showHistory; blurStrength:hud.blurStrength/100; panelColor:themeValue("graph","panel",hud.panelColor); edgeColor:themeValue("graph","edge",hud.edgeColor); accent:themeValue("graph","accent",hud.accentColor); shadowColor:themeValue("graph","shadow",hud.shadowColor) }
    Text { visible:hud.showHistory; x:X(800); y:Y(615); text:"CPU HISTORY"; color:themeValue("graph","text",hud.textColor); font.pixelSize:18*s; font.bold:true }
    Canvas { visible:hud.showHistory; id:graph; x:X(800); y:Y(660); width:320*s; height:145*s; antialiasing:true; renderTarget:Canvas.FramebufferObject
        onPaint:{var c=getContext("2d");c.reset();c.strokeStyle=String(themeValue("graph","grid",hud.gridColor));c.lineWidth=1;for(var i=0;i<6;++i){var yy=i*(height/5);c.beginPath();c.moveTo(0,yy);c.lineTo(width,yy);c.stroke();}var h=hud.history;if(!h||h.length<2)return;c.strokeStyle=String(themeValue("graph","accent",hud.accentColor));c.lineWidth=Math.max(2,3*s);c.lineJoin="round";c.lineCap="round";c.beginPath();for(var j=0;j<h.length;++j){var xx=j*(width/(h.length-1));var value=clamp(h[j]);var yy=height-(value/100)*height;if(j===0)c.moveTo(xx,yy);else c.lineTo(xx,yy);}c.stroke();}
        Connections { target:hud; function onHistoryChanged(){graph.requestPaint()} function onZoneThemesChanged(){graph.requestPaint()} function onGridColorChanged(){graph.requestPaint()} function onAccentColorChanged(){graph.requestPaint()} }
    }
    Text { visible:hud.showHistory; x:X(800); y:Y(825); text:"60 SECS"; color:themeValue("graph","muted",hud.mutedColor); font.pixelSize:12*s }

    BubbleGlass { visible:hud.showDock; x:X(285); y:Y(848); width:830*s; height:38*s; radius:14*s; sourceItem:hud.backgroundItem; sourceRect:Qt.rect(X(285),Y(848),830*s,38*s); blurEnabled:hud.blurEnabled; blurStrength:hud.blurStrength/100; panelColor:themeValue("brand","panel",hud.panelColor); edgeColor:themeValue("brand","edge",hud.edgeColor); accent:themeValue("brand","accent",hud.accentColor); shadowColor:themeValue("brand","shadow",hud.shadowColor) }
    Text { visible:hud.showDock; x:X(300); y:Y(856); width:800*s; text:"◉    ◉    ◉    ◉    ◉    ◉    ◉    ◉    ◉    ◉"; horizontalAlignment:Text.AlignHCenter; color:themeValue("brand","accent2",hud.accent2Color); font.pixelSize:17*s }

    property string clockText:""
    property string dayText:""
    property string dateText:""
    Timer { interval:1000; repeat:true; running:true; triggeredOnStart:true; onTriggered:{var d=new Date();function pad(n){return(n<10?"0":"")+n;}hud.clockText=pad(d.getHours())+":"+pad(d.getMinutes())+":"+pad(d.getSeconds());var days=["SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"];hud.dayText=days[d.getDay()];hud.dateText=pad(d.getDate())+" "+["January","February","March","April","May","June","July","August","September","October","November","December"][d.getMonth()]+" "+d.getFullYear();} }
    Timer { interval:250; repeat:true; running:hud.telemetryUrl!==""; triggeredOnStart:true; onTriggered:hud.pollTelemetry() }
}

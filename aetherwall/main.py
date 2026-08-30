from pathlib import Path
import os, sys, time, shutil, subprocess, hashlib
import psutil
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QComboBox, QLineEdit,
    QFileDialog, QMessageBox, QStackedWidget, QProgressBar, QFrame,
    QAbstractItemView, QSlider, QSizePolicy, QCheckBox, QGroupBox
)
from .config import load, save, TELEMETRY, TELEMETRY_URL
from .telemetry import sample
from .plasma import apply

VIDEO={'.mp4','.mkv','.webm','.mov','.avi','.m4v'}
IMAGE={'.png','.jpg','.jpeg','.webp','.bmp','.gif'}
ROOTS=[Path.home()/'Pictures'/'AetherWall',Path.home()/'Pictures'/'Wallpapers',Path.home()/'Pictures',Path('/mnt/data/Live-wallpaper'),Path('/mnt/data/Live-wallpaper/Live-wallpaper-hd')]
APP_ROOT=Path(__file__).resolve().parent.parent
ICON=APP_ROOT/'assets'/'aetherwall.png'

STYLE='''
QMainWindow,QWidget{background:#070b18;color:#e8edf8;font-family:Inter,DejaVu Sans;}
QFrame#navPanel{background:#070b18;border:0;}
QPushButton{background:#0d1930;border:1px solid #30486f;border-radius:9px;padding:9px 13px;color:#e8edf8;}
QPushButton:hover{background:#172a4b;border-color:#7d9fe0;}
QPushButton:pressed,QPushButton:checked{background:#5d2bc2;border:1px solid #b78cff;}
QComboBox,QLineEdit{background:#0d1930;border:1px solid #30486f;border-radius:8px;padding:8px;color:#e8edf8;}
QListWidget{background:#060b17;border:1px solid #263a5d;border-radius:10px;outline:none;}
QListWidget::item{padding:4px;border-radius:7px;}
QListWidget::item:hover{background:#10203b;}
QListWidget::item:selected{background:#263e6c;border:1px solid #8faeff;}
QProgressBar{background:#111a2e;border:1px solid #2a3e63;border-radius:7px;text-align:center;}
QProgressBar::chunk{background:#7d4cff;border-radius:6px;}
QFrame#card,QGroupBox#card{background:#0a1120;border:1px solid #2b3e60;border-radius:14px;}
QLabel#title{font-size:30px;font-weight:700;}
QLabel#subtitle{color:#8e9bb4;font-size:14px;}
QLabel#section{font-size:17px;font-weight:700;}
QSlider::groove:horizontal{height:5px;background:#1c2942;border-radius:3px;}
QSlider::handle:horizontal{width:14px;margin:-5px 0;background:#9b55ff;border-radius:7px;}
QCheckBox{spacing:8px;padding:5px;border-radius:6px;}
QCheckBox:hover{background:#101c31;}
'''

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AetherWall v4.0')
        self.setWindowIcon(QIcon(str(ICON)) if ICON.exists() else QIcon())
        self.resize(1536,900); self.setMinimumSize(1120,700)
        self.cfg=load(); self.selected=''; self.favorite_selected=''
        self.thumbdir=Path.home()/'.cache/aetherwall/thumbnails'; self.thumbdir.mkdir(parents=True,exist_ok=True)
        self.setStyleSheet(STYLE)

        root=QWidget(); self.setCentralWidget(root)
        main=QHBoxLayout(root); main.setContentsMargins(8,8,8,8); main.setSpacing(10)
        nav_panel=QFrame(); nav_panel.setObjectName('navPanel'); nav_panel.setFixedWidth(154); main.addWidget(nav_panel)
        nav=QVBoxLayout(nav_panel); nav.setContentsMargins(2,2,2,2); nav.setSpacing(7)
        self.stack=QStackedWidget(); main.addWidget(self.stack,1); self.nav=[]
        for text,idx in [('⌂  Library',0),('★  Favorites',1),('✦  Reactive',2),('◇  Performance',3),('⚙  Setup',4),('▣  Diagnostics',5)]:
            b=QPushButton(text); b.setCheckable(True); b.clicked.connect(lambda _,i=idx,btn=b:self.navigate(i,btn)); nav.addWidget(b); self.nav.append(b)
        nav.addStretch(); self.navstatus=QLabel('●  Ready'); nav.addWidget(self.navstatus); self.count=QLabel(); nav.addWidget(self.count)

        self.library(); self.favorites(); self.reactive(); self.performance(); self.setup(); self.diagnostics()
        self.navigate(0,self.nav[0]); self.rescan()
        self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(self.refresh_interval_ms())
        self.ensure_telemetry_service(); self.telemetry_status=self.telemetry_service_status(); self.tick()

    def navigate(self,i,b):
        self.stack.setCurrentIndex(i)
        for x in self.nav: x.setChecked(x is b)
        self.set_status(b.text().strip()+' opened')
    def set_status(self,t): self.navstatus.setText('●  '+t)
    def page(self,title,sub=''):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(16,12,16,12); l.setSpacing(8)
        h=QLabel(title); h.setObjectName('title'); l.addWidget(h)
        if sub: s=QLabel(sub); s.setObjectName('subtitle'); s.setWordWrap(True); l.addWidget(s)
        return w,l
    def card(self):
        c=QFrame(); c.setObjectName('card'); return c

    # ---------- Library ----------
    def library(self):
        w,l=self.page('Wallpaper Library','Browse local images and videos. Select a preview, then apply it. Filenames are intentionally hidden.')
        r=QHBoxLayout(); r.setSpacing(8)
        self.search=QLineEdit(); self.search.setPlaceholderText('Search wallpapers…'); self.search.textChanged.connect(self.filter); r.addWidget(self.search,1)
        self.fit=QComboBox(); self.fit.addItems(['Fit','Fill','Stretch']); self.fit.setCurrentText(self.cfg.get('fit','fill').title()); self.fit.currentTextChanged.connect(lambda v:self.cfg.__setitem__('fit',v.lower())); r.addWidget(self.fit)
        a=QPushButton('＋ Add Folder'); a.clicked.connect(self.add_folder); r.addWidget(a)
        z=QPushButton('↻ Rescan'); z.clicked.connect(self.rescan); r.addWidget(z)
        r.addWidget(QLabel('Rows:'))
        self.rows=QSlider(Qt.Horizontal); self.rows.setRange(1,3); self.rows.setValue(int(self.cfg.get('rows',3))); self.rows.setFixedWidth(105); self.rows.valueChanged.connect(self.change_rows); r.addWidget(self.rows)
        self.rows_label=QLabel(str(self.rows.value())); self.rows_label.setMinimumWidth(12); r.addWidget(self.rows_label); l.addLayout(r)

        body=QHBoxLayout(); body.setSpacing(10)
        self.list=QListWidget(); self.list.setMinimumWidth(620); self.list.setViewMode(QListWidget.IconMode); self.list.setResizeMode(QListWidget.Adjust); self.list.setMovement(QListWidget.Static); self.list.setSpacing(7); self.list.setSelectionMode(QAbstractItemView.SingleSelection); self.list.currentRowChanged.connect(self.select); body.addWidget(self.list,3)
        card=self.card(); card.setMinimumWidth(380); pv=QVBoxLayout(card); pv.setContentsMargins(8,8,8,8)
        self.preview=QLabel('Select an image or video'); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(360,360); self.preview.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); self.preview.setStyleSheet('background:#050812;border-radius:12px;color:#7e8da9;'); pv.addWidget(self.preview,1); body.addWidget(card,2); l.addLayout(body,1)
        ar=QHBoxLayout(); ar.setSpacing(8)
        ap=QPushButton('▶  Apply Wallpaper'); ap.clicked.connect(self.apply_selected); ar.addWidget(ap,1)
        self.favbtn=QPushButton('☆  Favorite'); self.favbtn.clicked.connect(self.favorite); ar.addWidget(self.favbtn)
        self.removebtn=QPushButton('▣  Remove from Library'); self.removebtn.clicked.connect(self.remove_from_library); self.removebtn.setEnabled(False); ar.addWidget(self.removebtn); l.addLayout(ar)
        self.stack.addWidget(w); self.update_library_grid()
    def change_rows(self,v): self.cfg['rows']=int(v); save(self.cfg); self.rows_label.setText(str(v)); self.update_library_grid()
    def update_library_grid(self):
        if not hasattr(self,'list'): return
        rows=max(1,min(3,int(self.rows.value())))
        sizes={1:(360,214,370,224),2:(280,166,290,176),3:(218,130,228,140)}
        iw,ih,gw,gh=sizes[rows]; self.list.setIconSize(QSize(iw,ih)); self.list.setGridSize(QSize(gw,gh))
        for i in range(self.list.count()): self.list.item(i).setSizeHint(QSize(gw,gh))
    def favorites(self):
        w,l=self.page('Favorites','Saved wallpapers are shown as image/video previews.'); self.favlist=QListWidget(); self.favlist.setIconSize(QSize(240,135)); self.favlist.setViewMode(QListWidget.IconMode); self.favlist.setResizeMode(QListWidget.Adjust); self.favlist.setMovement(QListWidget.Static); self.favlist.setSpacing(8); self.favlist.setGridSize(QSize(258,153)); self.favlist.currentRowChanged.connect(self.select_favorite); l.addWidget(self.favlist,1)
        r=QHBoxLayout(); a=QPushButton('▶  Apply Selected'); a.clicked.connect(self.apply_favorite); r.addWidget(a); b=QPushButton('☆  Remove Favorite'); b.clicked.connect(self.remove_favorite); r.addWidget(b); c=QPushButton('↻  Refresh'); c.clicked.connect(self.refresh_favorites); r.addWidget(c); l.addLayout(r); self.stack.addWidget(w)

    def thumb(self,path):
        cache_key='v40-'+path; out=self.thumbdir/(hashlib.sha1(cache_key.encode()).hexdigest()+'.jpg')
        if out.exists(): return str(out)
        try:
            suffix=Path(path).suffix.lower()
            if suffix in IMAGE:
                q=QPixmap(path)
                if not q.isNull(): q.scaled(800,450,Qt.KeepAspectRatio,Qt.SmoothTransformation).save(str(out),'JPG',90)
            elif suffix in VIDEO and shutil.which('ffmpeg'):
                cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-ss','00:00:00.8','-i',path,'-frames:v','1','-vf','scale=800:450:force_original_aspect_ratio=decrease,pad=800:450:(ow-iw)/2:(oh-ih)/2:color=black',str(out)]
                subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20,check=False)
        except Exception: pass
        return str(out) if out.exists() else ''
    def _add_preview_item(self,widget,path):
        t=self.thumb(path); item=QListWidgetItem(QIcon(t) if t else QIcon(),''); item.setData(Qt.UserRole,path); item.setToolTip('Video' if Path(path).suffix.lower() in VIDEO else 'Image'); widget.addItem(item)
    def all_roots(self): return ROOTS+[Path(x) for x in self.cfg.get('extra_roots',[])]
    def files(self):
        excluded={str(Path(x).expanduser().resolve()) for x in self.cfg.get('excluded',[])}; out=[]
        for root in self.all_roots():
            if root.exists():
                try:
                    for p in root.rglob('*'):
                        if p.is_file() and p.suffix.lower() in VIDEO|IMAGE:
                            try:key=str(p.resolve())
                            except OSError:key=str(p)
                            if key not in excluded:out.append(key)
                except (PermissionError,OSError):pass
        return sorted(set(out),key=str.lower)
    def rescan(self):
        self.cfg['library']=self.files(); save(self.cfg); self.list.clear()
        for p in self.cfg['library']: self._add_preview_item(self.list,p)
        self.count.setText(f'{len(self.cfg["library"])} wallpapers'); self.filter(); self.refresh_favorites(); self.update_library_grid(); self.set_status(f'Library scanned — {len(self.cfg["library"])} wallpapers')
    def filter(self):
        q=self.search.text().lower()
        for i in range(self.list.count()):
            item=self.list.item(i); path=str(item.data(Qt.UserRole) or ''); item.setHidden(bool(q and q not in Path(path).name.lower()))
    def select(self,row):
        if 0<=row<len(self.cfg['library']):
            self.selected=self.cfg['library'][row]; t=self.thumb(self.selected)
            if t:
                self.preview.setPixmap(QPixmap(t).scaled(self.preview.size()-QSize(16,16),Qt.KeepAspectRatio,Qt.SmoothTransformation)); self.preview.setText('')
            else:self.preview.setPixmap(QPixmap()); self.preview.setText('▶  VIDEO PREVIEW\n\nPreview frame unavailable.\nInstall FFmpeg and press Rescan.')
            self.favbtn.setText('★  Remove Favorite' if self.selected in self.cfg.get('favorites',[]) else '☆  Favorite'); self.removebtn.setEnabled(True); self.set_status('Wallpaper preview selected')
    def add_folder(self):
        d=QFileDialog.getExistingDirectory(self,'Add wallpaper folder')
        if d:
            self.cfg.setdefault('extra_roots',[])
            if d not in self.cfg['extra_roots']: self.cfg['extra_roots'].append(d)
            save(self.cfg); self.rescan(); self.set_status('Folder added')
    def favorite(self):
        if not self.selected:return self.set_status('Select a wallpaper first')
        f=set(self.cfg.get('favorites',[]));
        if self.selected in f:f.remove(self.selected); self.set_status('Removed from Favorites')
        else:f.add(self.selected); self.set_status('Added to Favorites')
        self.cfg['favorites']=sorted(f); save(self.cfg); self.refresh_favorites(); self.favbtn.setText('★  Remove Favorite' if self.selected in f else '☆  Favorite')
    def refresh_favorites(self):
        if not hasattr(self,'favlist'):return
        self.favlist.clear(); valid=[]
        for p in self.cfg.get('favorites',[]):
            if Path(p).exists():valid.append(p); self._add_preview_item(self.favlist,p)
        self.cfg['favorites']=valid; save(self.cfg)
    def select_favorite(self,row):
        f=self.cfg.get('favorites',[])
        if 0<=row<len(f):self.favorite_selected=f[row]; self.set_status('Favorite preview selected')
    def remove_favorite(self):
        if not self.favorite_selected:return self.set_status('Select a favorite first')
        self.cfg['favorites']=[p for p in self.cfg.get('favorites',[]) if p!=self.favorite_selected]; self.favorite_selected=''; save(self.cfg); self.refresh_favorites(); self.set_status('Removed from Favorites')
    def apply_favorite(self):
        if self.favorite_selected:self.selected=self.favorite_selected; self.apply_selected()
        else:self.set_status('Select a favorite first')
    def remove_from_library(self):
        if not self.selected:return
        ans=QMessageBox.question(self,'Remove from Library','Remove this wallpaper from AetherWall\'s library?\n\nThe original file will NOT be deleted.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if ans!=QMessageBox.Yes:return
        self.cfg.setdefault('excluded',[]); self.cfg['excluded'].append(self.selected) if self.selected not in self.cfg['excluded'] else None
        self.cfg['library']=[p for p in self.cfg.get('library',[]) if p!=self.selected]; self.cfg['favorites']=[p for p in self.cfg.get('favorites',[]) if p!=self.selected]; self.selected=''; save(self.cfg); self.rescan(); self.preview.clear(); self.preview.setText('Select an image or video'); self.removebtn.setEnabled(False); self.set_status('Wallpaper removed from library')
    def restore_removed(self):self.cfg['excluded']=[]; save(self.cfg); self.rescan(); self.set_status('Removed wallpapers restored')

    # ---------- Reactive ----------
    def reactive(self):
        w,l=self.page('Reactive System Hub','Native Plasma wallpaper with a persistent adaptive bubble-glass HUD. Configure visibility, blur and the live desktop preview.')
        split=QHBoxLayout(); split.setSpacing(10)
        settings=self.card(); settings.setMinimumWidth(390); sl=QVBoxLayout(settings); sl.setContentsMargins(12,12,12,12); sl.setSpacing(7)
        self.stats=QLabel(); self.stats.setStyleSheet('font-size:17px;font-weight:700;'); sl.addWidget(self.stats)
        self.bar=QProgressBar(); sl.addWidget(self.bar)
        self.reactivebtn=QPushButton(); self.reactivebtn.setCheckable(True); self.reactivebtn.clicked.connect(self.toggle_reactive); sl.addWidget(self.reactivebtn)
        self.blurbtn=QPushButton(); self.blurbtn.setCheckable(True); self.blurbtn.clicked.connect(self.toggle_blur); sl.addWidget(self.blurbtn)
        br=QHBoxLayout(); br.addWidget(QLabel('Blur Intensity')); self.blurslider=QSlider(Qt.Horizontal); self.blurslider.setRange(0,100); self.blurslider.setValue(int(self.cfg.get('blur_strength',65))); self.blurslider.valueChanged.connect(self.change_blur); br.addWidget(self.blurslider,1); self.blurlabel=QLabel(f'{self.blurslider.value()}%'); br.addWidget(self.blurlabel); sl.addLayout(br)
        hudbox=QGroupBox('HUD Customization'); hudbox.setObjectName('card'); hl=QVBoxLayout(hudbox); hl.setContentsMargins(10,10,10,10)
        self.hud_checks=[]
        entries=[('show_title','Top Title (AetherWall)'),('show_clock','Clock & Date'),('show_system','System Panel (CPU / RAM / Battery / Power)'),('show_meters','Circular Meters (Left)'),('show_history','CPU History Graph'),('show_dock','Bottom Dock')]
        for key,text in entries:
            c=QCheckBox(text); c.setChecked(bool(self.cfg.get(key,True))); c.toggled.connect(lambda v,k=key:self.set_hud_option(k,v)); hl.addWidget(c); self.hud_checks.append(c)
        sl.addWidget(hudbox,1)
        ap=QPushButton('⚡  Apply Selected Wallpaper + HUD'); ap.clicked.connect(self.apply_selected); sl.addWidget(ap)
        split.addWidget(settings,0)

        preview=self.card(); pl=QVBoxLayout(preview); pl.setContentsMargins(12,12,12,12); ph=QHBoxLayout(); title=QLabel('HUD PREVIEW'); title.setStyleSheet('font-size:18px;font-weight:700;'); ph.addWidget(title); ph.addStretch(); self.preview_temp=QLabel('CPU AVG TEMP —'); ph.addWidget(self.preview_temp); pl.addLayout(ph)
        surface=QFrame(); surface.setStyleSheet('background:#030713;border:1px solid #263858;border-radius:16px;'); gl=QGridLayout(surface); gl.setContentsMargins(18,18,18,18); gl.setHorizontalSpacing(14); gl.setVerticalSpacing(14)
        self.p_brand=QLabel('AETHERWALL\nREACTIVE SYSTEM HUB'); self.p_brand.setStyleSheet('background:#0c1322;border:1px solid #8c56ff;border-radius:18px;padding:12px;font-size:17px;font-weight:700;'); gl.addWidget(self.p_brand,0,0,1,2)
        self.p_clock=QLabel('00:00:00\nSUNDAY\n30 August 2026'); self.p_clock.setAlignment(Qt.AlignCenter); self.p_clock.setStyleSheet('background:#0c1322;border:1px solid #5b74a8;border-radius:18px;padding:10px;font-size:17px;font-weight:700;'); gl.addWidget(self.p_clock,0,2,1,1)
        self.p_meters=[]
        for i,(label,color) in enumerate([('CPU','purple'),('RAM','cyan'),('BATTERY','green')]):
            q=QLabel(label+'\n—'); q.setAlignment(Qt.AlignCenter); q.setMinimumHeight(112); q.setStyleSheet('background:#0b1220;border:2px solid #52627d;border-radius:70px;padding:10px;font-size:18px;font-weight:700;'); gl.addWidget(q,i+1,0); self.p_meters.append(q)
        self.p_system=QLabel('SYSTEM\nCPU   —\nRAM   —\nCPU AVG TEMP   —\nBATTERY   —\nPOWER   —'); self.p_system.setStyleSheet('background:#0c1322;border:1px solid #617293;border-radius:18px;padding:14px;font-size:15px;'); gl.addWidget(self.p_system,1,1,2,2)
        self.p_graph=QLabel('CPU HISTORY\n\n╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲'); self.p_graph.setStyleSheet('background:#0b1220;border:1px solid #8c56ff;border-radius:18px;padding:12px;font-size:15px;'); gl.addWidget(self.p_graph,3,1,1,2)
        self.p_dock=QLabel('◉  ◉  ◉  ◉  ◉  ◉  ◉  ◉  ◉  ◉'); self.p_dock.setAlignment(Qt.AlignCenter); self.p_dock.setStyleSheet('background:#0c1322;border:1px solid #4e6388;border-radius:14px;padding:9px;'); gl.addWidget(self.p_dock,4,0,1,3)
        pl.addWidget(surface,1); split.addWidget(preview,1); l.addLayout(split,1); self.stack.addWidget(w); self.update_reactive_button(); self.update_blur_button()
    def set_hud_option(self,key,value):self.cfg[key]=bool(value); save(self.cfg)
    def toggle_blur(self):self.cfg['blur_enabled']=self.blurbtn.isChecked(); save(self.cfg); self.update_blur_button(); self.apply_selected(silent=True) if self.selected else None
    def change_blur(self,value):self.cfg['blur_strength']=int(value); save(self.cfg); self.blurlabel.setText(f'{value}%')
    def update_blur_button(self):
        if hasattr(self,'blurbtn'):
            on=bool(self.cfg.get('blur_enabled',True)); self.blurbtn.setChecked(on); self.blurbtn.setText('Background Blur: ON' if on else 'Background Blur: OFF')

    # ---------- Other pages ----------
    def performance(self):
        w,l=self.page('Performance','Configure the telemetry refresh rate and desktop update cadence.'); self.perf=QComboBox(); self.perf.addItems(['15 FPS','30 FPS','60 FPS','120 FPS','Adaptive']); saved_fps=self.cfg.get('fps',30); self.perf.setCurrentText('Adaptive' if saved_fps=='adaptive' else f'{saved_fps} FPS'); l.addWidget(self.perf); b=QPushButton('✓  Save Performance Settings'); b.clicked.connect(self.save_performance); l.addWidget(b); self.perfinfo=QLabel(); self.perfinfo.setObjectName('subtitle'); l.addWidget(self.perfinfo); l.addStretch(); self.stack.addWidget(w)
    def setup(self):
        w,l=self.page('Setup & Backends','Native KDE Plasma 6 wallpaper plugins, bubble-glass HUD and optional AetherWall widget integration.')
        card=self.card(); cl=QVBoxLayout(card); cl.setContentsMargins(14,14,14,14)
        for x in ['Image plugin: org.aetherwall.wallpaper','Video plugin: org.aetherwall.video','Widget: org.aetherwall.widget','Backend: KDE Plasma 6 / KWin Wayland','Composition: background media → adaptive bubble-glass HUD','CPU average temperature: psutil hardware sensors','Audio: muted by default','Adaptive HUD contrast: PER REGION','Wallpaper scripts are never executed']: cl.addWidget(QLabel(x))
        l.addWidget(card); self.pluginstatus=QLabel(); l.addWidget(self.pluginstatus)
        b=QPushButton('↻  Refresh Plasma Plugin Cache'); b.clicked.connect(self.refresh_plugin); l.addWidget(b)
        wb=QPushButton('▣  Install / Refresh AetherWall Widget'); wb.clicked.connect(self.install_widget); l.addWidget(wb)
        restore=QPushButton('↺  Restore Removed Wallpapers'); restore.clicked.connect(self.restore_removed); l.addWidget(restore); l.addStretch(); self.stack.addWidget(w)
    def diagnostics(self):
        w,l=self.page('Diagnostics','Live runtime, hardware temperature and wallpaper-engine status.'); self.diag=QLabel(); self.diag.setWordWrap(True); self.diag.setStyleSheet('font-family:monospace;background:#0b1222;border:1px solid #263957;border-radius:12px;padding:18px;'); l.addWidget(self.diag,1); b=QPushButton('⟳  Refresh Diagnostics'); b.clicked.connect(self.tick); l.addWidget(b); self.stack.addWidget(w)

    def apply_selected(self,silent=False):
        if not self.selected:
            if not silent: QMessageBox.information(self,'AetherWall','Select an image or video first.')
            self.set_status('Nothing selected'); return
        try:
            self.cfg['fit']=self.fit.currentText().lower(); self.cfg['wallpaper']=self.selected; save(self.cfg); result=apply(self.selected,self.cfg); self.set_status('Wallpaper + HUD applied')
            if not silent: QMessageBox.information(self,'AetherWall',result)
        except Exception as e:self.set_status('Apply failed'); QMessageBox.critical(self,'AetherWall — Apply failed',str(e))
    def update_reactive_button(self):
        if hasattr(self,'reactivebtn'):
            on=bool(self.cfg.get('reactive',True)); self.reactivebtn.setChecked(on); self.reactivebtn.setText('Reactive HUD: ON' if on else 'Reactive HUD: OFF')
    def toggle_reactive(self):
        self.cfg['reactive']=self.reactivebtn.isChecked(); save(self.cfg); self.update_reactive_button(); self.set_status('Reactive HUD '+('enabled' if self.cfg['reactive'] else 'disabled')); self.apply_selected(silent=True) if self.selected else None
    def save_performance(self):
        v=self.perf.currentText(); self.cfg['fps']='adaptive' if v=='Adaptive' else int(v.split()[0]); save(self.cfg); self.restart_refresh_timer(); self.set_status('Performance saved: '+v); self.perfinfo.setText('Saved. HUD refresh target: '+v+'.')
    def refresh_plugin(self):
        if shutil.which('kbuildsycoca6'): subprocess.run(['kbuildsycoca6'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.set_status('Plasma plugin cache refreshed'); self.pluginstatus.setText('Image plugin: '+('FOUND' if (Path.home()/'.local/share/plasma/wallpapers/org.aetherwall.wallpaper').exists() else 'MISSING')+'\nVideo plugin: '+('FOUND' if (Path.home()/'.local/share/plasma/wallpapers/org.aetherwall.video').exists() else 'MISSING')+'\nWidget: '+('FOUND' if (Path.home()/'.local/share/plasma/plasmoids/org.aetherwall.widget').exists() else 'MISSING'))
    def install_widget(self):
        tool=shutil.which('kpackagetool6')
        src=APP_ROOT/'plasma'/'org.aetherwall.widget'
        if not tool or not src.exists(): return self.set_status('kpackagetool6 or widget package missing')
        subprocess.run([tool,'--type','Plasma/Applet','--upgrade',str(src)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.refresh_plugin(); self.set_status('AetherWall widget installed/refreshed')
    def ensure_telemetry_service(self):
        if shutil.which('systemctl'):
            try:subprocess.run(['systemctl','--user','start','aetherwall-telemetry.service'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
            except Exception:pass
    def telemetry_service_status(self):
        if not shutil.which('systemctl'):return 'unavailable'
        try:p=subprocess.run(['systemctl','--user','is-active','aetherwall-telemetry.service'],capture_output=True,text=True,timeout=3); return p.stdout.strip() or 'inactive'
        except Exception:return 'unknown'
    def refresh_interval_ms(self):
        fps=self.cfg.get('fps',30)
        if fps=='adaptive':return 200
        try:return max(250,int(1000/max(1,int(fps))))
        except (TypeError,ValueError):return 200
    def restart_refresh_timer(self):
        if hasattr(self,'timer'):self.timer.setInterval(self.refresh_interval_ms())
    def tick(self):
        metrics=sample(); cpu=metrics['cpu']; ram=metrics['ram']; bp=metrics['battery']; temp=metrics.get('cpu_temp')
        temp_text='N/A' if temp is None else f'{temp:.1f}°C'
        self.stats.setText(f'CPU {cpu:.1f}%   •   RAM {ram:.1f}%   •   Battery {bp:.1f}%   •   CPU Avg Temp {temp_text}   •   {time.strftime("%H:%M:%S")}'); self.bar.setValue(round(cpu)); self.update_reactive_button()
        if hasattr(self,'preview_temp'):
            self.preview_temp.setText('CPU AVG TEMP  '+temp_text)
            self.p_meters[0].setText(f'CPU\n{cpu:.1f}%'); self.p_meters[1].setText(f'RAM\n{ram:.1f}%'); self.p_meters[2].setText(f'BATTERY\n{bp:.1f}%')
            self.p_system.setText(f'SYSTEM\nCPU   {cpu:.1f}%\nRAM   {ram:.1f}%\nCPU AVG TEMP   {temp_text}\nBATTERY   {bp:.1f}%\nPOWER   {metrics["power"]}')
            self.p_clock.setText(time.strftime('%H:%M:%S\n%A\n%d %B %Y').upper())
        plugin=Path.home()/'.local/share/plasma/wallpapers/org.aetherwall.wallpaper'; video_plugin=Path.home()/'.local/share/plasma/wallpapers/org.aetherwall.video'; widget=Path.home()/'.local/share/plasma/plasmoids/org.aetherwall.widget'
        self.diag.setText(f'AetherWall 4.0.0\n\nWayland: {bool(os.environ.get("WAYLAND_DISPLAY"))}\nDesktop: {os.environ.get("XDG_CURRENT_DESKTOP","Unknown")}\nSession: {os.environ.get("XDG_SESSION_TYPE","Unknown")}\nImage plugin: {"FOUND" if plugin.exists() else "MISSING"}\nVideo plugin: {"FOUND" if video_plugin.exists() else "MISSING"}\nWidget: {"FOUND" if widget.exists() else "MISSING"}\nReactive HUD: {"ON" if self.cfg.get("reactive") else "OFF"}\nAdaptive contrast: PER REGION\nBubble glass: ON\nHUD blur: {"ON" if self.cfg.get("blur_enabled",True) else "OFF"} ({self.cfg.get("blur_strength",65)}%)\nCPU average temperature: {temp_text}\nHUD regions: title={self.cfg.get("show_title",True)}, clock={self.cfg.get("show_clock",True)}, system={self.cfg.get("show_system",True)}, meters={self.cfg.get("show_meters",True)}, graph={self.cfg.get("show_history",True)}, dock={self.cfg.get("show_dock",True)}\nWallpaper: {self.cfg.get("wallpaper") or "none"}\nTelemetry endpoint: {TELEMETRY_URL}\nTelemetry cache exists: {TELEMETRY.exists()}\nTelemetry service: {self.telemetry_status}\nffmpeg: {"FOUND" if shutil.which("ffmpeg") else "MISSING"}\nqdbus6: {"FOUND" if shutil.which("qdbus6") else "MISSING"}')


def main():
    app=QApplication(sys.argv); app.setApplicationName('AetherWall'); app.setApplicationDisplayName('AetherWall v4.0'); app.setWindowIcon(QIcon(str(ICON)) if ICON.exists() else QIcon()); a=App(); a.show(); return app.exec()
if __name__=='__main__':raise SystemExit(main())

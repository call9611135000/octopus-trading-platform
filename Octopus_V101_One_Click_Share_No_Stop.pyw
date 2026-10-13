import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from tkinter import colorchooser
from pathlib import Path

VERSION = 'V101'

# Windows-wide single-instance lock shared by Octopus releases V071 onward.
# Keep the mutex handle alive for the lifetime of the application.
_OCTOPUS_MUTEX_HANDLE = None

def _acquire_octopus_instance():
    global _OCTOPUS_MUTEX_HANDLE
    import os
    if os.name != 'nt':
        return True
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel32.CreateMutexW(None, False, 'Local\\Octopus_Chart_Workspace_SingleInstance')
    if not handle:
        raise OSError(ctypes.get_last_error(), 'Unable to create Octopus instance mutex')
    _OCTOPUS_MUTEX_HANDLE = handle
    if ctypes.get_last_error() != 183:  # ERROR_ALREADY_EXISTS
        return True
    # Activate an existing Octopus window rather than opening another writer.
    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        found = []
        def enum_cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            n = user32.GetWindowTextLengthW(hwnd)
            if n < 7:
                return True
            title = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, title, n + 1)
            if title.value.startswith('Octopus V'):
                found.append(hwnd)
                return False
            return True
        user32.EnumWindows(CALLBACK(enum_cb), 0)
        if found:
            user32.ShowWindow(found[0], 9)  # SW_RESTORE
            user32.SetForegroundWindow(found[0])
    except Exception:
        pass
    return False

# Self-contained Windows application icon (no external icon file required).
def _set_octopus_icon(window):
    try:
        import ctypes
        if hasattr(ctypes, 'windll'):
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Octopus.ChartWorkspace.V050')
    except Exception:
        pass
    try:
        import base64, os, tempfile
        from pathlib import Path
        icon_dir=Path(os.environ.get('LOCALAPPDATA',tempfile.gettempdir()))/'Octopus'
        icon_dir.mkdir(parents=True,exist_ok=True)
        icon_path=icon_dir/'octopus_v046.ico'
        icon_bytes=base64.b64decode(_OCTOPUS_ICON_BASE64)
        if not icon_path.exists() or icon_path.read_bytes()!=icon_bytes:
            icon_path.write_bytes(icon_bytes)
        window.iconbitmap(default=str(icon_path))
    except Exception:
        pass

_OCTOPUS_ICON_BASE64 = (
    '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'
)

BG='#151515'; BAR='#d7e0ee'; LINE='#aeb8c8'
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'Octopus {VERSION} | Chart Workspace')
        _set_octopus_icon(self)
        self.geometry('1450x850'); self.minsize(900,550)
        try:self.state('zoomed')
        except tk.TclError:pass
        self.configure(bg=BG)
        self.sheets={'Sheet 1': []}; self.active_sheet='Sheet 1'; self.active_chart=None; self.active_index=-1
        self._menu(); self._toolbar(); self._tabs(); self._status(); self._sheets(); self._chart()
        self.show_sheet('Sheet 1');self.new_chart('NIFTY')
        self.bind('<Control-n>',lambda e:self.new_chart(self.symbol.get().strip() or 'NIFTY'))
        self.bind('<Control-w>',lambda e:self.close_active())
        self.bind('<Control-s>',lambda e:self.save_workspace())
        self.bind('<Control-o>',lambda e:self.open_workspace())
        self.bind('<F5>',lambda e:self.draw_blank())
        self.bind('<Escape>',lambda e:self.select_tool('Crosshair'))
    def _menu(self):
        m=tk.Menu(self)
        definitions={
          'File':[('New Chart',lambda:self.new_chart(self.symbol.get().strip() or 'NIFTY')),('New Sheet',self.new_sheet),None,('Close Chart',self.close_active),('Export Workspace...',self.save_workspace),('Import Workspace...',self.open_workspace),None,('Exit',self.destroy)],
          'Edit':[('Undo Drawing',self.undo_drawing),('Clear Drawings',self.clear_drawings),None,('Copy Symbol',self.copy_symbol)],
          'View':[('Crosshair',lambda:self.select_tool('Crosshair')),('Clear Chart',self.clear_chart),None,('1m',lambda:self.tf.set('1m')),('5m',lambda:self.tf.set('5m')),('15m',lambda:self.tf.set('15m')),('1D',lambda:self.tf.set('1D'))],
          'Insert':[(t,lambda x=t:self.select_tool(x)) for t in ['Trend line','Horizontal line','Vertical line','Rectangle','Crosshair','Ray','Ellipse','Text marker']] + [None,('Grid   Ctrl+G',self.toggle_grid)],
          'Format':[('Toggle Crosshair',self.toggle_crosshair),('Clear Drawings',self.clear_drawings)],
          'Symbol':[('Open Symbol',lambda:self.new_chart(self.symbol.get().strip() or 'NIFTY')),('Find Symbol',self.focus_symbol)],
          'Analysis':[('Data Status',self.data_status),('Analysis Engine (not connected)',None)],
          'Tools':[('Bar Replay (requires market data)',None),('Preferences',self.preferences),('Customize',self.customize),('Reset View',self.reset_view)],
          'Window':[('Toggle Watchlist',self.toggle_watchlist),('New Chart',lambda:self.new_chart(self.symbol.get().strip() or 'NIFTY')),('Close Chart',self.close_active),('Next Chart',self.next_chart),('New Sheet',self.new_sheet)],
          'Help':[('User Guide',self.user_guide),('Search Help',self.user_guide),('Trading Platform Tips',self.user_guide),('Check for Updates (not connected)',None),('Resources (not connected)',None),('Release Information',self.release_info),('About Octopus',self.about)]
        }
        for name,entries in definitions.items():
            sub=tk.Menu(m,tearoff=False)
            for entry in entries:
                if entry is None:sub.add_separator()
                else:
                    label,callback=entry
                    sub.add_command(label=label,command=callback,state='normal' if callback else 'disabled')
            m.add_cascade(label=name,menu=sub)
        self.config(menu=m)
    def close_active(self):
        if self.active_index>=0:self.close_chart(self.active_index)
    def undo_drawing(self):
        shapes=self.shapes.get(self.active_sheet,[])
        if shapes:shapes.pop();self.draw_blank()
    def clear_drawings(self):
        self.shapes[self.active_sheet]=[];self.draw_blank()
    def copy_symbol(self):
        self.clipboard_clear();self.clipboard_append(self.active_chart or self.symbol.get())
    def focus_symbol(self):
        self.symbol_entry.focus_set();self.symbol_entry.select_range(0,'end')
    def next_chart(self):
        charts=self.sheets[self.active_sheet]
        if charts:self.activate((self.active_index+1)%len(charts))
    def save_workspace(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Magic Algo Workspace','*.json')])
        if not path:return
        try:
            with open(path,'w',encoding='utf-8') as f:json.dump({'sheets':self.sheets,'active_sheet':self.active_sheet,'timeframe':self.tf.get(),'drawings':self.shapes},f,indent=2)
            self.info.set('Workspace saved: '+path)
        except Exception as e:messagebox.showerror('Save failed',str(e))
    def open_workspace(self):
        path=filedialog.askopenfilename(filetypes=[('Magic Algo Workspace','*.json')])
        if not path:return
        try:
            with open(path,encoding='utf-8') as f:data=json.load(f)
            sheets=data['sheets']
            if not isinstance(sheets,dict) or not sheets or not all(isinstance(v,list) and all(isinstance(x,str) for x in v) for v in sheets.values()):raise ValueError('Invalid workspace')
            self.sheets=sheets;self.active_sheet=data.get('active_sheet','Sheet 1')
            if self.active_sheet not in sheets:self.active_sheet=next(iter(sheets))
            self.tf.set(data.get('timeframe','1m'))
            self.shapes={k:[tuple(item) for item in v] for k,v in data.get('drawings',{}).items() if isinstance(v,list)}
            self.drawing_meta=data.get('drawing_meta',{}) if isinstance(data.get('drawing_meta'),dict) else {}
            self.rebuild_sheets();self.show_sheet(self.active_sheet)
        except Exception as e:messagebox.showerror('Open failed',str(e))
    def rebuild_sheets(self):
        for child in self.sheetbar.winfo_children():child.destroy()
        for sheet in self.sheets:
            selected=(sheet==self.active_sheet)
            tk.Button(self.sheetbar,text=sheet,
                      command=lambda x=sheet:self.show_sheet(x),
                      font=('Segoe UI',9,'bold' if selected else 'normal'),
                      relief='flat',borderwidth=0,
                      bg='#fff1c6' if selected else '#e7ebf2',
                      activebackground='#fff1c6',padx=5).pack(side='left',padx=1,pady=1)
        tk.Button(self.sheetbar,text='+',command=self.new_sheet,
                  relief='flat',bg='#e7ebf2',padx=6).pack(side='left',padx=1,pady=1)
    def customize(self):
        """Compact, functional customization controls, separate from market data."""
        if getattr(self,'customize_window',None) and self.customize_window.winfo_exists():
            self.customize_window.lift();return
        win=tk.Toplevel(self);self.customize_window=win
        win.title('Octopus V064 — Customize');win.geometry('490x390');win.transient(self)
        book=ttk.Notebook(win);book.pack(fill='both',expand=True,padx=9,pady=9)
        config_path=self._prefs_path().with_name('MagicAlgoPro_customize.json')
        defaults={'full_menus':True,'large_icons':False,'tips':True,'shortcut_tips':True,'dark_lists':True,'tab_position':'Top','menu_animation':'None'}
        try:settings={**defaults,**json.loads(config_path.read_text(encoding='utf-8'))}
        except (OSError,ValueError):settings=defaults.copy()
        vars={k:(tk.BooleanVar(value=v) if isinstance(v,bool) else tk.StringVar(value=v)) for k,v in settings.items()}
        def page(name):
            frame=ttk.Frame(book,padding=15);book.add(frame,text=name);return frame
        options=page('Options')
        for key,label in [('full_menus','Always show full menus'),('large_icons','Large toolbar icons'),('tips','Show toolbar tooltips'),('shortcut_tips','Show shortcut keys in tooltips')]:
            ttk.Checkbutton(options,text=label,variable=vars[key]).pack(anchor='w',pady=7)
        ttk.Label(options,text='Menu animation').pack(anchor='w',pady=(12,3))
        ttk.Combobox(options,textvariable=vars['menu_animation'],values=['None','Fade','Slide'],state='readonly',width=17).pack(anchor='w')
        appearance=page('Appearance')
        ttk.Label(appearance,text='Chart tab location').pack(anchor='w',pady=5)
        for val in ['Top','Bottom']:ttk.Radiobutton(appearance,text=val,variable=vars['tab_position'],value=val).pack(anchor='w',pady=4)
        ttk.Checkbutton(appearance,text='Use dark theme for list views',variable=vars['dark_lists']).pack(anchor='w',pady=10)
        ttk.Label(appearance,text='Chart colors and grids: Tools → Preferences.').pack(anchor='w',pady=10)
        keys=page('Keyboard')
        ttk.Label(keys,text='Current shortcuts').pack(anchor='w')
        for line in ['Ctrl+N    New chart','Ctrl+W    Close chart','Ctrl+S    Save workspace','Ctrl+O    Open workspace','F5            Redraw chart','Esc          Crosshair tool']:
            ttk.Label(keys,text=line).pack(anchor='w',pady=4)
        ttk.Label(keys,text='Custom key reassignment is not available in this build.').pack(anchor='w',pady=9)
        footer=ttk.Frame(win);footer.pack(fill='x',padx=10,pady=(0,10))
        def apply(close=False):
            data={k:v.get() for k,v in vars.items()}
            try:
                config_path.parent.mkdir(parents=True,exist_ok=True)
                config_path.write_text(json.dumps(data,indent=2),encoding='utf-8')
            except OSError as exc:
                messagebox.showerror('Customize',str(exc),parent=win);return
            # Theme options are saved; avoid rebuilding charts or requesting data.
            if close:win.destroy()
        ttk.Button(footer,text='Close',command=win.destroy).pack(side='right',padx=4)
        ttk.Button(footer,text='Apply',command=apply).pack(side='right',padx=4)
        ttk.Button(footer,text='OK',command=lambda:apply(True)).pack(side='right',padx=4)

    def preferences(self):
        messagebox.showinfo('Preferences','Chart-first startup is enabled.\\nLive feed and order execution are not connected.')
    def user_guide(self):
        messagebox.showinfo('Octopus Guide','Use + to create a chart tab and × to close it.\\nUse the symbol field to open a chart.\\nChoose a drawing tool on the right.\\nUse File > Save Workspace to save your chart tabs.\\nNo live market data or broker orders are connected.')
    def release_info(self):
        messagebox.showinfo('Release Information','Octopus V064\\nChart-first foundation, functional menus, chart tabs, eight sheets and workspace save/open.\\nNo live market data or trading.')
    def about(self):
        messagebox.showinfo('About Octopus','Octopus V064\\nIndependent chart workspace foundation\\nOffline • Trading disabled')
    def _toolbar(self):
        f=tk.Frame(self,bg=BAR,height=28);f.pack(fill='x');f.pack_propagate(False);self.main_toolbar=f
        self.symbol=tk.StringVar(value='NIFTY');self.symbol_entry=tk.Entry(f,textvariable=self.symbol,width=24);self.symbol_entry.pack(side='left',padx=8)
        tk.Button(f,text='Open Symbol',command=lambda:self.new_chart(self.symbol.get().strip() or 'NIFTY')).pack(side='left')
        self.tf=tk.StringVar(value='1m');ttk.Combobox(f,textvariable=self.tf,values=['1m','5m','9m','15m','30m','60m','1D'],width=5,state='readonly').pack(side='left',padx=10)
        tk.Button(f,text='Watchlist',command=self.toggle_watchlist,relief='flat',bg=BAR).pack(side='left',padx=3)
        tk.Button(f,text='Zoom +',command=lambda:self.zoom(1),relief='flat',bg=BAR).pack(side='left',padx=2)
        tk.Button(f,text='Zoom −',command=lambda:self.zoom(-1),relief='flat',bg=BAR).pack(side='left',padx=2)
        # Dockable module widgets are constructed after the chart initializes.
        tk.Button(f,text='BROKER / TRADING ▾',command=self.toggle_trading,relief='flat',bg='#c4d5e9').pack(side='right',padx=5)
        self.feed_indicator=tk.Frame(f,bg=BAR)
        self.feed_indicator.pack(side='right',padx=5)
        self.feed_text=tk.Label(self.feed_indicator,text='DATA DISCONNECTED',bg=BAR,fg='#233b56',font=('Segoe UI',9,'bold'))
        self.feed_text.pack(side='right',padx=(4,0))
        self.feed_led=tk.Canvas(self.feed_indicator,width=14,height=14,bg=BAR,highlightthickness=0,bd=0)
        self.feed_led.pack(side='right')
        self.feed_led_dot=self.feed_led.create_oval(2,2,12,12,fill='#c32323',outline='#842020',width=1)
    def _tabs(self):
        f=tk.Frame(self,bg='#657d9e',height=23);f.pack(fill='x');f.pack_propagate(False);self.tabs=f
    def _chart(self):
        f=tk.Frame(self,bg=BG);f.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(f,bg=BG,highlightthickness=0,cursor='crosshair');self.canvas.pack(side='left',fill='both',expand=True)
        self.chart_frame=f
        tools=tk.Frame(f,bg='#d5deed',width=23);tools.pack(side='right',fill='y')
        self.drawing_toolbar=tools
        for label,tool in [('↗','Trend line'),('─','Horizontal line'),('│','Vertical line'),('▭','Rectangle'),('✛','Crosshair'),('◯','Ellipse'),('T','Text marker')]:
            tk.Button(tools,text=label,width=2,relief='flat',bg='#d5deed',command=lambda t=tool:self.select_tool(t)).pack(pady=2)
        self.canvas.bind('<Configure>',lambda e:self.draw_blank())
        self.canvas.bind('<Button-1>',self.point)
        self.canvas.bind('<MouseWheel>',lambda e:self.zoom(1 if e.delta>0 else -1))
        self.canvas.bind('<Motion>',self.move)
        self.canvas.bind('<ButtonPress-3>',self._axis_drag_start)
        self.canvas.bind('<B3-Motion>',self._axis_drag_move)
        self.canvas.bind('<ButtonRelease-3>',self._axis_drag_end)
        self.canvas.bind('<Leave>',lambda e:self.clear_pointer())
        self.tool='Crosshair';self.first=None;self.cross=[];self.shapes={};self.grid_on=False;self.cross_on=True;self.pointer=None;self.zoom_level=0;self.watchlist_panel=None;self.trading_panel=None
    def _sheets(self):
        # V050: Sheet controls and status share ONE compact bottom row.
        f=self.bottom_strip
        self.sheetbar=tk.Frame(f,bg='#d8e0ed')
        self.sheetbar.pack(side='left',fill='y')
        self.rebuild_sheets()

    def _status(self):
        self.info=tk.StringVar(value=f'{VERSION} | Blank chart workspace | Offline | No orders submitted')
        self.bottom_strip=tk.Frame(self,bg='#d8e0ed',height=25)
        self.bottom_strip.pack(side='bottom',fill='x')
        self.bottom_strip.pack_propagate(False)
        self.status_label=tk.Label(self.bottom_strip,textvariable=self.info,anchor='e',
                                   bg='#d8e0ed',fg='#273c59',font=('Segoe UI',8),
                                   padx=9)
        self.status_label.pack(side='right',fill='y')
    def new_sheet(self):
        s=f'Sheet {len(self.sheets)+1}'
        while s in self.sheets:s=f'Sheet {int(s.split()[-1])+1}'
        self.sheets[s]=[]
        self.rebuild_sheets()
        self.show_sheet(s)
    def show_sheet(self,s):
        self.active_sheet=s
        self.rebuild_sheets()
        if self.sheets[s]:
            self.active_index=len(self.sheets[s])-1
            self.active_chart=self.sheets[s][self.active_index]
        else:
            self.active_index=-1
            self.active_chart=None
        self.refresh_tabs();self.draw_blank()
        self.info.set(f'{VERSION} | {s} | No live data | Trading disabled')
    def new_chart(self,sym):
        sym=sym.strip().upper() or 'NIFTY'
        if sym in self.sheets[self.active_sheet]:
            self.active_index=self.sheets[self.active_sheet].index(sym);self.active_chart=sym
        else:
            self.sheets[self.active_sheet].append(sym);self.active_chart=sym;self.active_index=len(self.sheets[self.active_sheet])-1
        self.refresh_tabs();self.draw_blank()
    def refresh_tabs(self):
        for c in self.tabs.winfo_children(): c.destroy()
        for i, sym in enumerate(self.sheets[self.active_sheet]):
            active = (i == getattr(self, 'active_index', -1))
            bg = '#fff3c9' if active else '#e1e7f1'
            group = tk.Frame(self.tabs, bg=bg)
            group.pack(side='left', padx=1, pady=1)
            tk.Button(group, text=sym, font=('Segoe UI', 9, 'bold' if active else 'normal'),
                      bg=bg, relief='flat', borderwidth=0,
                      command=lambda j=i: self.activate(j)).pack(side='left')
            tk.Button(group, text='×', font=('Segoe UI', 9, 'bold'), bg=bg,
                      relief='flat', borderwidth=0, padx=3,
                      command=lambda j=i: self.close_chart(j)).pack(side='left')
        tk.Button(self.tabs, text='+', command=lambda:self.new_chart(self.symbol.get()),
                  bg='#d4deed', relief='flat').pack(side='left')
    def activate(self, i):
        self.active_index = i
        self.active_chart = self.sheets[self.active_sheet][i]
        self.symbol.set(self.active_chart)
        self.refresh_tabs()
        self.draw_blank()
    def close_chart(self, i):
        charts = self.sheets[self.active_sheet]
        if i < 0 or i >= len(charts): return
        charts.pop(i)
        old = getattr(self, 'active_index', 0)
        if not charts:
            self.active_index = -1
            self.active_chart = None
        else:
            self.active_index = min(old - (1 if i < old else 0), len(charts)-1) if i != old else min(i, len(charts)-1)
            self.active_chart = charts[self.active_index]
            self.symbol.set(self.active_chart)
        self.refresh_tabs()
        self.draw_blank()
        self.info.set(f'{VERSION} | {self.active_sheet} | Chart tab closed | No orders submitted')
    def clear_chart(self):
        self.sheets[self.active_sheet]=[];self.active_chart=None;self.active_index=-1;self.shapes[self.active_sheet]=[]
        self.refresh_tabs();self.draw_blank()
    def draw_blank(self):
        c=self.canvas;c.delete('all');w=c.winfo_width();h=c.winfo_height()
        if w<20 or h<20:return
        c.create_line(w-58,0,w-58,h,fill='#333333');c.create_line(0,h-25,w,h-25,fill='#333333')
        if self.grid_on:
            step=max(35,90-self.zoom_level*8)
            for x in range(0,w-58,step):c.create_line(x,0,x,h-25,fill='#202830',dash=(2,5))
            for y in range(0,h-25,step):c.create_line(0,y,w-58,y,fill='#202830',dash=(2,5))
        if not self.active_chart:
            c.create_text(w/2,h/2-10,text='This is a blank chart window.',fill='#ddd',font=('Segoe UI',12))
            c.create_text(w/2,h/2+22,text='Choose a symbol and connect a datafeed in a later stage.',fill='#aaa',font=('Segoe UI',10))
        else:
            c.create_text(w/2,h/2-10,text=self.active_chart+'  |  Chart awaiting datafeed',fill='#d5d5d5',font=('Segoe UI',13))
            c.create_text(w/2,h/2+22,text='No simulated market prices or live trading',fill='#999',font=('Segoe UI',10))
        for idx,item in enumerate(self.shapes.get(self.active_sheet,[])):
            if idx<len(self._drawing_metadata()) and not self._drawing_metadata()[idx].get("visible",True):continue
            typ,x1,y1,x2,y2=item
            if typ=='Rectangle':c.create_rectangle(x1,y1,x2,y2,outline='#e8b55c')
            elif typ=='Ellipse':c.create_oval(x1,y1,x2,y2,outline='#e8b55c')
            elif typ=='Text marker':c.create_text(x1,y1,text='NOTE',fill='#e8b55c',anchor='nw')
            else:c.create_line(x1,y1,x2,y2,fill='#e8b55c',width=2)
        if self.cross_on and self.pointer:
            x,y=self.pointer;c.create_line(x,0,x,h-25,fill='#657d9e',dash=(3,3),tags='cross');c.create_line(0,y,w-58,y,fill='#657d9e',dash=(3,3),tags='cross')
    def select_tool(self,tool):self.tool=tool;self.first=None;self.info.set('Drawing tool: '+tool)
    def point(self,e):
        if self.tool=='Crosshair':return
        if self.tool=='Text marker':self.shapes.setdefault(self.active_sheet,[]).append((self.tool,e.x,e.y,e.x,e.y))
        elif self.tool=='Horizontal line':self.shapes.setdefault(self.active_sheet,[]).append((self.tool,0,e.y,self.canvas.winfo_width()-60,e.y))
        elif self.tool=='Vertical line':self.shapes.setdefault(self.active_sheet,[]).append((self.tool,e.x,0,e.x,self.canvas.winfo_height()-25))
        elif self.first is None:self.first=(e.x,e.y);return
        else:
            self.shapes.setdefault(self.active_sheet,[]).append((self.tool,*self.first,e.x,e.y));self.first=None
        self.draw_blank()
    def move(self,e):
        self.pointer=(e.x,e.y)
        self.canvas.delete('cross')
        if self.cross_on:
            self.canvas.create_line(e.x,0,e.x,self.canvas.winfo_height()-25,fill='#657d9e',dash=(3,3),tags='cross')
            self.canvas.create_line(0,e.y,self.canvas.winfo_width()-58,e.y,fill='#657d9e',dash=(3,3),tags='cross')
    def clear_pointer(self):
        self.pointer=None;self.canvas.delete('cross')
    def toggle_grid(self):
        self.grid_on=not self.grid_on
        if hasattr(self,'_v059_grid_var'):self._v059_grid_var.set(self.grid_on)
        self.draw_blank()
    def toggle_crosshair(self):
        self.cross_on=not self.cross_on;self.draw_blank()
    def zoom(self,delta):
        self.zoom_level=max(-4,min(6,self.zoom_level+delta));self.draw_blank()
        self.info.set(f'{VERSION} | View zoom {self.zoom_level:+d} | No market data')
    def reset_view(self):
        self.zoom_level=0;self.pointer=None;self.draw_blank()
    def data_status(self):
        messagebox.showinfo('Market Data','No datafeed is connected. Charts are blank by design. Broker trading is disabled.')
    def toggle_trading(self):
        if self.trading_panel is not None:
            self.trading_panel.destroy();self.trading_panel=None;return
        panel=tk.Frame(self.chart_frame,bg='#172436',width=310)
        panel.pack(side='right',fill='y',before=self.canvas)
        panel.pack_propagate(False);self.trading_panel=panel
        header=tk.Frame(panel,bg='#243750');header.pack(fill='x')
        tk.Label(header,text='BROKER / TRADING',fg='white',bg='#243750',font=('Segoe UI',10,'bold')).pack(side='left',padx=8,pady=6)
        tk.Button(header,text='×',command=self.toggle_trading,bg='#243750',fg='white',relief='flat').pack(side='right')
        broker=tk.StringVar(value='SHOONYA')
        ttk.Combobox(panel,textvariable=broker,state='readonly',values=['FLATTRADE','SHOONYA','ALICEBLUE','DHAN','ZERODHA','GROWW','FYERS','UPSTOX']).pack(fill='x',padx=8,pady=7)
        tk.Label(panel,text='BROKER NOT CONNECTED',fg='#ffcf83',bg='#172436').pack(anchor='w',padx=9)
        nav=ttk.Notebook(panel);nav.pack(fill='both',expand=True,padx=5,pady=7)
        for name in ['Login','Order Ticket','Order Book','Positions','P&L','Options']:
            page=tk.Frame(nav,bg='#172436');nav.add(page,text=name)
            if name=='Order Ticket':
                for label in ['Instrument','Quantity','Order Type','Price','Stop Loss','Target']:
                    line=tk.Frame(page,bg='#172436');line.pack(fill='x',padx=7,pady=3)
                    tk.Label(line,text=label,width=11,anchor='w',fg='white',bg='#172436').pack(side='left')
                    tk.Entry(line,width=16).pack(side='left',fill='x',expand=True)
                tk.Label(page,text='ORDER SUBMISSION DISABLED',fg='#ffcf83',bg='#172436').pack(pady=12)
            else:
                tk.Label(page,text=name+'\nBroker runtime not connected to this chart app.',fg='#dce7f5',bg='#172436',wraplength=260,justify='center').pack(expand=True)
        tk.Label(panel,text='V034 historical chart stage • Existing V119 remains separate\nNo orders sent • No broker credentials read',bg='#172436',fg='#9db1c9',justify='center',wraplength=280).pack(side='bottom',pady=10)
    def toggle_watchlist(self):
        if self.watchlist_panel is not None:
            self.watchlist_panel.destroy();self.watchlist_panel=None;return
        p=tk.Frame(self.chart_frame,bg='#1b2736',width=185)
        p.pack(side='right',fill='y',before=self.canvas);p.pack_propagate(False)
        self.watchlist_panel=p
        tk.Label(p,text='WATCHLIST',bg='#1b2736',fg='white',font=('Segoe UI',10,'bold')).pack(fill='x',pady=8)
        for sym in ['NIFTY','BANKNIFTY','FINNIFTY','SENSEX','BANKEX','RELIANCE','SBIN']:
            tk.Button(p,text=sym,anchor='w',bg='#243448',fg='white',relief='flat',command=lambda x=sym:self.new_chart(x)).pack(fill='x',padx=5,pady=1)
        tk.Label(p,text='Symbols only • No quotes',bg='#1b2736',fg='#b8c6d8').pack(side='bottom',pady=8)



# V034: Historical chart module. No broker credentials or live orders are used.
import urllib.request, urllib.parse, datetime, math, threading, statistics

ICON_DATA_V064 = {'Crosshair': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAP0lEQVR42mNgoCdQ2XHtPyE1TNSybCQbBAtoYgKcaEPIMgxZEy42MmCk2NnUdhHVwoiRFJfd8dBiHM1rg8AgAPNuMdaWOikwAAAAAElFTkSuQmCC', 'Trend line': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS65I6HFiNZBmEzhIGBgYGRUgNICiNChhBlEDGGEDSIWEPwGkSKITgNItUQjFgjxwAMF1FiCNwgSg3BGS4DCgA2dDbbIuffeQAAAABJRU5ErkJggg==', 'Horizontal line': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAJElEQVR42mNgGAWjYBABRhhDZce1/+QacsdDi5FpNCxHARUAANhGBAQsWquyAAAAAElFTkSuQmCC', 'Vertical line': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAJklEQVR42mNgGJJAZce1/yo7rv3Hp4aJWpaNGjRq0KhBQ8wgqgEA/MkFf/iCo9QAAAAASUVORK5CYII=', 'Rectangle': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAOklEQVR42mNgGLaAEZmjsuPaf1INuOOhxcjAwMDARC0XseCzBR9Adz3VXDRq0Ig2iIWYxEZXFw0+AADaRArPfGioEgAAAABJRU5ErkJggg==', 'Ray': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS65I6HFiNZBmEzhIGBgYGRUgNICiNChhBlEDGGEDSIWEPwGkSKITgNItUQjFgjxwAMF1FiCNwgSg3BGS4DCgA2dDbbIuffeQAAAABJRU5ErkJggg==', 'Ellipse': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAATElEQVR42mNgGLaAEZ+kyo5r/9HF7nhoYdXDRIoh+MRxGoLPIKIMI0YhQTVE24ZFLRO1Ym0YG0SbWKMkHTGSmrJxZRMmUhTjEx98AABXWkXj3SC6YQAAAABJRU5ErkJggg==', 'Text marker': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAO0lEQVR42mNgGLaAEV1AZce1QAYGhnwo14aBgeEIlD3ljofWGrJsUdlx7QOxapmo5bVRg+ho0CgY0QAAQo4IsHMbX98AAAAASUVORK5CYII=', 'SMA 20': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS66o6HFiPZBiF7iWyvIRsCcw1FXkM2hGSDsHkJr0EqO679R9eEy0s4DULWgM1AbIZgGIRuK0wTPi/h9A4uTYQMYyTG/wzUipGhCQCNJ0BgMMD/0AAAAABJRU5ErkJggg==', 'EMA 20': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS66o6HFiPZBiF7iWyvIRsCcw1FXkM2hGSDsHkJr0EqO679R9eEy0s4DULWgM1AbIZgGIRuK0wTPi/h9A4uTYQMYyTG/wzUipGhCQCNJ0BgMMD/0AAAAABJRU5ErkJggg==', 'Volume': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAANElEQVR42mNgGGhgdLXiv9HViv8wPhO1DKa9QehOH3gX0cwgQl4dxF4jNZaGUayNYIOoBgCHNBQPGB+YpAAAAABJRU5ErkJggg==', 'RSI 14': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS66o6HFiPZBiF7iWyvIRsCcw1FXkM2hGSDsHkJr0EqO679R9eEy0s4DULWgM1AbIZgGIRuK0wTPi/h9A4uTYQMYyTG/wzUipGhCQCNJ0BgMMD/0AAAAABJRU5ErkJggg==', 'Bollinger Bands 20, 2': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS66o6HFiPZBiF7iWyvIRsCcw1FXkM2hGSDsHkJr0EqO679R9eEy0s4DULWgM1AbIZgGIRuK0wTPi/h9A4uTYQMYyTG/wzUipGhCQCNJ0BgMMD/0AAAAABJRU5ErkJggg==', 'Refresh historical candles': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS66o6HFiPZBiF7iWyvIRsCcw1FXkM2hGSDsHkJr0EqO679R9eEy0s4DULWgM1AbIZgGIRuK0wTPi/h9A4uTYQMYyTG/wzUipGhCQCNJ0BgMMD/0AAAAABJRU5ErkJggg==', 'Data source / status': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGAXYgMqOa/9hbCZKDYHRTJS66o6HFiPZBiF7iWyvIRsCcw1FXkM2hGSDsHkJr0EqO679R9eEy0s4DULWgM1AbIZgGIRuK0wTPi/h9A4uTYQMYyTG/wzUipGhCQCNJ0BgMMD/0AAAAABJRU5ErkJggg==', 'Replay back 10 bars': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWElEQVR42mNgGBlAZce1/+TqZcJmGDkGMuFzHSkGMhHjXWIMZCIl/PAZyEROhGAzkImSGEY2kIVcg+54aDEi81koNYBkg3AZQLRBhAwgaBCxBlA9rw0+AAC1TCxaZvrwhgAAAABJRU5ErkJggg==', 'Replay forward 1 bar': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWElEQVR42mNgGBlAZce1/+TqZcJmGDkGMuFzHSkGMhHjXWIMZCIl/PAZyEROhGAzkImSGEY2kIVcg+54aDEi81koNYBkg3AZQLRBhAwgaBCxBlA9rw0+AAC1TCxaZvrwhgAAAABJRU5ErkJggg==', 'LIVE (latest downloaded bar)': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAARklEQVR42mNgGAWEACM+SaOrFf/Rxc5pd2DVw0SKIfjEmUhRjE+eiVRDcKljolZgjySDcKUTQuqYiFFEjDwTKYpJcfEwAgAS8hwWoOzfLAAAAABJRU5ErkJggg=='}

OCTOPUS_MENU_ICONS_V064 = {'save': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAATElEQVR42mNgGGyAEV1AdEXWf2I1v46YBtfPRK4h6OqZCNlErDwTtcJo8BnEQko4DC2v0T6M8CVOmqYjqsUaC6neIiqwSXUFqeqJAgBtExm0q/8VoQAAAABJRU5ErkJggg==', 'database': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAATElEQVR42mNgGGyAEV3AoO/Bf2I1XyhSgOtnItcQdPVMhGwiVp6JWmE0+AxiISUchpbXaB9G+BInTdMR1WKNhVRvERXYpLqCVPVEAQAHsBhPyhpVoQAAAABJRU5ErkJggg==', 'new': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAVklEQVR42mNgGLaAEZkjvmLRf1I0v4yIg+tnopaLWAjZhA1gczlRLhJfseg/IW9TzWu0DSNc4YDPe7R3EXLMwVwCEyM71ihyESnpCqdBpGYVqnpt8AEAVYAdpIkeJ74AAAAASUVORK5CYII=', 'sheet': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAVklEQVR42mNgGLaAEZmzqPf/f1I0xxUzwvUzUctFLIRswgawuZwoFy3q/f+fkLep5jXahhGucMDnPdq7CDnmYC6BiZEdaxS5iJR0hdMgUrMKVb02+AAAQ2Ag2JAkJfEAAAAASUVORK5CYII=', 'close': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWklEQVR42mNgGFngZkTcf1LlmXApwmUYLnkmfDaRwkcxSH3FIkZSXIisnpGcMMJmKRMxioiRZyJFMT5xJlKTAC5xJpqnI2Jjk6h0hGwIIcPwpiNS+VQJo8EHAPzLTxQXJRQTAAAAAElFTkSuQmCC', 'folder': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAS0lEQVR42mNgGAV0A4wwxq3F1v+xKVCLPcpIkom4DMIljg5YCClQiz3KSMgwFFcTazMuF7OQ4w1sgInq0Uep16jmosFnENVibfABACpxHxdYhnonAAAAAElFTkSuQmCC', 'exit': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWklEQVR42mNgGFngZkTcf1LlmXApwmUYLnkmfDaRwkcxSH3FIkZSXIisnpGcMMJmKRMxioiRZyJFMT5xJlKTAC5xJpqnI2Jjk6h0hGwIIcPwpiNS+VQJo8EHAPzLTxQXJRQTAAAAAElFTkSuQmCC', 'undo': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGLaAEZ/k1PSr/9HFsmdqMxI0CJtGbACbYUykeoEoF5HqHZwuItcQgl4j1hCywohkg0hxDV6DiE0KWA1CdwW6YVPTr/7HZQEjua5Bt5SJnPAhKWXjMozUSBg4AABtRSjXt5CXjwAAAABJRU5ErkJggg==', 'trash': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAWklEQVR42mNgGFngflr0f1LlmXApwmUYLnkmfDaRwkcxSHHWUkZSXIisnpGcMMJmKRMxioiRZyJFMT5xJlKTAC5xJpqnI2Jjk6h0hGwIIcPwpiNS+VQJo8EHAEvFT6111kzeAAAAAElFTkSuQmCC', 'copy': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAXUlEQVR42mNgGGyAEZ9kSPft/4QMWFOqysjAwMDARC0XsRCjCGYrPteyEOMVZHFshlLVa0y4vIJsMy5X0M9FA2oQUdGPHGu4YpY+LkKOLZhLcMUgC7l5jGZeG3wAAE8PICYq1GBdAAAAAElFTkSuQmCC', 'cross': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAMklEQVR42mNgGJJAdOWJ/6IrT/zHp4aJWpaNGkRHgxiRo5hcQ16HWzAyjSbIkWwQ1QAAdLYOLkXRpPkAAAAASUVORK5CYII=', 'grid': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAALUlEQVR42mNgGPSgsP/kf3LEmKjlAEZ8thIL+gvNGQef1wafQaOBPRrYgwoAAMiuLXSwPiuYAAAAAElFTkSuQmCC', 'clock': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAdUlEQVR42mNgGGyAEZ/k220+/9HFhL22MBJtEDYDCBnIhM8QZMXCXlsYkfnoljERYwgulyCrZyLG2cTIM6GbTsgQdMNg+pioFf30MwjZC/iSBROx4UHIQEZs0U8owLElEyZyUzZer+FLuYQSLdXyGtVyP9UAAN8vTSyv1KZJAAAAAElFTkSuQmCC', 'line': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGDbAc/mL/8h8JkoMQTaMiVouY6LUS9sjJRhJNgjdEIrDCN01JBmEy0t4DUKPFXxeggFGUsIBl2swXESuISgGEWMIPsCEy5DtkRKMMNvRabxhhGwYPg0UJ7ihBwDItTkhXHUsfwAAAABJRU5ErkJggg==', 'hline': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAJ0lEQVR42mNgGAWjgHLACGMEbVn7n1xD1vkEMzJRy0VMo5EyCqgAAAILBAbvJTfgAAAAAElFTkSuQmCC', 'vline': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAKklEQVR42mNgGGyAkZCCPQ0v/8PYLg3iONUzUctFowaNGjRq0BAziGoAAPo/BB7qZMuxAAAAAElFTkSuQmCC', 'box': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAOklEQVR42mNgGLaAEZlzYYHvf1INMEjYzMjAwMDARC0XseCzBR9Adz3VXDRq0Ig2iIWYxEZXFw0+AADnwwrat6mUlwAAAABJRU5ErkJggg==', 'ellipse': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAVklEQVR42mNgGAWEACM+yR0tV/+ji3nUaDMSbRA2AwgZyIjPAGy241LDQoxt2ORwunpHy9X/xHgJlx4masUaE03SAineQ1fLgi/6iYk12qYjSlL2MAYAwk48ksHMm0sAAAAASUVORK5CYII=', 'text': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAM0lEQVR42mNgGAWEACMyZ+W2c/9JNSDcy4iRgYGBgYmuzl657dx/Qq6lmotGDRo1aHgCAHyeCm71cQ53AAAAAElFTkSuQmCC', 'search': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAa0lEQVR42mNgGGyAEZeEyqLb/5H5d+JUGfEZxESMIbjE8AKVRbf/4zKIaMMIKcYnz0StwB58BlEtsBmJjX5CaYmJWA0wMVyWMJLqbVyWkRTYyJrRXUZyrOEyjKzox2YYI6VJharpjoGBgQEA7VpHdb34lysAAAAASUVORK5CYII=', 'chart': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGDZAbUXVf2Q+EyWGIBvGRC2XMVHqpVsRbYwkG4RuCMVhhO4akgzC5SW8BqHHCj4vwQAjKeGAyzUYLiLXEBSDiDEEH2DCZcitiDZGmO3oNN4wQjYMnwaKE9zQAwDUFDXBcUGTiwAAAABJRU5ErkJggg==', 'settings': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAARUlEQVR42mNgoCdonnr8f/PU4//xqWGilmVD0CBCYQMDjOQYUJttyUgzrzEScg2y7bjEB2esDZHAJibgSXYRPs0jJNMCAOf5Hdlg3lwhAAAAAElFTkSuQmCC', 'info': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAbUlEQVR42mNgGGyAEZ9kwvwb/9HFFiRqMBJtEDYDCBnIhM+QBYkajDANyGxsljHhMwRZDEbjMoyJkLORXYQvnJjQTccVmOheQXcxE7WifyQYhB54hAB65DCRk7KxyTMSStnEylMtr1Et91MNAAC7ck1EYTf6agAAAABJRU5ErkJggg==', 'refresh': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAZElEQVR42mNgGLaAEZ+kxIal/9HFXgREMxI0CJtGbACbYUykeoEoF5HqHZwuItcQgl4j1hCywohkg0hxDV6DiE0KWA1CdwW6YRIblv7HZQEjua5Bt5SJnPAhKWXjMozUSBg4AADv/ypn9baMtwAAAABJRU5ErkJggg==', 'arrow': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAU0lEQVR42mNgGFkgfMXW/6TqYcJnGCkGMlHLdUzEepWQgUykhh0uA5moFRlMlMQssoEs5Bq0MsKbkWIXoRtCsouwGUCSQfgMINprxBhC1bw2+AAAbgInAj4dOb4AAAAASUVORK5CYII=', 'play': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAU0lEQVR42mNgGFkgaV3hf1L1MOEzjBQDmajlOiZivUrIQCZSww6XgUzUigwmSmIW2UAWcg2aF9TPSLGL0A0h2UXYDCDJIHwGEO01Ygyhal4bfAAAyH4lnYctCqkAAAAASUVORK5CYII=', 'pause': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAKElEQVR42mNgGLaAEV3g2hL3/8h8rZidjMTIMVHLRaMGjRo0atAQAwBRhAgaS5ogOwAAAABJRU5ErkJggg==', 'eye': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAATklEQVR42mNgGAV0A4y4JKr3XPyPS67VRZ+RoEH4DMBnIBMuQ1pd9BnRbUYXQ1aPIYhLITZXIOtholZgM9Ek1tDDiBQxqsUa1dLRKCAMAKYmMf9Qn47iAAAAAElFTkSuQmCC', 'help': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAbElEQVR42mNgGGyAEZ9k9fyL/9HFWhP1GYk2CJsBhAxkwmdIa6I+I0wDMhubZUz4DEEWg9G4DGMi5GxkF+ELJyZ003EFJrpX0F3MRK3oHwkGoQceIYAeOUzkpGxs8oyEUjax8lTLa1TL/VQDACM0TTDhpPOBAAAAAElFTkSuQmCC', 'lock': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAVUlEQVR42mNgoBJgJKSgY9nR/zB2RZQ1TvVMxBqCjU8U6Fh29D82g0gyDJ8GXHJM1ApsqhnEQLPoJyUwkZMD1bzGQoxtxLh68MXa4DOIhZQAHVopGwB7RiyDUSxKqQAAAABJRU5ErkJggg==', 'generic': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAARklEQVR42mNgGAWEACM+yaLulf/RxfpKw7HqYSLFEHziTKQoxifPRKohuNQxUSuwR5JBuNIJIXVMxCgiRp6JFMWkuHgYAQDpIxwWhFCMPAAAAABJRU5ErkJggg==', 'next': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAU0lEQVR42mNgGFkgYePu/6TqYcJnGCkGMlHLdUzEepWQgUykhh0uA5moFRlMlMQssoEs5Bq0wN+VkWIXoRtCsouwGUCSQfgMINprxBhC1bw2+AAAF1wnqpEvD94AAAAASUVORK5CYII=', 'volume': 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAANUlEQVR42mNgGDbAf3fzf//dzf9hfCZqGUx7g9CdPvAuoplBhLw6iL1GaiwNo1gbegZRDQAALoAUff4bS8sAAAAASUVORK5CYII='}

class ChartApp(App):
    SYMBOL_MAP={'NIFTY':'^NSEI','BANKNIFTY':'^NSEBANK','FINNIFTY':'NIFTY_FIN_SERVICE.NS',
                'SENSEX':'^BSESN','RELIANCE':'RELIANCE.NS','SBIN':'SBIN.NS'}
    def __init__(self):
        self.prefs=self._load_prefs()
        self.bars_cache={}; self.loading=set(); self.errors={};self.replay_count=None
        self.show_sma=None
        self.chart_kind='Candles'
        self.tab_timeframes={}
        self.tab_views={}
        self._slider_sync=False
        self.pan_fraction=0.0
        self.price_shift=0.0
        self._changing_tab=False
        super().__init__()
        self.title(f'Octopus {VERSION} | Chart Workspace')
        self.show_sma=tk.BooleanVar(master=self,value=True)
        self.show_ema=tk.BooleanVar(master=self,value=False)
        self.show_volume=tk.BooleanVar(master=self,value=False)
        self.show_rsi=tk.BooleanVar(master=self,value=False)
        self.show_bbands=tk.BooleanVar(master=self,value=False)
        self.tf.trace_add('write',lambda *_:self._timeframe_changed())
        self.drawing_meta={}
        self._install_drawing_tools()
        self._enhance_menus()
        self._chart_buttons()
        self._capture_controls()
        self._chart_type_control()
        self._navigation_sliders()
        self._restore_view()
        self._install_navigation_shortcuts()
        if self.active_chart:self.tab_timeframes[(self.active_sheet,self.active_chart)]=self.tf.get()
        self.request_bars()
        self._install_workspace_saving()
        self._v057_install_menu_icons()
        self._v059_grid_menu_state()
        self._v060_platform_foundation()
        self._initialize_database()
        self._load_cached_bars()
        self.after(200, self._restore_saved_workspace)
        self.protocol('WM_DELETE_WINDOW',self._close_with_save)
        self._auto_refresh_enabled=True
        self._auto_refresh_interval_ms=100
        self._network_refresh_interval_s=0.1
        self._last_network_refresh_at=0.0
        self._refresh_failures=0
        self._last_feed_success=0.0
        self._feed_blink_on=True
        self.after(100,self._auto_refresh_tick)
        self.after(500,self._feed_status_tick)
    def _v059_grid_menu_state(self):
        """Make Insert > Grid a real checked toggle, reflecting keyboard changes."""
        root_menu=self.nametowidget(self['menu'])
        for idx in range(root_menu.index('end')+1):
            if root_menu.type(idx)=='cascade' and root_menu.entrycget(idx,'label')=='Insert':
                sub=root_menu.nametowidget(root_menu.entrycget(idx,'menu'))
                for j in range(sub.index('end')+1):
                    if sub.type(j)=='command' and sub.entrycget(j,'label').startswith('Grid   Ctrl+G'):
                        sub.delete(j)
                        self._v059_grid_var=tk.BooleanVar(master=self,value=bool(self.grid_on))
                        kw={'label':'Grid   Ctrl+G','variable':self._v059_grid_var,
                            'command':self._v059_toggle_grid_from_menu}
                        icon=getattr(self,'_v057_icons',{}).get('grid')
                        if icon:kw.update(image=icon,compound='left')
                        sub.insert_checkbutton(j,**kw)
                        return
    def _v059_toggle_grid_from_menu(self):
        self.grid_on=bool(self._v059_grid_var.get())
        self.draw_blank()

    def _install_workspace_saving(self):
        menu=self.nametowidget(self['menu'])
        for i in range(menu.index('end')+1):
            if menu.type(i)=='cascade' and menu.entrycget(i,'label')=='File':
                file_menu=menu.nametowidget(menu.entrycget(i,'menu'))
                file_menu.insert_command(0,label='Save Active Sheet    Ctrl+S',command=self.save_sheet)
                file_menu.insert_command(1,label='Save All Sheets    Ctrl+Shift+S',command=self.save_all)
                file_menu.insert_separator(2)
                break
        self.bind_all('<Control-s>',lambda e:self._save_shortcut(self.save_sheet))
        self.bind_all('<Control-Shift-S>',lambda e:self._save_shortcut(self.save_all))
        self.bind_all('<Control-Shift-s>',lambda e:self._save_shortcut(self.save_all))
    def _save_shortcut(self,fn):
        fn()
        return 'break'
    def _workspace_file(self):
        from pathlib import Path
        import os
        folder=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'Octopus'
        folder.mkdir(parents=True,exist_ok=True)
        return folder / 'workspace.json'
    def _database_path(self):
        return self._workspace_file().parent / 'market_data.sqlite3'
    def _initialize_database(self):
        import sqlite3
        with sqlite3.connect(self._database_path(), timeout=10) as db:
            db.execute('CREATE TABLE IF NOT EXISTS candles (symbol TEXT NOT NULL, timeframe TEXT NOT NULL, ts INTEGER NOT NULL, open REAL, high REAL, low REAL, close REAL, volume REAL, PRIMARY KEY(symbol,timeframe,ts))')
            db.execute('CREATE INDEX IF NOT EXISTS candles_lookup ON candles(symbol,timeframe,ts)')
    def _canonical_candles(self,rows,tf):
        """One canonical candle per exchange-local timeframe bucket.

        Repeated intraminute snapshots represent the same candle, not new bars.
        Use the latest complete snapshot for each bucket, avoiding synthetic
        highs/lows created by merging partial provider snapshots.
        """
        import datetime
        if not rows:return []
        minutes={'1m':1,'5m':5,'9m':9,'15m':15,'30m':30,'60m':60}
        span=minutes.get(tf)
        ist=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
        buckets={}
        for row in sorted(rows,key=lambda r:int(r[0])):
            if len(row)<6:continue
            ts=int(row[0])
            if span:
                dt=datetime.datetime.fromtimestamp(ts,ist)
                if span==9:
                    # 9-minute bars begin at 09:15 IST, aligned to the session.
                    base=dt.replace(hour=9,minute=15,second=0,microsecond=0)
                    delta=int((dt-base).total_seconds()//60)
                    bucket=int((base+datetime.timedelta(minutes=(delta//9)*9)).timestamp())
                else:
                    bucket=ts//(span*60)*(span*60)
            else:
                dt=datetime.datetime.fromtimestamp(ts,ist)
                bucket=int(dt.replace(hour=0,minute=0,second=0,microsecond=0).timestamp())
            buckets[bucket]=(bucket,*tuple(float(v) for v in row[1:6]))
        return [buckets[k] for k in sorted(buckets)]

    def _load_cached_bars(self):
        import sqlite3
        try:
            with sqlite3.connect(self._database_path(), timeout=10) as db:
                for symbol,tf in db.execute('SELECT DISTINCT symbol,timeframe FROM candles'):
                    rows=db.execute('SELECT ts,open,high,low,close,volume FROM candles WHERE symbol=? AND timeframe=? ORDER BY ts',(symbol,tf)).fetchall()
                    if rows:self.bars_cache[(symbol,tf)]=self._canonical_candles(rows,tf)
        except Exception as exc:
            self.info.set('Database restore warning: '+str(exc)[:90])
    def _save_cached_bars(self):
        import sqlite3
        with sqlite3.connect(self._database_path(),timeout=20) as db:
            for (symbol,tf),rows in self.bars_cache.items():
                db.executemany('INSERT OR REPLACE INTO candles(symbol,timeframe,ts,open,high,low,close,volume) VALUES (?,?,?,?,?,?,?,?)',[(symbol,tf,*row[:6]) for row in rows])
    def _persist_downloaded_bars(self,key,rows):
        import sqlite3
        with sqlite3.connect(self._database_path(),timeout=20) as db:
            # Remove legacy duplicate/subminute timestamps from this series.
            db.execute('DELETE FROM candles WHERE symbol=? AND timeframe=?',key)
            db.executemany('INSERT OR REPLACE INTO candles(symbol,timeframe,ts,open,high,low,close,volume) VALUES (?,?,?,?,?,?,?,?)',[(key[0],key[1],*row[:6]) for row in rows])
    def _sheet_state(self, sheet):
        charts=list(self.sheets.get(sheet,[]))
        timeframes={c:(self.tf.get() if sheet==self.active_sheet and c==self.active_chart else self.tab_timeframes.get((sheet,c),'1m')) for c in charts}
        views={c:list((self.pan_fraction,self.price_shift) if sheet==self.active_sheet and c==self.active_chart else self.tab_views.get((sheet,c),(1.0,0.0))) for c in charts}
        return {'charts':charts,'active_chart':self.active_chart if sheet==self.active_sheet else (charts[0] if charts else None),
                'timeframes':timeframes,'views':views,'drawings':self.shapes.get(sheet,[]),'drawing_meta':self.drawing_meta.get(sheet,[])}
    def _write_workspace(self, all_sheets=False):
        import json,os
        path=self._workspace_file()
        data={'format':'Octopus Workspace','version':1,'active_sheet':self.active_sheet,'sheets':{},'indicators':{},'chart_state':{}}
        if path.exists():
            try:
                previous=json.loads(path.read_text(encoding='utf-8'))
                if isinstance(previous.get('sheets'),dict):data['sheets']=previous['sheets']
                if isinstance(previous.get('indicators'),dict):data['indicators']=previous['indicators']
            except (OSError,ValueError,TypeError):pass
        data['chart_state']={'zoom_level':getattr(self,'zoom_level',0),'replay_count':self.replay_count,'active_sheet':self.active_sheet}
        names=list(self.sheets) if all_sheets else [self.active_sheet]
        for name in names:data['sheets'][name]=self._sheet_state(name)
        for name in ('sma','ema','volume','rsi','bbands'):
            var=getattr(self,'show_'+name,None)            if var is not None:data['indicators'][name]=bool(var.get())
        if all_sheets:self._save_cached_bars()
        temp=path.with_suffix('.tmp')
        temp.write_text(json.dumps(data,indent=2),encoding='utf-8')
        # Preserve the last known-good workspace before an atomic replacement.
        if path.exists():
            import shutil
            backup=path.with_name('workspace.previous.json')
            shutil.copy2(path,backup)
        os.replace(temp,path)
        self.info.set(('Save All' if all_sheets else 'Saved '+self.active_sheet)+' | '+str(path))
    def save_sheet(self):
        try:self._write_workspace(False)
        except Exception as exc:messagebox.showerror('Save Sheet',str(exc))
    def save_all(self):
        try:self._write_workspace(True)
        except Exception as exc:messagebox.showerror('Save All',str(exc))
    def _restore_saved_workspace(self):
        path=self._workspace_file()
        if not path.exists():return
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            stored=data.get('sheets',{})
            if not isinstance(stored,dict) or not stored:return
            restored={}
            for sheet,state in stored.items():
                if not isinstance(sheet,str) or not isinstance(state,dict):continue
                charts=state.get('charts',[])
                if not isinstance(charts,list) or not all(isinstance(c,str) for c in charts):continue
                restored[sheet]=charts
                for chart,tf in state.get('timeframes',{}).items():
                    if chart in charts and tf in ('1m','5m','9m','15m','30m','60m','1D'):
                        self.tab_timeframes[(sheet,chart)]=tf
                for chart,view in state.get('views',{}).items():
                    if chart in charts and isinstance(view,list) and len(view)==2:
                        self.tab_views[(sheet,chart)]=(float(view[0]),float(view[1]))
                self.shapes[sheet]=[tuple(d) for d in state.get('drawings',[]) if isinstance(d,(list,tuple)) and len(d)==5]
                self.drawing_meta[sheet]=state.get('drawing_meta',[]) if isinstance(state.get('drawing_meta',[]),list) else []
            if not restored:return
            self.sheets=restored
            self.active_sheet=data.get('active_sheet') if data.get('active_sheet') in restored else next(iter(restored))
            for name,value in data.get('indicators',{}).items():
                var=getattr(self,'show_'+name,None)
                if var is not None:var.set(bool(value))
            self.rebuild_sheets()
            self.show_sheet(self.active_sheet)
            target=stored.get(self.active_sheet,{}).get('active_chart')
            if target in self.sheets[self.active_sheet]:self.activate(self.sheets[self.active_sheet].index(target))
            chart_state=data.get('chart_state',{})
            if isinstance(chart_state,dict):
                self.zoom_level=chart_state.get('zoom_level',getattr(self,'zoom_level',0))
                self.replay_count=chart_state.get('replay_count')
            self.draw_blank()
            self.info.set('V064 | Saved workspace and database restored | Orders disabled')
        except Exception as exc:
            self.info.set('V064 | Workspace restore failed: '+str(exc)[:90])
    def _close_with_save(self):
        if getattr(self,'_recording',False):self._rec_stop()
        self._auto_refresh_enabled=False
        try:self._write_workspace(True)
        except Exception:pass
        self.destroy()
    def _install_drawing_tools(self):
        # Compact icon-backed menus and a keyboard-searchable tool picker.
        import base64
        self._tool_icons={}
        icon_data=ICON_DATA_V064
        for name,data in icon_data.items():
            try:self._tool_icons[name]=tk.PhotoImage(master=self,data=data)
            except tk.TclError:pass
        self._drawing_choice=tk.StringVar(master=self,value=self.tool)
        menu=self.nametowidget(self['menu'])
        drawings=tk.Menu(menu,tearoff=False)
        drawings.add_command(label='Find tool...    Ctrl+K',command=self._open_tool_palette)
        drawings.add_separator()
        self._drawing_names=('Crosshair','Trend line','Horizontal line','Vertical line','Rectangle','Ray','Ellipse','Text marker')
        for name in self._drawing_names:
            opts={'label':name,'variable':self._drawing_choice,'value':name,'command':lambda n=name:self.select_tool(n)}
            if name in self._tool_icons:opts.update(image=self._tool_icons[name],compound='left')
            drawings.add_radiobutton(**opts)
        drawings.add_separator()
        drawings.add_command(label='Undo last drawing    Ctrl+Z',command=self._undo_drawing)
        drawings.add_command(label='Delete drawing near pointer    Delete',command=self._delete_nearest_drawing)
        drawings.add_command(label='Clear drawings on this sheet',command=self._clear_drawings)
        drawings.add_separator()
        drawings.add_command(label='Drawing Manager...    Ctrl+Shift+D',command=self._open_drawing_manager)
        menu.add_cascade(label='Drawings',menu=drawings)
        self.bind_all('<Control-k>',lambda e:self._palette_shortcut())
        self.bind_all('<Control-Shift-D>',lambda e:self._manager_shortcut())
        self.bind_all('<Control-Shift-d>',lambda e:self._manager_shortcut())
        self.bind_all('<Control-z>',lambda e:self._drawing_shortcut(self._undo_drawing))
        self.bind_all('<Delete>',lambda e:self._drawing_shortcut(self._delete_nearest_drawing))
        self.canvas.bind('<Control-Button-1>',lambda e:self._delete_nearest_drawing((e.x,e.y)))
        # Add icons to the existing Insert drawing submenu without replacing callbacks.
        for i in range(menu.index('end')+1):
            if menu.type(i)=='cascade' and menu.entrycget(i,'label')=='Insert':
                sub=menu.nametowidget(menu.entrycget(i,'menu'))
                for j in range(sub.index('end')+1):
                    if sub.type(j) in ('command','checkbutton'):
                        name=sub.entrycget(j,'label')
                        if name in self._tool_icons:
                            sub.entryconfigure(j,image=self._tool_icons[name],compound='left')
                break

    def select_tool(self,tool):
        super().select_tool(tool)
        if hasattr(self,'_drawing_choice'):self._drawing_choice.set(tool)

    def _palette_shortcut(self):
        self._open_tool_palette()
        return 'break'

    def _open_tool_palette(self):
        old=getattr(self,'_palette_window',None)
        if old is not None and old.winfo_exists():
            old.lift();old.focus_force();return
        popup=tk.Toplevel(self)
        self._palette_window=popup
        popup.title('Octopus | Find Drawing Tool')
        popup.transient(self)
        popup.resizable(False,False)
        popup.configure(bg='#192638')
        popup.geometry('340x300')
        query=tk.StringVar(master=popup)
        entry=tk.Entry(popup,textvariable=query,font=('Segoe UI',12),bg='#eaf1f7',fg='#101820')
        entry.pack(fill='x',padx=10,pady=(10,6))
        results=tk.Listbox(popup,font=('Segoe UI',11),bg='#172334',fg='#eaf1f7',selectbackground='#246a8c',activestyle='none',height=10)
        results.pack(fill='both',expand=True,padx=10,pady=(0,10))
        def refresh(*_):
            results.delete(0,'end')
            for name in self._drawing_names:
                if query.get().strip().lower() in name.lower():results.insert('end',name)
            if results.size():results.selection_set(0)
        def choose(_=None):
            selected=results.curselection()
            if not selected:return 'break'
            self.select_tool(results.get(selected[0]));popup.destroy();return 'break'
        query.trace_add('write',refresh)
        entry.bind('<Return>',choose)
        results.bind('<Return>',choose)
        results.bind('<Double-Button-1>',choose)
        popup.bind('<Escape>',lambda e:popup.destroy())
        refresh();entry.focus_set()

    def _manager_shortcut(self):
        self._open_drawing_manager()
        return 'break'

    def _drawing_metadata(self, sheet=None):
        sheet=sheet or self.active_sheet
        drawings=self.shapes.get(sheet,[])
        meta=self.drawing_meta.setdefault(sheet,[])
        while len(meta)<len(drawings):
            i=len(meta)
            meta.append({'name':drawings[i][0]+' '+str(i+1),'visible':True,'locked':False})
        if len(meta)>len(drawings):del meta[len(drawings):]
        return meta

    def _open_drawing_manager(self):
        """Non-modal drawing editor for the current sheet."""
        old=getattr(self,'_drawing_manager_window',None)
        if old is not None and old.winfo_exists():
            old.lift();old.focus_force();return
        win=tk.Toplevel(self);self._drawing_manager_window=win
        win.title('Octopus V064 | Drawing Manager');win.geometry('630x430');win.minsize(530,340)
        win.transient(self);win.configure(bg='#172334')
        title=tk.Label(win,bg='#172334',fg='#f2f6fb',font=('Segoe UI',11,'bold'))
        title.pack(anchor='w',padx=12,pady=(10,5))
        lb=tk.Listbox(win,selectmode='extended',bg='#101b2a',fg='#f0f5fa',selectbackground='#27698b',font=('Segoe UI',10),activestyle='none')
        lb.pack(fill='both',expand=True,padx=12,pady=5)
        def refresh(select=None):
            selected=lb.curselection() if select is None else (select,)
            lb.delete(0,'end');meta=self._drawing_metadata()
            for i,item in enumerate(self.shapes.get(self.active_sheet,[])):
                m=meta[i];flags=('●' if m.get('visible',True) else '○')+('  LOCK' if m.get('locked') else '')
                lb.insert('end',f'{i+1:03d}  {flags:8}  {m.get("name",item[0])}   [{item[0]}]')
            for i in selected:
                if 0<=i<lb.size():lb.selection_set(i);lb.see(i)
            title.config(text=f'Drawings on {self.active_sheet}  •  {lb.size()} objects')
        def selected():return list(lb.curselection())
        def change(action):
            inds=selected();drawings=self.shapes.setdefault(self.active_sheet,[]);meta=self._drawing_metadata()
            if action=='delete':
                for i in reversed(inds):
                    if not meta[i].get('locked'):drawings.pop(i);meta.pop(i)
            elif action=='duplicate':
                for i in inds:
                    if meta[i].get('locked'):continue
                    typ,x1,y1,x2,y2=drawings[i]
                    drawings.append((typ,x1+12,y1+12,x2+12,y2+12))
                    meta.append({'name':meta[i].get('name',typ)+' copy','visible':True,'locked':False})
            elif action in ('visible','locked'):
                key='visible' if action=='visible' else 'locked'
                for i in inds:meta[i][key]=not meta[i].get(key,key=='visible')
            elif action=='rename' and len(inds)==1:
                from tkinter import simpledialog
                i=inds[0];name=simpledialog.askstring('Rename drawing','Drawing name:',initialvalue=meta[i].get('name',''),parent=win)
                if name and name.strip():meta[i]['name']=name.strip()[:90]
            self.draw_blank();refresh(inds[0] if inds and action!='delete' else None)
        def add():
            from tkinter import simpledialog
            choices=('Trend line','Horizontal line','Vertical line','Rectangle','Ray','Ellipse','Text marker')
            tool=simpledialog.askstring('Add Drawing','Enter drawing type:\n'+', '.join(choices),initialvalue='Trend line',parent=win)
            if not tool:return
            match=next((x for x in choices if x.casefold()==tool.strip().casefold()),None)
            if match is None:
                messagebox.showwarning('Drawing type','Choose a listed drawing type.',parent=win);return
            self.select_tool(match);win.lift()
            self.info.set('V064 | '+match+' selected. Click the chart to draw.')
            messagebox.showinfo('Draw on chart','Click the chart to place the drawing. Two clicks are needed for lines and shapes. The list updates automatically.',parent=win)
        bar=tk.Frame(win,bg='#172334');bar.pack(fill='x',padx=12,pady=(4,12))
        for label,fn in [('Add Drawing',add),('Show/Hide',lambda:change('visible')),('Lock/Unlock',lambda:change('locked')),('Rename',lambda:change('rename')),('Duplicate',lambda:change('duplicate')),('Delete',lambda:change('delete')),('Close',win.destroy)]:
            tk.Button(bar,text=label,command=fn,bg='#2a4057',fg='white',relief='flat',padx=6).pack(side='left',padx=(0,4))
        lb.bind('<Delete>',lambda e:change('delete'))
        win.bind('<Escape>',lambda e:win.destroy())
        def poll():
            if win.winfo_exists():
                if getattr(win,'_last_state',None)!=(self.active_sheet,len(self.shapes.get(self.active_sheet,[]))):
                    win._last_state=(self.active_sheet,len(self.shapes.get(self.active_sheet,[])))
                    refresh()
                win.after(350,poll)
        refresh();poll()

    def _drawing_shortcut(self,fn):
        if self.focus_get() is not None and isinstance(self.focus_get(),(tk.Entry,ttk.Entry,tk.Text)):
            return
        fn()

    def _undo_drawing(self):
        drawings=self.shapes.get(self.active_sheet,[])
        if drawings:
            meta=self._drawing_metadata()
            if meta[-1].get('locked'):
                self.info.set('V064 | Last drawing is locked');return
            drawings.pop();meta.pop()
            self.draw_blank()
            self.info.set('V064 | Last drawing removed')

    def _clear_drawings(self):
        meta=self._drawing_metadata()
        self.shapes[self.active_sheet]=[d for i,d in enumerate(self.shapes.get(self.active_sheet,[])) if meta[i].get('locked')]
        self.drawing_meta[self.active_sheet]=[m for m in meta if m.get('locked')]
        self.first=None
        self.draw_blank()
        self.info.set('V064 | Drawings cleared on '+self.active_sheet)

    def _delete_nearest_drawing(self,point=None):
        drawings=self.shapes.get(self.active_sheet,[])
        if not drawings:return
        pos=point or self.pointer
        if pos is None:
            self.info.set('V064 | Move pointer near a drawing, then press Delete')
            return
        px,py=pos
        def distance(item):
            typ,x1,y1,x2,y2=item
            if typ=='Horizontal line':return abs(py-y1)
            if typ=='Vertical line':return abs(px-x1)
            if typ=='Text marker':return ((px-x1)**2+(py-y1)**2)**.5
            if typ in ('Rectangle','Ellipse'):
                return min(abs(px-x1),abs(px-x2),abs(py-y1),abs(py-y2)) if min(x1,x2)-8<=px<=max(x1,x2)+8 and min(y1,y2)-8<=py<=max(y1,y2)+8 else 1e9
            dx=x2-x1;dy=y2-y1
            if dx==dy==0:return ((px-x1)**2+(py-y1)**2)**.5
            t=max(0,min(1,((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)))
            return ((px-x1-t*dx)**2+(py-y1-t*dy)**2)**.5
        meta=self._drawing_metadata()
        candidates=[i for i in range(len(drawings)) if not meta[i].get('locked') and meta[i].get('visible',True)]
        if not candidates:return
        idx=min(candidates,key=lambda i:distance(drawings[i]))
        if distance(drawings[idx])<=14:
            drawings.pop(idx);meta.pop(idx)
            self.draw_blank()
            self.info.set('V064 | Drawing deleted')
        else:self.info.set('V064 | No drawing within 14 pixels of pointer')

    def _install_navigation_shortcuts(self):
        # Navigation stays local to the active chart; no new UI row.
        self.canvas.bind('<MouseWheel>',self._wheel_navigation,add='+')
        self.canvas.bind('<Button-4>',lambda e:self._wheel_navigation(e,1),add='+')
        self.canvas.bind('<Button-5>',lambda e:self._wheel_navigation(e,-1),add='+')
        for sequence,action in (
            ('<Home>',self._jump_first),('<End>',self.replay_live),
            ('<Left>',lambda:self._pan_bars(-10)),('<Right>',lambda:self._pan_bars(10)),
            ('<Control-plus>',lambda:self.zoom(-1)),('<Control-minus>',lambda:self.zoom(1)),
            ('<Control-0>',self._fit_chart),('<Control-g>',self.toggle_grid),
            ('<Control-h>',self.toggle_crosshair),
            ('<Control-Left>',lambda:self.replay_step(-1)),
            ('<Control-Right>',lambda:self.replay_step(1))):
            self.bind_all(sequence,lambda event,fn=action: self._shortcut(fn))
        nav=tk.Menu(self.nametowidget(self['menu']),tearoff=False)
        for label,fn in (
            ('Fit chart   Ctrl+0',self._fit_chart),
            ('Go to first bars   Home',self._jump_first),
            ('Go to latest   End',self.replay_live),
            ('Pan 10 bars left   Left',lambda:self._pan_bars(-10)),
            ('Pan 10 bars right   Right',lambda:self._pan_bars(10)),
            ('Crosshair   Ctrl+H',self.toggle_crosshair)):
            nav.add_command(label=label,command=fn)
        self.nametowidget(self['menu']).add_cascade(label='Navigate',menu=nav)

    def _shortcut(self,fn):
        if self.focus_get() is not None and isinstance(self.focus_get(),(tk.Entry,ttk.Entry,ttk.Combobox)):
            return
        fn()
        return 'break'

    def _wheel_navigation(self,event,override=None):
        direction=override if override is not None else (1 if event.delta>0 else -1)
        if event.state & 0x0001: self._pan_bars(-direction*8)
        else: self.zoom(-direction)
        return 'break'

    def _pan_bars(self,delta):
        if not self.active_chart:return
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        if not rows:return
        available=min(self.replay_count or len(rows),len(rows))
        count=max(25,min(600,int(self.prefs['visible_bars'])+self.zoom_level*14))
        movable=max(1,available-count)
        self.pan_fraction=max(0,min(1,self.pan_fraction+delta/movable))
        self._remember_view()
        self._slider_sync=True
        try:self.hscroll.set(round(self.pan_fraction*1000))
        finally:self._slider_sync=False
        self.draw_blank()

    def _jump_first(self):
        self.pan_fraction=0.0
        self._remember_view()
        self._slider_sync=True
        try:self.hscroll.set(0)
        finally:self._slider_sync=False
        self.draw_blank()

    def _fit_chart(self):
        self.zoom_level=0
        self.price_shift=0.0
        self.pan_fraction=1.0
        self._remember_view()
        self._slider_sync=True
        try:self.hscroll.set(1000);self.vscroll.set(0)
        finally:self._slider_sync=False
        self.draw_blank()

    def _axis_drag_start(self,event):
        self._drag_origin=(event.x,event.y,self.pan_fraction,self.price_shift)

    def _axis_drag_move(self,event):
        origin=getattr(self,'_drag_origin',None)
        if origin is None:return
        x0,y0,pan,shift=origin
        w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height())
        if x0>=w-66:
            self.price_shift=max(-1,min(1,shift+(event.y-y0)/max(80,h*.6)))
        else:
            self.pan_fraction=max(0,min(1,pan+(x0-event.x)/max(80,w*.8)))
        self._slider_sync=True
        try:
            self.hscroll.set(round(self.pan_fraction*1000))
            self.vscroll.set(round(self.price_shift*100))
        finally:self._slider_sync=False
        self._remember_view();self.draw_blank()

    def _axis_drag_end(self,event):
        self._drag_origin=None

    def move(self,event):
        super().move(event)
        # Redraw quote inspection without re-fetching any market data.
        if self.active_chart and self.bars_cache:
            self.draw_blank()

    @staticmethod
    def _resample_session(rows,minutes):
        """Aggregate 1m bars from 09:15 IST with correct session boundaries."""
        from datetime import timezone,timedelta
        ist=timezone(timedelta(hours=5,minutes=30))
        buckets={}
        for ts,o,hi,lo,cl,vol in rows:
            dt=datetime.datetime.fromtimestamp(ts,ist)
            minute=dt.hour*60+dt.minute
            session_start=9*60+15
            if minute<session_start or minute>=15*60+30:continue
            index=(minute-session_start)//minutes
            start=dt.replace(hour=9,minute=15,second=0,microsecond=0)+datetime.timedelta(minutes=index*minutes)
            key=int(start.timestamp())
            if key not in buckets:buckets[key]=[key,o,hi,lo,cl,vol]
            else:
                bar=buckets[key]
                bar[2]=max(bar[2],hi);bar[3]=min(bar[3],lo)
                bar[4]=cl;bar[5]+=vol
        return [tuple(buckets[k]) for k in sorted(buckets)]

    def _navigation_sliders(self):
        # Sliders are attached to the chart, without another toolbar row.
        self.hscroll=tk.Scale(self.chart_frame,from_=0,to=1000,orient='horizontal',showvalue=False,
                              resolution=1,bg='#c9d5e4',highlightthickness=0,bd=0,
                              sliderlength=25,width=7,command=self._horizontal_changed)
        self.hscroll.pack(side='bottom',fill='x')
        self.vscroll=tk.Scale(self.chart_frame,from_=100,to=-100,orient='vertical',showvalue=False,
                              resolution=1,bg='#c9d5e4',highlightthickness=0,bd=0,
                              sliderlength=24,width=7,command=self._vertical_changed)
        self.vscroll.pack(side='right',fill='y',padx=0,pady=0)
        # V034: Pack order is critical in Tk. The expanding canvas must be LAST;
        # otherwise it reserves unused width before right-side widgets are laid out.
        # Reserve only the actual toolbar and scrollbar widths, not a black gutter.
        self.canvas.pack_forget()
        self.drawing_toolbar.pack_forget()
        self.hscroll.pack_forget()
        self.vscroll.pack_forget()
        self.hscroll.pack(side='bottom',fill='x')
        self.drawing_toolbar.pack(side='right',fill='y')
        self.vscroll.pack(side='right',fill='y',padx=0,pady=0)
        self.canvas.pack(side='left',fill='both',expand=True)
        self._slider_sync=True
        self.hscroll.set(1000);self.vscroll.set(0)
        self._slider_sync=False
    def _horizontal_changed(self,value):
        if self._slider_sync:return
        self.pan_fraction=float(value)/1000.0
        self._remember_view()
        self.draw_blank()
    def _vertical_changed(self,value):
        if self._slider_sync:return
        self.price_shift=float(value)/100.0
        self._remember_view()
        self.draw_blank()
    def _remember_view(self):
        if self.active_chart:self.tab_views[(self.active_sheet,self.active_chart)]=(self.pan_fraction,self.price_shift)
    def _restore_view(self):
        self.pan_fraction,self.price_shift=self.tab_views.get((self.active_sheet,self.active_chart),(1.0,0.0))
        if hasattr(self,'hscroll'):
            self._slider_sync=True
            self.hscroll.set(round(self.pan_fraction*1000))
            self.vscroll.set(round(self.price_shift*100))
            self._slider_sync=False

    def _v057_icon_kind(self, label):
        name=(label or '').lower()
        rules=(
          ('save all','database'),('save','save'),('database','database'),
          ('new sheet','sheet'),('new','new'),('close','close'),('exit','exit'),
          ('import','folder'),('export','folder'),('open','folder'),
          ('undo','undo'),('delete','trash'),('clear','trash'),('copy','copy'),
          ('crosshair','cross'),('grid','grid'),('horizontal','hline'),('vertical','vline'),
          ('trend','line'),('ray','line'),('rectangle','box'),('ellipse','ellipse'),
          ('text','text'),('find','search'),('search','search'),
          ('chart','chart'),('candles','chart'),('indicator','chart'),('sma','chart'),('ema','chart'),
          ('rsi','chart'),('bollinger','chart'),('volume','volume'),
          ('preference','settings'),('customize','settings'),('reset','refresh'),
          ('refresh','refresh'),('data','database'),('replay back','undo'),
          ('replay forward','next'),('live','play'),('replay','play'),
          ('next','next'),('watchlist','eye'),('toggle','eye'),
          ('status','info'),('about','info'),('help','help'),('guide','help'),
          ('tip','help'),('update','refresh'),('information','info'),
          ('1m','clock'),('5m','clock'),('15m','clock'),('1d','clock'),
          ('tool','settings'),('drawing','line'),('symbol','search'),
        )
        return next((kind for word,kind in rules if word in name),'generic')

    def _v060_aligned_icon(self, source):
        """Keep a consistent 20x20 icon gutter in every Tk submenu."""
        if source is None:
            source=self._v057_icons.get('generic')
        if source is None:return None
        cache=getattr(self,'_v060_icon_cache',None)
        if cache is None:
            cache={};self._v060_icon_cache=cache
        key=str(source)
        if key in cache:return cache[key]
        try:
            icon=tk.PhotoImage(master=self,width=20,height=20)
            w,h=source.width(),source.height()
            # Tk native menu image dimensions are identical for all entries.
            # Do not stretch icons: centered padding keeps linework sharp.
            x=max(0,(20-w)//2);y=max(0,(20-h)//2)
            icon.tk.call(str(icon),'copy',str(source),'-from',0,0,min(w,20),min(h,20),'-to',x,y)
            cache[key]=icon
            return icon
        except tk.TclError:return source

    def _v057_decorate_menu(self, menu, visited=None):
        if visited is None:visited=set()
        path=str(menu)
        if path in visited:return
        visited.add(path)
        try:end=menu.index('end')
        except tk.TclError:return
        if end is None:return
        for idx in range(end+1):
            try:
                typ=menu.type(idx)
                if typ=='separator':continue
                label=menu.entrycget(idx,'label')
                if typ=='cascade':
                    sub=menu.nametowidget(menu.entrycget(idx,'menu'))
                    self._v057_decorate_menu(sub,visited)
                    # Keep top-level native menu bar labels compact and readable.
                    if menu is self.nametowidget(self['menu']):continue
                icon=self._v060_aligned_icon(self._v057_icons[self._v057_icon_kind(label)])
                menu.entryconfigure(idx,image=icon,compound='left')
            except (tk.TclError,KeyError,AttributeError):continue

    def _v057_install_menu_icons(self):
        # References must remain alive while Tk menus are displayed.
        self._v057_icons={}
        for kind,encoded in OCTOPUS_MENU_ICONS_V064.items():
            try:self._v057_icons[kind]=tk.PhotoImage(master=self,data=encoded)
            except tk.TclError:pass
        self._v057_decorate_menu(self.nametowidget(self['menu']))
    def _v060_platform_foundation(self):
        """Independent host foundation. No third-party code is executed."""
        import os
        # Program files may be read-only. Keep plugins and settings per-user,
        # independent of the .pyw location and Windows installation upgrades.
        # OCTOPUS_HOME is an optional explicit override for portable setups.
        override=os.environ.get('OCTOPUS_HOME','').strip()
        base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'Octopus' / 'Platform'
        self._octopus_home=Path(override).expanduser() if override else base
        try:
            self._octopus_modules=self._octopus_home / 'modules'
            self._octopus_modules.mkdir(parents=True,exist_ok=True)
        except OSError:
            self._octopus_home=base
            self._octopus_modules=self._octopus_home / 'modules'
            self._octopus_modules.mkdir(parents=True,exist_ok=True)
        self._octopus_registry=self._octopus_home / 'modules.json'
        root=self.nametowidget(self['menu'])
        for i in range(root.index('end')+1):
            if root.type(i)=='cascade' and root.entrycget(i,'label')=='Tools':
                tools_menu=root.nametowidget(root.entrycget(i,'menu'))
                tools_menu.add_separator()
                tools_menu.add_command(label='Module Manager...',command=self._v060_module_manager)
                break
        self._v057_decorate_menu(root)

    def _v060_module_manager(self):
        """Inspect module manifests without importing or executing plugin code."""
        win=tk.Toplevel(self)
        win.title(f'Octopus {VERSION} | Module Manager')
        win.geometry('710x390')
        win.minsize(560,310)
        win.transient(self)
        frame=ttk.Frame(win,padding=10);frame.pack(fill='both',expand=True)
        header=ttk.Frame(frame);header.pack(fill='x',pady=(0,7))
        ttk.Label(header,text='Module Manager',font=('Segoe UI',11,'bold')).pack(side='left')
        summary=tk.StringVar(value='Scanning modules...')
        ttk.Label(header,textvariable=summary).pack(side='right')
        cols=('name','version','status')
        table=ttk.Treeview(frame,columns=cols,show='headings',selectmode='browse',height=10)
        for key,heading,width in [('name','Module',315),('version','Version',100),('status','Status',170)]:
            table.heading(key,text=heading);table.column(key,width=width,anchor='w',stretch=(key=='name'))
        scroller=ttk.Scrollbar(frame,orient='vertical',command=table.yview)
        table.configure(yscrollcommand=scroller.set)
        table.pack(side='top',fill='both',expand=True)
        scroller.place(in_=table,relx=1,rely=0,relheight=1,anchor='ne')
        detail=tk.StringVar(value='Modules are never executed automatically.')
        ttk.Label(frame,textvariable=detail,foreground='#555').pack(anchor='w',pady=(7,2))
        def refresh():
            for row in table.get_children():table.delete(row)
            counts={'Installed':0,'Available':0,'Disabled':0,'Invalid':0}
            try:
                folders=sorted((x for x in self._octopus_modules.iterdir() if x.is_dir()),key=lambda x:x.name.lower())
            except OSError:folders=[]
            for folder in folders:
                manifest=folder/'module.json'
                if not manifest.is_file():
                    continue
                try:
                    if manifest.stat().st_size>65536:raise ValueError('Manifest too large')
                    info=json.loads(manifest.read_text(encoding='utf-8'))
                    if not isinstance(info,dict):raise ValueError('Invalid manifest')
                    name=str(info.get('name') or folder.name).strip()[:90]
                    version=str(info.get('version') or '—').strip()[:24]
                    enabled=info.get('enabled',True)
                    if not isinstance(enabled,bool):raise ValueError('Invalid enabled flag')
                    entry=info.get('entrypoint')
                    # An entrypoint is descriptive only. Never import or run it.
                    # Do not follow absolute paths or parent-directory escapes.
                    valid_entry=isinstance(entry,str) and bool(entry.strip()) and not Path(entry).is_absolute() and '..' not in Path(entry).parts
                    if not enabled: status='Disabled'
                    elif valid_entry and (folder/entry).is_file():status='Installed'
                    else:status='Available'
                except (OSError,ValueError,TypeError,UnicodeError):
                    name=folder.name[:90];version='—';status='Invalid'
                counts[status]+=1
                table.insert('', 'end',values=(name,version,status))
            summary.set('  ·  '.join(f'{key}: {counts[key]}' for key in ('Installed','Available','Disabled')))
            if counts['Invalid']:summary.set(summary.get()+f"  ·  Invalid: {counts['Invalid']}")
            if not table.get_children():detail.set('No module manifests found. Add a module folder containing module.json.')
            else:detail.set('Installed = entrypoint file found  |  Available = manifest only  |  Disabled = manifest setting')
        refresh()
        footer=ttk.Frame(frame);footer.pack(fill='x',pady=(8,0))
        def open_modules_folder():
            try:
                import os
                os.startfile(str(self._octopus_modules))
            except Exception as exc:
                messagebox.showerror('Module Manager','Cannot open modules folder: '+str(exc),parent=win)
        def create_test_module():
            # Explicit user action only; never overwrite an existing module.
            folder=self._octopus_modules/'magic-algo-demo'
            if folder.exists():
                messagebox.showinfo('Magic Algo Test Module',
                    'The test module folder already exists. Existing files were not changed.',parent=win)
                refresh();return
            try:
                folder.mkdir(parents=False,exist_ok=False)
                manifest={
                    'id':'magic-algo-demo',
                    'name':'Magic Algo — Integration Test',
                    'version':'0.1.0',
                    'enabled':True,
                    'entrypoint':'demo.py',
                    'description':'Non-trading manifest discovery test; never auto-executed.'
                }
                (folder/'module.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
                (folder/'demo.py').write_text(
                    '# Magic Algo integration test placeholder.\n'
                    '# No trading, credentials, imports or automatic execution.\n',
                    encoding='utf-8')
            except Exception as exc:
                messagebox.showerror('Magic Algo Test Module',str(exc),parent=win)
                return
            refresh()
            for item in table.get_children():
                if table.set(item,'name')==manifest['name']:
                    table.selection_set(item);table.see(item);break
            detail.set('Test module detected. No code has been executed.')
        ttk.Button(footer,text='Open Modules Folder',command=open_modules_folder).pack(side='left')
        ttk.Button(footer,text='Create Test Module',command=create_test_module).pack(side='left',padx=(8,0))
        ttk.Button(footer,text='Close',command=win.destroy).pack(side='right',padx=(5,0))
        ttk.Button(footer,text='Refresh',command=refresh).pack(side='right')

    def _enhance_menus(self):
        menu=self.nametowidget(self['menu'])
        analysis=tk.Menu(menu,tearoff=False)
        for label,var in [('SMA 20',self.show_sma),('EMA 20',self.show_ema),('Volume',self.show_volume),('RSI 14',self.show_rsi),('Bollinger Bands 20, 2',self.show_bbands)]:
            analysis.add_checkbutton(label=label,variable=var,command=self.draw_blank,**({"image":self._tool_icons[label],"compound":"left"} if label in self._tool_icons else {}))
        analysis.add_separator()
        analysis.add_command(label='Refresh historical candles',command=lambda:self.request_bars(force=True))
        analysis.add_command(label='Data source / status',command=self.data_status)
        menu.add_cascade(label='Indicators',menu=analysis)
        # Volume is an opt-in indicator available from Insert as well.
        for idx in range(menu.index('end')+1):
            if menu.type(idx)=='cascade' and menu.entrycget(idx,'label')=='Insert':
                insert_menu=menu.nametowidget(menu.entrycget(idx,'menu'))
                insert_menu.add_separator()
                indicator_menu=tk.Menu(insert_menu,tearoff=False)
                indicator_menu.add_checkbutton(label='Volume',variable=self.show_volume,command=self.draw_blank)
                insert_menu.add_cascade(label='Indicators',menu=indicator_menu)
                break
        replay=tk.Menu(menu,tearoff=False)
        replay.add_command(label='Replay back 10 bars',command=lambda:self.replay_step(-10),image=self._tool_icons.get('Replay back 10 bars'),compound='left')
        replay.add_command(label='Replay forward 1 bar',command=lambda:self.replay_step(1),image=self._tool_icons.get('Replay forward 1 bar'),compound='left')
        replay.add_command(label='LIVE (latest downloaded bar)',command=self.replay_live,image=self._tool_icons.get('LIVE (latest downloaded bar)'),compound='left')
        replay.add_separator()
        replay.add_command(label='Record',command=self._rec_start)
        replay.add_command(label='Stop recording',command=self._rec_stop)
        replay.add_command(label='Share recording',command=self._rec_share)
        menu.add_cascade(label='Replay',menu=replay)
        # Dynamic window listing: the active sheet's open charts are rebuilt on opening.
        for i in range(menu.index('end')+1):
            if menu.type(i)=='cascade' and menu.entrycget(i,'label')=='Window':
                window_menu=menu.nametowidget(menu.entrycget(i,'menu'))
                break
        else:return
        def rebuild():
            window_menu.delete(0,'end')
            for label,cmd in [('New Chart',lambda:self.new_chart(self.symbol.get().strip() or 'NIFTY')),('Close Chart',self.close_active),('Next Chart',self.next_chart),('Toggle Watchlist',self.toggle_watchlist)]:
                window_menu.add_command(label=label,command=cmd)
            window_menu.add_separator()
            for idx,chart in enumerate(self.sheets.get(self.active_sheet,[])):
                window_menu.add_command(label=('✓ ' if idx==self.active_index else '   ')+f'{idx+1}  {chart}',command=lambda j=idx:self.activate(j))
            self._v057_decorate_menu(window_menu)
        window_menu.configure(postcommand=rebuild)

    def _chart_buttons(self):
        self._replay_playing=False
        self._replay_job=None
        self._replay_speed=tk.StringVar(master=self,value='1x')
        self._replay_position=tk.IntVar(master=self,value=1000)
        self._replay_sync=False
        self._dock_init()

    def _dock_init(self):
        import os
        from pathlib import Path
        self._dock_file=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'Octopus' / 'module_docking.json'
        self._dock_file.parent.mkdir(parents=True,exist_ok=True)
        self._dock_state={'Recorder & Replay':'top'}
        self._dock_order=['Recorder & Replay']
        try:
            import json
            saved=json.loads(self._dock_file.read_text(encoding='utf-8'))
            old=saved.get('positions',{})
            where=old.get('Recorder & Replay',old.get('Flight Recorder','top'))
            if where in ('top','bottom','left','right','floating','hidden'):
                self._dock_state['Recorder & Replay']=where
        except Exception:pass
        self._dock_hosts={}
        self._dock_hosts['top']=tk.Frame(self.main_toolbar,bg=BAR)
        self._dock_hosts['top'].pack(side='left',padx=3)
        self._dock_hosts['bottom']=tk.Frame(self,bg=BAR,height=28)
        self._dock_hosts['bottom'].pack(side='top',fill='x',before=self.chart_frame)
        self._dock_hosts['left']=tk.Frame(self.chart_frame,bg=BAR)
        self._dock_hosts['left'].pack(side='left',fill='y',before=self.canvas)
        self._dock_hosts['right']=tk.Frame(self.chart_frame,bg=BAR)
        self._dock_hosts['right'].pack(side='right',fill='y',before=self.drawing_toolbar)
        self._dock_widgets={}
        self._dock_windows={}
        self._dock_drag=None
        self._dock_ghost=None
        # Capture pointer motion and release even after it leaves the grip widget.
        self.bind_all('<B1-Motion>',self._dock_drag_motion,add='+')
        self.bind_all('<ButtonRelease-1>',self._dock_global_release,add='+')
        self._dock_render()
        menu=tk.Menu(self,tearoff=False)
        for name in self._dock_order:
            sub=tk.Menu(menu,tearoff=False)
            for loc in ('top','bottom','left','right','floating','hidden'):
                sub.add_command(label=loc.title(),command=lambda n=name,l=loc:self._dock_move(n,l))
            menu.add_cascade(label=name,menu=sub)
        menu.add_separator()
        menu.add_command(label='Reset Layout',command=self._dock_reset)
        self._dock_module_menu=menu

    def _dock_save(self):
        import json
        try:
            self._dock_file.write_text(json.dumps({'positions':self._dock_state,'order':self._dock_order},indent=2),encoding='utf-8')
        except Exception:pass

    def _dock_render(self):
        for name,frame in list(self._dock_widgets.items()):
            try:frame.destroy()
            except Exception:pass
        self._dock_widgets={}
        for name,win in list(self._dock_windows.items()):
            try:win.destroy()
            except Exception:pass
        self._dock_windows={}
        for name in self._dock_order:
            where=self._dock_state[name]
            if where=='hidden':continue
            if where=='floating':
                host=tk.Toplevel(self)
                host.title('Octopus — '+name)
                host.resizable(True,False)
                host.protocol('WM_DELETE_WINDOW',lambda n=name:self._dock_move(n,'top'))
                self._dock_windows[name]=host
            else:host=self._dock_hosts[where]
            frame=tk.Frame(host,bg='#23364e',bd=1,relief='ridge')
            frame.pack(side='top' if where in ('left','right') else 'left',padx=2,pady=1,anchor='nw')
            self._dock_widgets[name]=frame
            grip=tk.Label(frame,text='⠿',bg='#49617f',fg='white',cursor='fleur',
                          font=('Segoe UI',10,'bold'),padx=4)
            grip.pack(side='top' if where in ('left','right') else 'left')
            grip.bind('<ButtonPress-1>',lambda e,n=name:self._dock_drag_start(e,n))
            grip.bind('<ButtonRelease-1>',lambda e,n=name:self._dock_drag_end(e,n))
            grip.bind('<B1-Motion>',self._dock_drag_motion)
            grip.bind('<Button-3>',lambda e,n=name:self._dock_menu(e,n))
            title=tk.Label(frame,text='REPLAY',
                           bg='#23364e',fg='#dbe7f8',font=('Segoe UI',8,'bold'))
            title.pack(side='top' if where in ('left','right') else 'left',padx=3)
            title.bind('<Button-3>',lambda e,n=name:self._dock_menu(e,n))
            def button(t,fn):
                b=tk.Button(frame,text=t,command=fn,relief='flat',bg='#27374c',fg='white',
                            font=('Segoe UI',9),padx=4)
                b.pack(side='top' if where in ('left','right') else 'left',padx=1)
                return b
            self._rec_btn=button('● REC',self._rec_start)
            button('SHARE',self._rec_share_or_finish)
            self._rec_copy_label=tk.Label(frame,text=getattr(self,'_rec_copy_status','NOT COPIED'),bg='#23364e',fg='#ff8585',font=('Segoe UI',8,'bold'))
            self._rec_copy_label.pack(side='top' if where in ('left','right') else 'left',padx=4)
            self._rec_time_label=tk.Label(frame,text=self._rec_clock_text(),
                bg='#23364e',fg='#dbe7f8',font=('Consolas',9,'bold'))
            self._rec_time_label.pack(side='top' if where in ('left','right') else 'left',padx=5)
            sep=tk.Frame(frame,width=2,height=18,bg='#71849b')
            sep.pack(side='top' if where in ('left','right') else 'left',padx=4,pady=2)
            combo=ttk.Combobox(frame,textvariable=self._replay_speed,
                 values=('0.25x','0.5x','1x','2x','5x','10x'),width=5,state='readonly')
            combo.pack(side='top' if where in ('left','right') else 'left',padx=2)
            button('LIVE',self.replay_live)
            self._replay_slider=tk.Scale(frame,from_=0,to=1000,orient='horizontal',
                variable=self._replay_position,showvalue=False,length=90,width=7,
                sliderlength=13,highlightthickness=0,bd=0,bg='#172334',
                troughcolor='#455d76',command=self._seek_replay)
            self._replay_slider.pack(side='top' if where in ('left','right') else 'left',padx=2)
        for loc in ('bottom','left','right'):
            host=self._dock_hosts[loc]
            if any(self._dock_state[n]==loc for n in self._dock_order):
                if not host.winfo_manager():
                    if loc=='bottom':host.pack(side='top',fill='x',before=self.chart_frame)
                    elif loc=='left':host.pack(side='left',fill='y',before=self.canvas)
                    else:host.pack(side='right',fill='y',before=self.drawing_toolbar)
            else:host.pack_forget()
        self._dock_save()

    def _dock_move(self,name,where):
        if getattr(self,'_replay_playing',False):
            self._stop_replay_play()
        self._dock_state[name]=where
        self._dock_render()

    def _dock_menu(self,event,name):
        menu=tk.Menu(self,tearoff=False)
        for where in ('top','bottom','left','right','floating','hidden'):
            menu.add_command(label=('✓ ' if self._dock_state[name]==where else '   ')+where.title(),
                             command=lambda w=where:self._dock_move(name,w))
        menu.add_separator()
        menu.add_command(label='Reset all toolbars',command=self._dock_reset)
        menu.tk_popup(event.x_root,event.y_root)
        menu.grab_release()

    def _dock_reset(self):
        self._dock_state={'Recorder & Replay':'top'}
        self._dock_order=['Recorder & Replay']
        self._dock_render()

    def _dock_drag_start(self,event,name):
        self._dock_drag=(name,event.x_root,event.y_root)
        try:
            ghost=tk.Toplevel(self)
            ghost.overrideredirect(True)
            ghost.attributes('-topmost',True)
            tk.Label(ghost,text='⠿  '+name+'  — drop to dock',bg='#2d527d',
                     fg='white',padx=12,pady=7,font=('Segoe UI',10,'bold')).pack()
            ghost.geometry(f'+{event.x_root+12}+{event.y_root+12}')
            self._dock_ghost=ghost
        except Exception:
            self._dock_ghost=None

    def _dock_drag_motion(self,event):
        if not self._dock_drag:return
        if self._dock_ghost:
            try:self._dock_ghost.geometry(f'+{event.x_root+12}+{event.y_root+12}')
            except Exception:pass

    def _dock_global_release(self,event):
        if self._dock_drag:
            self._dock_drag_end(event,self._dock_drag[0])

    def _dock_drag_end(self,event,name):
        drag=self._dock_drag
        self._dock_drag=None
        if self._dock_ghost:
            try:self._dock_ghost.destroy()
            except Exception:pass
            self._dock_ghost=None
        if not drag or drag[0]!=name:return
        x,y=event.x_root,event.y_root
        if abs(x-drag[1])+abs(y-drag[2])<15:return
        # Check the other module first to allow reordering.
        for other,frame in list(self._dock_widgets.items()):
            if other==name or self._dock_state[other]=='floating':continue
            if frame.winfo_rootx()<=x<=frame.winfo_rootx()+frame.winfo_width() and frame.winfo_rooty()<=y<=frame.winfo_rooty()+frame.winfo_height():
                self._dock_order.remove(name)
                self._dock_order.insert(self._dock_order.index(other),name)
                self._dock_state[name]=self._dock_state[other]
                self._dock_render()
                return
        rootx=self.winfo_rootx();rooty=self.winfo_rooty()
        width=self.winfo_width();height=self.winfo_height()
        # Top toolbar is roughly 85px; bottom/side dock zones are generous.
        if rootx<=x<=rootx+width and rooty<=y<=rooty+115:
            self._dock_move(name,'top')
        elif rootx<=x<=rootx+width and rooty+height-140<=y<=rooty+height:
            self._dock_move(name,'bottom')
        elif rootx<=x<=rootx+130 and rooty<=y<=rooty+height:
            self._dock_move(name,'left')
        elif rootx+width-130<=x<=rootx+width and rooty<=y<=rooty+height:
            self._dock_move(name,'right')
        else:
            self._dock_move(name,'floating')

    def _capture_controls(self):
        self._recording=False;self._last_recording=None;self._rec_job=None
        self._rec_temp=None;self._rec_count=0
        self._rec_started_at=None;self._rec_started_stamp=None
        self._rec_finished_duration=0
        self._rec_copy_status='NOT COPIED'
        self.after(1000,self._rec_clock_tick)

    def _rec_clock_text(self):
        from datetime import datetime
        import time
        if getattr(self,'_recording',False) and getattr(self,'_rec_started_at',None) is not None:
            elapsed=max(0,int(time.monotonic()-self._rec_started_at))
            stamp=self._rec_started_stamp or datetime.now()
            return f'● {stamp:%d-%m-%Y %I:%M:%S %p}  {elapsed//3600:02d}:{elapsed//60%60:02d}:{elapsed%60:02d}'
        if getattr(self,'_rec_started_stamp',None) is not None:
            elapsed=self._rec_finished_duration
            return f'{self._rec_started_stamp:%d-%m-%Y %I:%M:%S %p}  {elapsed//3600:02d}:{elapsed//60%60:02d}:{elapsed%60:02d}'
        return datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')+'  00:00:00'

    def _rec_clock_tick(self):
        try:
            if hasattr(self,'_rec_time_label') and self._rec_time_label.winfo_exists():
                self._rec_time_label.config(text=self._rec_clock_text(),
                    fg='#ff7070' if getattr(self,'_recording',False) else '#dbe7f8')
            self.after(1000,self._rec_clock_tick)
        except tk.TclError:
            pass

    def _seek_replay(self,value):
        if getattr(self,'_replay_sync',False):return
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        if not rows:return
        self._stop_replay_play()
        v=max(0,min(1000,int(float(value))))
        self.replay_count=max(1,min(len(rows),1+round((len(rows)-1)*v/1000)))
        if v>=1000:self.replay_count=None
        self.pan_fraction=1.0
        self.draw_blank()

    def _sync_replay_position(self):
        if not hasattr(self,'_replay_slider'):return
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        total=len(rows)
        if not total:return
        pos=total if self.replay_count is None else min(total,self.replay_count)
        v=round(1000*(pos-1)/max(1,total-1))
        self._replay_sync=True
        try:self._replay_position.set(v)
        finally:self._replay_sync=False

    def _stop_replay_play(self):
        self._replay_playing=False
        job=getattr(self,'_replay_job',None)
        if job is not None:
            try:self.after_cancel(job)
            except Exception:pass
        self._replay_job=None

    def _toggle_replay_play(self):
        if self._replay_playing:
            self._stop_replay_play();return
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        if not rows:return
        if self.replay_count is None:self.replay_count=max(1,len(rows)-60)
        self._replay_playing=True
        if hasattr(self,'_play_button'):
            self._play_button.configure(text='Ⅱ PAUSE')
        self._replay_advance()

    def _replay_advance(self):
        if not self._replay_playing:return
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        if not rows or self.replay_count is None or self.replay_count>=len(rows):
            self._stop_replay_play();return
        self.replay_count+=1
        self.pan_fraction=1.0
        self._sync_replay_position()
        self.draw_blank()
        speed={'0.25x':0.25,'0.5x':0.5,'1x':1,'2x':2,'5x':5,'10x':10}.get(self._replay_speed.get(),1)
        self._replay_job=self.after(max(40,round(1000/speed)),self._replay_advance)

    def _rec_replay(self):
        # Recording playback is separate from historical candle replay.
        import os
        path=getattr(self,'_last_recording',None)
        if path and Path(path).is_file():
            try:os.startfile(str(path))
            except Exception as exc:messagebox.showerror('Flight Recorder',str(exc))
        else:
            messagebox.showinfo('Flight Recorder','Record and STOP to save a video before replaying it.')

    def _rec_start(self):
        if self._recording:
            self._rec_stop()
            return
        try:from PIL import ImageGrab
        except ImportError:
            messagebox.showerror('Recorder','Pillow required: py -m pip install Pillow');return
        import tempfile
        self._rec_temp=tempfile.TemporaryDirectory(prefix='octopus_record_')
        import time
        from datetime import datetime
        self._rec_started_at=time.monotonic()
        self._rec_started_stamp=datetime.now()
        self._rec_finished_duration=0
        self._rec_count=0;self._recording=True
        self._rec_btn.config(bg='#9f2635',text='● REC ON')
        self._rec_tick()
    def _rec_tick(self):
        if not self._recording:return
        try:
            from PIL import ImageGrab
            x,y=self.winfo_rootx(),self.winfo_rooty()
            frame=ImageGrab.grab(bbox=(x,y,x+self.winfo_width(),y+self.winfo_height()),all_screens=True)
            frame.thumbnail((1280,900))
            frame.convert('RGB').save(Path(self._rec_temp.name)/f'{self._rec_count:08d}.png')
            self._rec_count+=1
        except Exception as exc:
            self._recording=False;self._rec_btn.config(bg='#27374c',text='● REC')
            if self._rec_temp:self._rec_temp.cleanup();self._rec_temp=None
            messagebox.showerror('Recorder',str(exc));return
        # No duration limit: capture to disk rather than accumulating frames in RAM.
        self._rec_job=self.after(250,self._rec_tick)    def _rec_stop(self):
        if not self._recording:return
        import time
        if self._rec_started_at is not None:
            self._rec_finished_duration=max(0,int(time.monotonic()-self._rec_started_at))
        self._recording=False;self._rec_btn.config(bg='#27374c',text='● REC')
        self._rec_set_copy_status('ENCODING…', '#eacb75')
        try:self.after_cancel(self._rec_job)
        except Exception:pass
        self._rec_job=None
        if not self._rec_count:return
        import shutil,subprocess
        from datetime import datetime
        output_dir=Path.home()/'Videos'/'Octopus';output_dir.mkdir(parents=True,exist_ok=True)
        stem='Octopus_'+datetime.now().strftime('%Y%m%d_%H%M%S')
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
            except (ImportError, OSError):
                ffmpeg=None
        output=None
        folder=Path(self._rec_temp.name)
        try:
            if not ffmpeg:
                # Preserve the frames instead of silently downgrading an MP4 request to GIF.
                import shutil as _shutil
                retained=output_dir/(stem+'_frames')
                _shutil.copytree(folder,retained)
                messagebox.showwarning(
                    'MP4 encoder required',
                    'Recording frames were preserved at:\\n'+str(retained)+
                    '\\n\\nInstall the MP4 encoder once using:\\n'
                    'py -m pip install imageio-ffmpeg\\n\\n'
                    'Then start a new recording. No GIF fallback was generated.')
                return
            output=output_dir/(stem+'.mp4')
            # H.264/yuv420p requires even frame dimensions. Some window sizes
            # produce odd-width PNGs; pad without stretching the chart.
            common=[ffmpeg,'-y','-hide_banner','-loglevel','error',
                    '-framerate','4','-i',str(folder/'%08d.png'),
                    '-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2',
                    '-pix_fmt','yuv420p','-movflags','+faststart']
            errors=[]
            for codec,options in (
                ('libx264',['-preset','ultrafast','-crf','26']),
                ('mpeg4',['-q:v','5']),
            ):
                try:
                    command=common+['-c:v',codec]+options+[str(output)]
                    result=subprocess.run(command,capture_output=True,text=True,
                        timeout=max(180,round(self._rec_count/4)*5),
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    if result.returncode==0 and output.is_file() and output.stat().st_size>1024:
                        break
                    errors.append(codec+': '+(result.stderr or result.stdout or
                                  'exit code '+str(result.returncode))[-900:])
                except Exception as encode_error:
                    errors.append(codec+': '+str(encode_error))
            else:
                raise RuntimeError('FFmpeg could not encode the recording.\n'+
                                   '\n'.join(errors))
            if not output.is_file() or output.stat().st_size==0:
                raise RuntimeError('MP4 encoder did not produce a valid file.')
            self._last_recording=str(output)
        except Exception as exc:
            try:
                retained=output_dir/(stem+'_frames')
                shutil.copytree(folder,retained)
                extra='\\nFrames preserved: '+str(retained)
            except Exception:extra=''
            self._rec_set_copy_status('MP4 FAILED', '#ff8585')
            messagebox.showerror('MP4 recording failed',str(exc)+extra)
            return
        finally:
            if self._rec_temp:self._rec_temp.cleanup();self._rec_temp=None
        self._rec_share()
    def _rec_set_copy_status(self, message, color='#dbe7f8'):
        self._rec_copy_status=message
        label=getattr(self,'_rec_copy_label',None)
        if label is not None:
            try:label.config(text=message,fg=color)
            except tk.TclError:pass
        try:self.update_idletasks()
        except tk.TclError:pass

    def _rec_share_or_finish(self):
        """SHARE finishes an active capture, encodes MP4 and copies it."""
        if getattr(self, '_recording', False):
            self._rec_stop()  # _rec_stop automatically calls _rec_share on success.
        else:
            self._rec_share()

    def _rec_share(self):
        """Copy the saved recording as a Windows file-drop clipboard object."""
        import os, subprocess, base64
        path=os.path.abspath(str(getattr(self,'_last_recording','') or ''))
        if not os.path.isfile(path):
            self._rec_set_copy_status('NO RECORDING', '#ff8585')
            messagebox.showinfo('Share','Record and STOP first.')
            return
        if os.name!='nt':
            self._rec_set_copy_status('COPY FAILED', '#ff8585')
            messagebox.showerror('Share','Windows file clipboard is required.')
            return
        # PowerShell STA + WinForms uses the same native file-drop format as Explorer Copy.
        # Base64-encode the file name to avoid shell quoting/injection issues.
        encoded=base64.b64encode(path.encode('utf-16le')).decode('ascii')
        script=(
            'Add-Type -AssemblyName System.Windows.Forms; '
            '$p=[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String("'+encoded+'")); '
            '$list=New-Object System.Collections.Specialized.StringCollection; '
            '[void]$list.Add($p); '
            '$ok=$false; for($i=0;$i -lt 6;$i++){ try { '
            '[System.Windows.Forms.Clipboard]::SetFileDropList($list); '
            '$got=[System.Windows.Forms.Clipboard]::GetFileDropList(); '
            'if($got.Count -eq 1 -and $got[0] -eq $p){$ok=$true;break} '
            '} catch {} Start-Sleep -Milliseconds 150 }; '
            'if(-not $ok){exit 3}; exit 0'
        )
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        try:
            result=subprocess.run(
                ['powershell.exe','-NoProfile','-NonInteractive','-STA','-Command',script],
                capture_output=True,text=True,timeout=12,creationflags=flags)
            if result.returncode:
                detail=(result.stderr or result.stdout or 'Clipboard verification failed').strip()
                raise RuntimeError(detail[:350])
        except Exception as exc:
            self._rec_set_copy_status('COPY FAILED', '#ff8585')
            messagebox.showerror('Share failed',
                'Could not copy the recording as a Windows file.\n'+str(exc))
            return
        # Persistent visual confirmation, without a modal popup or opening Explorer.
        self._rec_set_copy_status('✓ COPIED MP4', '#55ef92')
        try:self.status_var.set('Copied: '+os.path.basename(path)+' | Ctrl+V to paste')
        except Exception:pass

    def _rec_open_folder(self):
        import os,subprocess
        path=getattr(self,'_last_recording',None)
        if path and os.path.isfile(path):
            try:subprocess.Popen(['explorer.exe','/select,',os.path.normpath(path)])
            except Exception as exc:messagebox.showerror('Open recording folder',str(exc))

    TYPES=('Candles','Heikin Ashi','Line','Area','OHLC','Order Flow','Footprint','TPO','Volume Profile','Renko')
    def _chart_type_control(self):
        if not hasattr(self,'kind_var'):self.kind_var=tk.StringVar(value='Candles')
        if hasattr(self,'kind_selector') and self.kind_selector.winfo_exists():
            self.kind_selector.destroy()
        selector=ttk.Combobox(self.main_toolbar,textvariable=self.kind_var,values=self.TYPES,width=15,state='readonly')
        selector.pack(side='left',padx=5,pady=1)
        selector.bind('<<ComboboxSelected>>',self._change_chart_type)
        self.kind_selector=selector
    def _change_chart_type(self,event=None):
        """Change the active tab in place; only + creates a chart."""
        if not self.active_chart:return
        kind=self.kind_var.get()
        old=self.active_chart
        base,_=self._parts(old)
        labels=self.sheets[self.active_sheet]
        target=base if kind=='Candles' else base+' | '+kind
        # Preserve other tabs even when their symbol and chart type match.
        if target in labels and target != old:
            n=2
            while f'{target} #{n}' in labels:n+=1
            target=f'{target} #{n}'
        index=self.active_index
        if index<0 or index>=len(labels) or labels[index]!=old:
            index=labels.index(old)
        if target!=old:
            labels[index]=target
            key=(self.active_sheet,old)
            new_key=(self.active_sheet,target)
            if key in self.tab_timeframes:self.tab_timeframes[new_key]=self.tab_timeframes.pop(key)
            if key in self.tab_views:self.tab_views[new_key]=self.tab_views.pop(key)
        self.active_chart=target
        self.active_index=index
        self.refresh_tabs()
        self.draw_blank()

    def _parts(self,label):
        import re
        bits=(label or '').split(' | ',1)
        kind=bits[1] if len(bits)>1 else 'Candles'
        kind=re.sub(r' #\d+$','',kind)
        return bits[0],kind
    def _timeframe_changed(self):
        if self._changing_tab:return
        if self.active_chart:self.tab_timeframes[(self.active_sheet,self.active_chart)]=self.tf.get()
        self.replay_count=None
        self.pan_fraction=1.0
        if hasattr(self,'hscroll'):
            self._slider_sync=True;self.hscroll.set(1000);self._slider_sync=False
        self._remember_view()
        self.request_bars()
    def _set_tab_timeframe(self):
        if not self.active_chart:return
        tf=self.tab_timeframes.get((self.active_sheet,self.active_chart),'1m')
        self._changing_tab=True
        try:self.tf.set(tf)
        finally:self._changing_tab=False
    def _yahoo_symbol(self,symbol):
        x=symbol.strip().upper()
        if x in self.SYMBOL_MAP:return self.SYMBOL_MAP[x]
        if x.startswith('^') or '.' in x:return x
        return x+'.NS'
    def _feed_status_tick(self):
        """Show green blinking only for a recently responding data connection."""
        try:
            import time
            fresh=(self._last_feed_success>0 and time.monotonic()-self._last_feed_success<10
                   and self._refresh_failures==0)
            self._feed_blink_on=not self._feed_blink_on
            if fresh:
                self.feed_text.configure(text='DATA CONNECTED')
                self.feed_led.itemconfigure(self.feed_led_dot,
                    fill='#00d94d' if self._feed_blink_on else '#245b39',
                    outline='#008e39' if self._feed_blink_on else '#245b39')
            else:
                self.feed_text.configure(text='DATA DISCONNECTED')
                self.feed_led.itemconfigure(self.feed_led_dot,fill='#d92323',outline='#842020')
        finally:
            if self.winfo_exists():self.after(500,self._feed_status_tick)

    def _auto_refresh_tick(self):
        """Nonblocking delayed-feed polling. Only active chart is fetched."""
        if not getattr(self,'_auto_refresh_enabled',False):return
        try:
            if self.active_chart and self.replay_count is None:
                import time
                now=time.monotonic()
                if now-self._last_network_refresh_at>=self._network_refresh_interval_s:
                    self._last_network_refresh_at=now
                    self.request_bars(force=True)
        except Exception as exc:
            self.info.set(f'{VERSION} | Refresh scheduler: {str(exc)[:90]}')
        finally:
            if getattr(self,'_auto_refresh_enabled',False):
                self.after(self._auto_refresh_interval_ms,self._auto_refresh_tick)

    def request_bars(self,force=False):
        if not self.active_chart:return
        sym,_=self._parts(self.active_chart)
        tf=self.tf.get()
        key=(sym,tf)
        if key in self.bars_cache and not force:self.draw_blank();return
        if key in self.loading:return
        self.loading.add(key);self.errors.pop(key,None)
        self.info.set(f'{VERSION} | Updating data | {sym} {tf} | Orders disabled')
        def work():
            try:
                intervals={'1m':('1m','7d'),'5m':('5m','60d'),'9m':('1m','7d'),'15m':('15m','60d'),
                           '30m':('30m','60d'),'60m':('60m','730d'),'1D':('1d','2y')}
                interval,period=intervals.get(tf,('1d','2y'))
                query=urllib.parse.urlencode({'interval':interval,'range':period,'includePrePost':'false'})
                url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(self._yahoo_symbol(sym),safe='')+'?'+query
                req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 MagicAlgoPro/017','Accept':'application/json'})
                with urllib.request.urlopen(req,timeout=12) as resp:
                    obj=json.load(resp)
                result=obj['chart']['result'][0];quote=result['indicators']['quote'][0]
                rows=[]
                for i,ts in enumerate(result['timestamp']):
                    o,h,l,c=[quote[k][i] for k in ('open','high','low','close')]
                    if None in (o,h,l,c):continue
                    rows.append((int(ts),float(o),float(h),float(l),float(c),float(quote['volume'][i] or 0)))
                if not rows:raise ValueError('Data source returned no valid candles')
                rows=self._canonical_candles(rows,interval if tf=='9m' else tf)
                if tf=='9m':
                    rows=self._resample_session(rows,9)
                    if not rows:raise ValueError('No 1-minute session bars available to construct 9m candles')
                rows=self._canonical_candles(rows,tf)
                self.after(0,lambda:self._loaded(key,rows,None))
            except Exception as exc:
                self.after(0,lambda msg=str(exc):self._loaded(key,None,msg))
        threading.Thread(target=work,daemon=True).start()
    def _loaded(self,key,rows,error):
        self.loading.discard(key)
        if error:
            self.errors[key]=error
            self._refresh_failures=min(getattr(self,'_refresh_failures',0)+1,6)
            # Gradually reduce network traffic if Yahoo is unavailable/rate limiting.
            self._network_refresh_interval_s=min(60.0,0.1*(2.0**self._refresh_failures))
        else:
            self._refresh_failures=0
            import time
            self._last_feed_success=time.monotonic()
            self._network_refresh_interval_s=0.1
            rows=self._canonical_candles(rows,key[1])
            previous=self.bars_cache.get(key)
            if previous:
                normalized=self._canonical_candles(previous,key[1])
                if normalized!=previous:
                    previous=normalized
                    self.bars_cache[key]=normalized
            # V078 NON-REPAINT POLICY: The data provider can revise earlier OHLCV
            # bars on each response. During automatic refresh preserve all bars
            # already seen, except the still-forming latest bar. When a new
            # timestamp arrives the former latest bar becomes immutable.
            # A manual refresh or newly opened chart can still fetch fresh history.
            if previous and rows and key in self.bars_cache:
                previous_by_ts={bar[0]:bar for bar in previous}
                latest_seen=previous[-1][0]
                incoming_latest=rows[-1][0]
                if incoming_latest >= latest_seen:
                    merged=[]
                    for bar in rows:
                        ts=bar[0]
                        if ts in previous_by_ts and (ts<latest_seen or ts<incoming_latest):
                            old_bar=previous_by_ts[ts]
                            # The fast feed can initially return an incomplete
                            # OHLC snapshot (O=H=L=C). Do not freeze such a
                            # placeholder forever. Replace it only when the
                            # provider supplies a genuine non-zero candle range.
                            old_flat=(abs(old_bar[2]-old_bar[3])<1e-9)
                            new_has_range=(bar[2]-bar[3])>1e-9
                            if old_flat and new_has_range:
                                merged.append(bar)
                            else:
                                merged.append(old_bar)
                        else:
                            merged.append(bar)
                    # Retain bars omitted by the latest partial provider response.
                    merged_ts={bar[0] for bar in merged}
                    merged.extend(bar for bar in previous if bar[0] not in merged_ts)
                    rows=sorted(merged,key=lambda bar:bar[0])
                else:
                    # Ignore a stale response that would roll back the chart.
                    rows=previous
            # Fast path for the overwhelmingly common unchanged 100ms response.
            # Verify the full series only when the last bar matches, so historical
            # corrections are still detected and persisted.
            if previous is rows:
                changed=False
            elif previous is None or len(previous)!=len(rows) or previous[-1]!=rows[-1]:
                changed=True
            else:
                changed=(previous!=rows)
            # Preserve the same visible rightmost candle while browsing history.
            # A fractional scrollbar otherwise shifts the chart whenever Yahoo
            # extends its returned history by one bar.
            active_key=(self._parts(self.active_chart)[0],self.tf.get()) if self.active_chart else None
            if changed and previous and active_key==key and self.pan_fraction<0.9995 and self.replay_count is None:
                count=max(25,min(600,int(self.prefs['visible_bars'])+self.zoom_level*14))
                old_end=min(len(previous),max(1,count+round(max(0,len(previous)-count)*self.pan_fraction)))
                old_stamp=previous[old_end-1][0]
                new_index=next((i for i,b in enumerate(rows) if b[0]==old_stamp),None)
                if new_index is not None:
                    new_end=new_index+1
                    self.pan_fraction=max(0.0,min(1.0,(new_end-count)/max(1,len(rows)-count)))
                    self._remember_view()
                    if hasattr(self,'hscroll'):
                        self._slider_sync=True
                        try:self.hscroll.set(round(self.pan_fraction*1000))
                        finally:self._slider_sync=False
            if changed:
                self.bars_cache[key]=rows
            # High-frequency polling must not write unchanged OHLCV history to SQLite.
            if changed or key not in getattr(self,'_canonical_db_cleaned',set()):
                try:
                    self._persist_downloaded_bars(key,rows)
                    if not hasattr(self,'_canonical_db_cleaned'):self._canonical_db_cleaned=set()
                    self._canonical_db_cleaned.add(key)
                except Exception as exc:self.errors[key]='Database save warning: '+str(exc)[:90]
            while len(self.bars_cache)>self.prefs['cache_symbols']:
                self.bars_cache.pop(next(iter(self.bars_cache)))
        if self.active_chart and (self._parts(self.active_chart)[0],self.tf.get())==key:
            if not error and changed:self.draw_blank()
            if error:self.info.set(f'{VERSION} | Data unavailable: '+error[:70]+f' | Retry in {self._network_refresh_interval_s:g}s | Cached chart')
            else:
                import datetime as _dt
                stamp=_dt.datetime.fromtimestamp(rows[-1][0],_dt.timezone(_dt.timedelta(hours=5,minutes=30))).strftime('%d-%m %H:%M')
                self.info.set(f'{VERSION} | {key[0]} {key[1]} | Last candle {stamp} IST | Delayed data | {len(rows)} bars | Orders disabled')
    def new_chart(self,sym):
        base=self._parts(sym.strip().upper())[0] or 'NIFTY'
        kind=self.kind_var.get() if hasattr(self,'kind_var') else 'Candles'
        root=base if kind=='Candles' else base+' | '+kind
        existing=self.sheets[self.active_sheet]
        label=root
        number=2
        while label in existing:
            label=(base+' | '+kind+' #'+str(number))
            number+=1
        existing.append(label)
        self.active_index=len(existing)-1
        self.active_chart=label
        self.tab_timeframes[(self.active_sheet,label)]=self.tf.get()
        self.tab_views[(self.active_sheet,label)]=(1.0,0.0)
        self.refresh_tabs();self.draw_blank()
        self.symbol.set(base)
        self.replay_count=None;self._restore_view();self.request_bars()
    def refresh_tabs(self):
        super().refresh_tabs()
        # Chart type selector remains in the main toolbar when tabs refresh.
    def activate(self,i):
        super().activate(i)
        base,kind=self._parts(self.active_chart)
        self.symbol.set(base)
        self.kind_var.set(kind)
        self._set_tab_timeframe()
        self._restore_view()
        self.replay_count=None;self.request_bars()
    def show_sheet(self,s):
        super().show_sheet(s)
        if hasattr(self,'bars_cache') and self.active_chart:
            self._set_tab_timeframe()
            self.request_bars()
    def save_workspace(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Magic Algo Workspace','*.json')])
        if not path:return
        try:
            payload={'sheets':self.sheets,'active_sheet':self.active_sheet,'timeframe':self.tf.get(),
                     'drawings':self.shapes,'drawing_meta':self.drawing_meta,'tab_timeframes':[
                         [sheet,label,tf] for (sheet,label),tf in self.tab_timeframes.items()]}
            with open(path,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
            self.info.set('Workspace saved: '+path)
        except Exception as e:messagebox.showerror('Save failed',str(e))
    def open_workspace(self):
        path=filedialog.askopenfilename(filetypes=[('Magic Algo Workspace','*.json')])
        if not path:return
        try:
            with open(path,encoding='utf-8') as f:data=json.load(f)
            sheets=data['sheets']
            if not isinstance(sheets,dict) or not sheets or not all(isinstance(v,list) and all(isinstance(x,str) for x in v) for v in sheets.values()):raise ValueError('Invalid workspace')
            self.sheets=sheets
            self.active_sheet=data.get('active_sheet','Sheet 1')
            if self.active_sheet not in sheets:self.active_sheet=next(iter(sheets))
            self.tab_timeframes={(a,b):c for a,b,c in data.get('tab_timeframes',[]) if isinstance(a,str) and isinstance(b,str) and c in ('1m','5m','9m','15m','30m','60m','1D')}
            self.shapes={k:[tuple(item) for item in v] for k,v in data.get('drawings',{}).items() if isinstance(v,list)}
            self.drawing_meta=data.get('drawing_meta',{}) if isinstance(data.get('drawing_meta'),dict) else {}
            self.rebuild_sheets();self.show_sheet(self.active_sheet)
        except Exception as e:messagebox.showerror('Open failed',str(e))
    def replay_step(self,delta):
        self._stop_replay_play()
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        if not rows:return
        current=self.replay_count if self.replay_count is not None else len(rows)
        self.replay_count=max(20,min(len(rows),current+delta))
        self._sync_replay_position()
        self.draw_blank()
    def replay_live(self):
        self._stop_replay_play()
        self.replay_count=None
        self.pan_fraction=1.0
        if hasattr(self,'hscroll'):
            self._slider_sync=True;self.hscroll.set(1000);self._slider_sync=False
        self._sync_replay_position()
        self._remember_view();self.draw_blank()
        # On return to LIVE reconcile any candles which were received as
        # incomplete placeholders while replay was active.
        self.request_bars(force=True)
    def data_status(self):
        key=(self._parts(self.active_chart)[0],self.tf.get())
        rows=self.bars_cache.get(key,[])
        messagebox.showinfo('Historical Data',f'Source: Yahoo Finance chart endpoint (unofficial)\nSymbol: {key[0]}\nTimeframe: {key[1]}\nDownloaded bars: {len(rows)}\nStatus: {self.errors.get(key,"historical data only" if rows else "not loaded")}\n\nNot an exchange-authorized live feed. Quotes may be delayed.\nBroker execution remains disabled.')
    def draw_blank(self):
        if not hasattr(self,'bars_cache') or not hasattr(self,'canvas') or not self.active_chart:
            return super().draw_blank()
        rows=self.bars_cache.get((self._parts(self.active_chart)[0],self.tf.get()),[])
        if not rows:return super().draw_blank()
        _,kind=self._parts(self.active_chart)
        if kind in ('Order Flow','Footprint','TPO','Volume Profile','Renko'):
            self.canvas.delete('all')
            self.canvas.create_text(self.canvas.winfo_width()/2,self.canvas.winfo_height()/2,
                text=kind+' requires a dedicated calculation / data module\nNo fabricated market data displayed',
                fill='#c6d6e7',font=('Segoe UI',14),justify='center')
            return
        if kind=='Heikin Ashi':
            transformed=[];prior_open=None;prior_close=None
            for ts,o,hi,lo,cl,v in rows:
                ha_close=(o+hi+lo+cl)/4
                ha_open=(o+cl)/2 if prior_open is None else (prior_open+prior_close)/2
                transformed.append((ts,ha_open,max(hi,ha_open,ha_close),min(lo,ha_open,ha_close),ha_close,v))
                prior_open,prior_close=ha_open,ha_close
            rows=transformed
        c=self.canvas;c.configure(bg=self.prefs['background']);c.delete('all');w=c.winfo_width();h=c.winfo_height()
        if w<120 or h<100:return
        available=min(self.replay_count or len(rows),len(rows))
        count=max(25,min(600,int(self.prefs['visible_bars'])+self.zoom_level*14))
        end=min(available,max(1,count+round(max(0,available-count)*self.pan_fraction)))
        left=max(0,end-count);visible=rows[left:end]
        if not visible:return
        # Only reserve volume space if enabled AND genuine positive volume exists.
        volume_active=bool(self.show_volume.get() and any(float(b[5])>0 for b in visible))
        rsi_active=bool(self.show_rsi.get() and len(visible)>15)
        right=w-92
        if volume_active and rsi_active: chart_bottom=int(h*.69)
        elif volume_active or rsi_active: chart_bottom=int(h*.77)
        else: chart_bottom=h-32
        chart_top=38
        # V041: fit the visible OHLC range and use round-number price levels.
        # 1/2/2.5/5/10 multiples provide readable ticks for indices and equities.
        lows=[float(bar[3]) for bar in visible]
        highs=[float(bar[2]) for bar in visible]
        raw_low=min(lows);raw_high=max(highs)
        spread=max(raw_high-raw_low,abs(raw_high)*0.0001,0.000001)
        padded_low=raw_low-spread*0.08
        padded_high=raw_high+spread*0.08
        raw_step=(padded_high-padded_low)/19.0
        magnitude=10**math.floor(math.log10(raw_step))
        tick_step=next((m*magnitude for m in (1,2,2.5,5,10) if m*magnitude>=raw_step),10*magnitude)
        lo=math.floor(padded_low/tick_step)*tick_step
        hi=math.ceil(padded_high/tick_step)*tick_step
        # Retain manual vertical panning, measured in fractions of the fitted range.
        shift=(hi-lo)*self.price_shift
        lo+=shift;hi+=shift
        first_tick=math.ceil((lo-1e-9*tick_step)/tick_step)
        last_tick=math.floor((hi+1e-9*tick_step)/tick_step)
        price_ticks=[i*tick_step for i in range(first_tick,last_tick+1)]
        def py(v):return chart_top+(hi-v)/(hi-lo)*(chart_bottom-chart_top)
        margin=min(int(self.prefs['right_margin']),max(0,count//3))
        step=right/max(1,count+margin);body=max(1,min(20,step*float(self.prefs['body_width'])/100))
        if self.grid_on:
            for i in range(1,6):
                y=chart_top+(chart_bottom-chart_top)*i/6
                c.create_line(0,y,right,y,fill='#1d2630',dash=(2,5))
        # AmiBroker-inspired subtle vertical bands, using the same bar-to-X transform.
        ist=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
        if self.tf.get()!='1D' and self.prefs['bands']:
            previous_band=None
            for i,b in enumerate(visible):
                stamp=datetime.datetime.fromtimestamp(b[0],ist)
                band=(stamp.date(), (stamp.hour*60+stamp.minute)//30)
                if band!=previous_band:
                    previous_band=band
                if band[1]%2==0:
                    x1=i*step; x2=(i+1)*step
                    c.create_rectangle(x1,chart_top,x2,h-25,fill=self.prefs['band_color'],outline='')
        # Price axis: auto-fitted round levels; gridlines match labels.
        for value in price_ticks:
            y=py(value)
            if self.prefs['horizontal_grid']:
                c.create_line(0,y,right,y,fill=self.prefs['grid_color'],dash=(2,5))
        line_points=[]
        for i,b in enumerate(visible):
            x=(i+.5)*step;_,o,high,low,close,vol=b
            if kind in ('Line','Area'):
                line_points.extend((x,py(close)))
                continue
            color=self.prefs['up_color'] if close>=o else self.prefs['down_color']
            c.create_line(x,py(high),x,py(low),fill=color,width=max(1,int(self.prefs['wick_width'])))
            if kind=='OHLC':
                c.create_line(x-body/2,py(o),x,py(o),fill=color)
                c.create_line(x,py(close),x+body/2,py(close),fill=color)
            else:
                c.create_rectangle(x-body/2,py(max(o,close)),x+body/2,max(py(min(o,close)),py(max(o,close))+1),fill=(self.prefs['background'] if close>=o and self.prefs['hollow_up'] else color),outline=color)
        if len(line_points)>=4:
            if kind=='Area':
                c.create_polygon(line_points+[right,chart_bottom,0,chart_bottom],fill='#102f35',outline='')
            c.create_line(*line_points,fill='#35c8b3',width=2)
        c.create_line(right,0,right,h,fill='#56606c')
        # Round-number labels, with only the precision the interval needs.
        decimals=max(0,min(6,-math.floor(math.log10(tick_step)))) if tick_step<1 else (1 if abs(tick_step-round(tick_step))>1e-8 else 0)
        for value in price_ticks:
            y=py(value)
            c.create_line(right-4,y,right,y,fill='#617387')
            c.create_text(right+4,y,text=f'{value:,.{decimals}f}',anchor='w',fill=self.prefs['axis_color'],font=('Consolas',int(self.prefs['axis_font'])))
        precision=int(self.prefs['quote_decimals'])
        lastbar=visible[-1]
        last_close=lastbar[4]
        last_change=(last_close-lastbar[1])/lastbar[1]*100 if lastbar[1] else 0
        c.create_text(9,10,text=f'{self.active_chart}  {self.tf.get()}  {datetime.datetime.fromtimestamp(lastbar[0],datetime.timezone(datetime.timedelta(hours=5,minutes=30))).strftime("%d-%m-%Y %H:%M")}  Open {lastbar[1]:,.{precision}f}  Hi {lastbar[2]:,.{precision}f}  Lo {lastbar[3]:,.{precision}f}  Close {last_close:,.{precision}f}  ({last_change:+.2f}%)',anchor='nw',fill='#e4edf9',font=('Segoe UI',9,'bold'))
        # Right-edge last-price marker, tied to the real close (not a rounded tick).
        last_y=py(last_close)
        if chart_top<=last_y<=chart_bottom:
            marker_color='#00b827' if lastbar[4]>=lastbar[1] else '#e62b2b'
            c.create_line(right-14,last_y,right,last_y,fill=marker_color,width=1)
            c.create_rectangle(right+1,last_y-9,w-1,last_y+9,fill='#e0e0e0',outline='')
            c.create_text(right+5,last_y,text=f'{last_close:,.2f}',anchor='w',fill='#151515',font=('Consolas',9,'bold'))
        if self.replay_count is not None:c.create_text(right-10,10,text='REPLAY',anchor='ne',fill='#f6ba59',font=('Segoe UI',10,'bold'))
        closes=[b[4] for b in rows[:end]]
        def line_indicator(values,color):
            coords=[]
            for i in range(left,end):
                if values[i] is None:continue
                coords.extend(((i-left+.5)*step,py(values[i])))
            if len(coords)>=4:c.create_line(*coords,fill=color,width=1.6,smooth=False)
        if self.show_sma.get():
            sma=[None]*len(closes)
            for i in range(19,len(closes)):sma[i]=sum(closes[i-19:i+1])/20
            line_indicator(sma,'#ffcc5b')
        if self.show_ema.get():
            ema=[];last=None
            for value in closes:
                last=value if last is None else last+(value-last)*(2/21)
                ema.append(last)
            line_indicator(ema,'#78aaff')
        if self.show_bbands.get() and len(closes)>=20:
            upper=[None]*len(closes);lower=[None]*len(closes)
            for j in range(19,len(closes)):
                window=closes[j-19:j+1]
                avg=sum(window)/20
                sigma=math.sqrt(sum((v-avg)**2 for v in window)/20)
                upper[j]=avg+2*sigma;lower[j]=avg-2*sigma
            line_indicator(upper,'#8b93e8')
            line_indicator(lower,'#8b93e8')
        vol_top=chart_bottom+10;vol_bottom=h-25
        if volume_active:
            vol_bottom=int(h*.84) if self.show_rsi.get() else h-27
            vmax=max((b[5] for b in visible),default=1) or 1
            for i,b in enumerate(visible):
                x=(i+.5)*step;v=b[5];barh=(vol_bottom-vol_top)*v/vmax
                c.create_rectangle(x-body/2,vol_bottom-barh,x+body/2,vol_bottom,fill='#296f62' if b[4]>=b[1] else '#80414d',outline='')
            c.create_text(7,vol_top,text='VOL',anchor='nw',fill='#9bb0c4',font=('Segoe UI',8))
        if self.show_rsi.get() and len(closes)>15:
            rsis=[None]*len(closes)
            for i in range(14,len(closes)):
                changes=[closes[j]-closes[j-1] for j in range(i-13,i+1)]
                gains=sum(max(d,0) for d in changes)/14;losses=sum(max(-d,0) for d in changes)/14
                rsis[i]=100 if losses==0 else 100-100/(1+gains/losses)
            top=int(h*.9) if volume_active else chart_bottom+8
            bottom=h-27
            coords=[]
            for i in range(left,end):
                if rsis[i] is not None:coords.extend(((i-left+.5)*step, bottom-(rsis[i]/100)*(bottom-top)))
            if len(coords)>=4:c.create_line(*coords,fill='#b391ff',width=1.4)
            c.create_text(7,top,text='RSI 14',anchor='nw',fill='#b391ff',font=('Segoe UI',8))
        c.create_line(0,h-25,right,h-25,fill='#394351')
        # Timeframe-specific IST clock ticks; all labels share the candle X transform.
        # 1m uses 5m ticks; 5m uses 15m ticks, subject only to label overlap.
        # The underlying candle geometry is never moved to manufacture a tick.
        ist=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
        tf=self.tf.get()
        tick_minutes={'1m':5,'5m':15,'9m':30,'15m':60,'30m':120,'60m':240}.get(tf)
        min_gap=(30 if tf in ('1m','5m') else max(42,int(self.prefs['grid_spacing'])//2))
        last_tick_x=-min_gap
        for i,bar in enumerate(visible):
            stamp=datetime.datetime.fromtimestamp(bar[0],ist)
            x=(i+.5)*step
            if x-last_tick_x<min_gap:continue
            if tf=='1D':
                # Day labels are dates, not invented intraday times.
                label=stamp.strftime('%d-%m')
                eligible=True
            else:
                minute_of_day=stamp.hour*60+stamp.minute
                eligible=(minute_of_day % tick_minutes == 0)
                label=stamp.strftime('%H:%M')
            if not eligible:continue
            if i and stamp.date()!=datetime.datetime.fromtimestamp(visible[i-1][0],ist).date():
                label=stamp.strftime('%d %b')
            if self.prefs['vertical_grid']:c.create_line(x,chart_top,x,h-25,fill=self.prefs['grid_color'],dash=(2,5))
            c.create_line(x,h-25,x,h-21,fill='#617387')
            c.create_text(x,h-13,text=label,fill='#91a6ba',font=('Segoe UI',8))
            last_tick_x=x
        # OHLC information uses the identical visible index-to-X mapping.
        if self.pointer and 0<=self.pointer[0]<right:
            i=max(0,min(len(visible)-1,int(self.pointer[0]/step)))
            b=visible[i]
            when=datetime.datetime.fromtimestamp(b[0],ist).strftime('%d-%m %H:%M')
            detail=f'{when}  O {b[1]:,.{precision}f}  H {b[2]:,.{precision}f}  L {b[3]:,.{precision}f}  C {b[4]:,.{precision}f}'
            c.create_text(right-8,10,text=detail,anchor='ne',fill='#a5cce5',font=('Consolas',9),tags='ohlc')
        for idx,item in enumerate(self.shapes.get(self.active_sheet,[])):
            if idx<len(self._drawing_metadata()) and not self._drawing_metadata()[idx].get("visible",True):continue
            typ,x1,y1,x2,y2=item
            if typ=='Rectangle':c.create_rectangle(x1,y1,x2,y2,outline='#e8b55c')
            elif typ=='Ellipse':c.create_oval(x1,y1,x2,y2,outline='#e8b55c')
            elif typ=='Text marker':c.create_text(x1,y1,text='NOTE',fill='#e8b55c',anchor='nw')
            else:c.create_line(x1,y1,x2,y2,fill='#e8b55c',width=2)
        if self.cross_on and self.pointer:
            x,y=self.pointer;c.create_line(x,0,x,h-25,fill=self.prefs['cross_color'],dash=(3,3),tags='cross');c.create_line(0,y,right,y,fill=self.prefs['cross_color'],dash=(3,3),tags='cross')


    PREF_DEFAULTS={
        'visible_bars':159,'right_margin':10,'body_width':64,'wick_width':1,
        'hollow_up':False,'bands':True,'horizontal_grid':True,'vertical_grid':True,
        'grid_spacing':105,'up_color':'#00dc22','down_color':'#ff2525',
        'background':'#050505','band_color':'#1b1b1b','grid_color':'#292929',
        'axis_color':'#b9c6d5','cross_color':'#657d9e','axis_font':8,
        'quote_decimals':2,'cache_symbols':100,
        'session_alignment':True,'timestamp_mode':'Start of interval',
    }

    def _prefs_path(self):
        import os
        folder=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'MagicAlgoPro'
        return folder / 'preferences.json'

    def _load_prefs(self):
        defaults=dict(self.PREF_DEFAULTS)
        try:
            data=json.loads(self._prefs_path().read_text(encoding='utf-8'))
            if isinstance(data,dict):
                for key in defaults:
                    if key in data and isinstance(data[key],type(defaults[key])):
                        defaults[key]=data[key]
        except (OSError,ValueError,TypeError):pass
        return defaults

    def _save_prefs(self):
        path=self._prefs_path()
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(self.prefs,indent=2),encoding='utf-8')

    def customize(self):
        """Compact, functional customization controls, separate from market data."""
        if getattr(self,'customize_window',None) and self.customize_window.winfo_exists():
            self.customize_window.lift();return
        win=tk.Toplevel(self);self.customize_window=win
        win.title('Octopus V064 — Customize');win.geometry('490x390');win.transient(self)
        book=ttk.Notebook(win);book.pack(fill='both',expand=True,padx=9,pady=9)
        config_path=self._prefs_path().with_name('MagicAlgoPro_customize.json')
        defaults={'full_menus':True,'large_icons':False,'tips':True,'shortcut_tips':True,'dark_lists':True,'tab_position':'Top','menu_animation':'None'}
        try:settings={**defaults,**json.loads(config_path.read_text(encoding='utf-8'))}
        except (OSError,ValueError):settings=defaults.copy()
        vars={k:(tk.BooleanVar(value=v) if isinstance(v,bool) else tk.StringVar(value=v)) for k,v in settings.items()}
        def page(name):
            frame=ttk.Frame(book,padding=15);book.add(frame,text=name);return frame
        options=page('Options')
        for key,label in [('full_menus','Always show full menus'),('large_icons','Large toolbar icons'),('tips','Show toolbar tooltips'),('shortcut_tips','Show shortcut keys in tooltips')]:
            ttk.Checkbutton(options,text=label,variable=vars[key]).pack(anchor='w',pady=7)
        ttk.Label(options,text='Menu animation').pack(anchor='w',pady=(12,3))
        ttk.Combobox(options,textvariable=vars['menu_animation'],values=['None','Fade','Slide'],state='readonly',width=17).pack(anchor='w')
        appearance=page('Appearance')
        ttk.Label(appearance,text='Chart tab location').pack(anchor='w',pady=5)
        for val in ['Top','Bottom']:ttk.Radiobutton(appearance,text=val,variable=vars['tab_position'],value=val).pack(anchor='w',pady=4)
        ttk.Checkbutton(appearance,text='Use dark theme for list views',variable=vars['dark_lists']).pack(anchor='w',pady=10)
        ttk.Label(appearance,text='Chart colors and grids: Tools → Preferences.').pack(anchor='w',pady=10)
        keys=page('Keyboard')
        ttk.Label(keys,text='Current shortcuts').pack(anchor='w')
        for line in ['Ctrl+N    New chart','Ctrl+W    Close chart','Ctrl+S    Save workspace','Ctrl+O    Open workspace','F5            Redraw chart','Esc          Crosshair tool']:
            ttk.Label(keys,text=line).pack(anchor='w',pady=4)
        ttk.Label(keys,text='Custom key reassignment is not available in this build.').pack(anchor='w',pady=9)
        footer=ttk.Frame(win);footer.pack(fill='x',padx=10,pady=(0,10))
        def apply(close=False):
            data={k:v.get() for k,v in vars.items()}
            try:
                config_path.parent.mkdir(parents=True,exist_ok=True)
                config_path.write_text(json.dumps(data,indent=2),encoding='utf-8')
            except OSError as exc:
                messagebox.showerror('Customize',str(exc),parent=win);return
            # Theme options are saved; avoid rebuilding charts or requesting data.
            if close:win.destroy()
        ttk.Button(footer,text='Close',command=win.destroy).pack(side='right',padx=4)
        ttk.Button(footer,text='Apply',command=apply).pack(side='right',padx=4)
        ttk.Button(footer,text='OK',command=lambda:apply(True)).pack(side='right',padx=4)

    def preferences(self):
        if getattr(self,'prefs_window',None) and self.prefs_window.winfo_exists():
            self.prefs_window.lift();return
        win=tk.Toplevel(self);self.prefs_window=win
        win.title('Octopus V064 — Preferences')
        win.geometry('650x520');win.minsize(610,480);win.transient(self)
        book=ttk.Notebook(win);book.pack(fill='both',expand=True,padx=9,pady=9)
        pending=dict(self.prefs)
        controls={}
        def page(title):
            frame=ttk.Frame(book,padding=13);book.add(frame,text=title);return frame
        def entry(parent,key,label,row,lo,hi):
            ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=7)
            v=tk.StringVar(value=str(pending[key]));controls[key]=(v,int,lo,hi)
            ttk.Entry(parent,textvariable=v,width=12).grid(row=row,column=1,sticky='w',padx=14)
        def check(parent,key,label,row):
            v=tk.BooleanVar(value=pending[key]);controls[key]=(v,bool,None,None)
            ttk.Checkbutton(parent,text=label,variable=v).grid(row=row,column=0,columnspan=3,sticky='w',pady=6)
        def color(parent,key,label,row):
            ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=5)
            v=tk.StringVar(value=pending[key]);controls[key]=(v,str,None,None)
            btn=tk.Button(parent,width=15,textvariable=v,bg=pending[key],fg='#ffffff')
            def choose():
                selected=colorchooser.askcolor(color=v.get(),parent=win)[1]
                if selected:v.set(selected);btn.configure(bg=selected)
            btn.configure(command=choose);btn.grid(row=row,column=1,sticky='w',padx=14)
        chart=page('Charting')
        entry(chart,'visible_bars','Default visible bars',0,25,600)
        entry(chart,'right_margin','Blank bars at right margin',1,0,50)
        entry(chart,'body_width','Candle body width (%)',2,10,100)
        check(chart,'hollow_up','Use hollow bodies for rising candles',3)
        candle=page('Bars & Candles')
        entry(candle,'wick_width','Wick thickness (pixels)',0,1,3)
        ttk.Label(candle,text='Candle body width and hollow style are in Charting.').grid(row=1,column=0,columnspan=3,sticky='w',pady=10)
        grid=page('Axes / Grids')
        check(grid,'bands','Alternating dark time bands',0)
        check(grid,'vertical_grid','Vertical gridlines at time labels',1)
        check(grid,'horizontal_grid','Horizontal gridlines at price levels',2)
        entry(grid,'grid_spacing','Minimum time-label spacing (px)',3,50,250)
        entry(grid,'axis_font','Axis font size',4,7,13)
        colors=page('Colors')
        for row,(key,label) in enumerate([('background','Chart background'),('up_color','Up candles'),('down_color','Down candles'),('band_color','Time bands'),('grid_color','Grid lines'),('axis_color','Axis text'),('cross_color','Crosshair')]):
            color(colors,key,label,row)
        data=page('Data')
        entry(data,'cache_symbols','Maximum cached symbol/timeframes',0,10,500)
        ttk.Label(data,text='Yahoo historical candles remain memory-only; no CSV/Excel files.',wraplength=530).grid(row=1,column=0,columnspan=3,sticky='w',pady=12)
        intra=page('Intraday')
        ttk.Label(intra,text='9-minute candles: aligned to NSE session at 09:15 IST (always enabled)').grid(row=0,column=0,columnspan=3,sticky='w',pady=7)
        ttk.Label(intra,text='9m uses 1-minute historical bars; no tick feed is connected.\nCompressed bars use the interval START timestamp.',justify='left').grid(row=1,column=0,columnspan=3,sticky='w',pady=14)
        misc=page('Miscellaneous')
        entry(misc,'quote_decimals','OHLC decimal places',0,0,6)
        ttk.Label(misc,text='Preferences save to local AppData and reload at startup.\nBroker trading remains disabled.',justify='left').grid(row=1,column=0,columnspan=3,sticky='w',pady=12)
        footer=ttk.Frame(win);footer.pack(fill='x',padx=10,pady=(0,10))
        def apply(close=False):
            try:
                for key,(v,typ,lo,hi) in controls.items():
                    val=v.get() if typ is bool else typ(v.get())
                    if lo is not None and not lo<=val<=hi:raise ValueError(f'{key}: enter {lo} to {hi}')
                    pending[key]=val
                self.prefs.update(pending)
                self._save_prefs()
                self.draw_blank()
                self.info.set('V064 | Chart preferences saved | Trading disabled')
                if close:win.destroy()
            except (ValueError,OSError) as exc:messagebox.showerror('Preferences',str(exc),parent=win)
        ttk.Button(footer,text='Cancel',command=win.destroy).pack(side='right',padx=4)
        ttk.Button(footer,text='Apply',command=apply).pack(side='right',padx=4)
        ttk.Button(footer,text='OK',command=lambda:apply(True)).pack(side='right',padx=4)
        def reset():
            for key,(v,typ,_,_) in controls.items():v.set(self.PREF_DEFAULTS[key])
        ttk.Button(footer,text='Restore defaults',command=reset).pack(side='left')

if __name__=='__main__':
    try:
        if _acquire_octopus_instance():
            ChartApp().mainloop()
        else:
            # Existing window was activated by _acquire_octopus_instance().
            # Exit quietly: a standalone Tk messagebox can appear behind other windows.
            pass
    except Exception:
        import traceback, pathlib, os
        log=pathlib.Path(os.environ.get('LOCALAPPDATA',str(pathlib.Path.home()))) / f'Octopus_{VERSION}_startup_error.log'
        log.write_text(traceback.format_exc(),encoding='utf-8')
        try:
            import tkinter.messagebox as mb
            mb.showerror(f'Octopus {VERSION} startup error',f'Unable to open application. Error report saved to:\n{log}\n\n{traceback.format_exc()[-1200:]}')
        except Exception:pass

import sys
import psutil
import time
from infi.systray import SysTrayIcon

BASE_PATH = 'C:\\Users\\vroth\\Google Drive\\Projetos\\running_programs\\'

def get_active_window():
    """
    Get the currently active window.

    Returns
    -------
    string :
        Name of the currently active window.
    """
    import sys
    active_window_name = None
    tid, pid = None, None
    path = None
    if sys.platform in ['linux', 'linux2']:
        # Alternatives: http://unix.stackexchange.com/q/38867/4784
        try:
            import wnck
        except ImportError:
            logging.info("wnck not installed")
            wnck = None
        if wnck is not None:
            screen = wnck.screen_get_default()
            screen.force_update()
            window = screen.get_active_window()
            if window is not None:
                pid = window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
        else:
            try:
                from gi.repository import Gtk, Wnck
                gi = "Installed"
            except ImportError:
                logging.info("gi.repository not installed")
                gi = None
            if gi is not None:
                Gtk.init([])  # necessary if not using a Gtk.main() loop
                screen = Wnck.Screen.get_default()
                screen.force_update()  # recommended per Wnck documentation
                active_window = screen.get_active_window()
                pid = active_window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
    elif sys.platform in ['Windows', 'win32', 'cygwin']:
        # http://stackoverflow.com/a/608814/562769
        import win32gui
        import win32process
        window = win32gui.GetForegroundWindow()
        tid, pid = win32process.GetWindowThreadProcessId(window)
        try:
            path = psutil.Process(pid).exe()
        except:
            pass
        active_window_name = win32gui.GetWindowText(window)
    elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
        # http://stackoverflow.com/a/373310/562769
        from AppKit import NSWorkspace
        active_window_name = (NSWorkspace.sharedWorkspace()
                              .activeApplication()['NSApplicationName'])
    else:
        print("sys.platform={platform} is unknown. Please report."
              .format(platform=sys.platform))
        print(sys.version)
    return {'pid': pid, 'name': active_window_name, 'path': path, 'time': time.time()}

ENABLED = True
counted = 0

def enable_disable(systray):
    global ENABLED
    ENABLED = not ENABLED
    if(ENABLED):
        print('Enabled')
        systray.update(icon='on.ico')
    #    systray.update(menu_options=menu_options_enabled)
    else:
        print('Disabled')
        systray.update(icon='off.ico')
    #    systray.update(menu_options=menu_options_disabled)
    
menu_options_enabled = (("Enable/Disable", None, enable_disable),)
#menu_options_disabled = (("Enable", None, enable_disable),)

#icon by: https://www.flaticon.com/free-icon/growth_3094918?term=stats&page=1&position=9&page=1&position=9&related_id=3094918&origin=search
systray = SysTrayIcon("on.ico", "System logger", menu_options_enabled)
systray.start()

def get_new_file_name():
    f = BASE_PATH + time.strftime("%Y%m%d") + '_app_use.csv'
    print('File: ', f)
    return f

def logging_function(date, time, pid, name, path, duration):
    global counted
    counted += 1
    out = ';'.join([str(i) for i in [date, 
                               time,
                               pid,
                               name.replace('\\', '\\\\').replace('""', '\\"') if name else '',
                               path.replace('\\', '\\\\').replace('""', '\\"') if path else '', 
                               duration]])
    print(counted, out, end='\r')
    return(out)

last = {'pid': None,
        'name': None,
        'path': None,
        'time': time.time()}

with open(get_new_file_name(), 'a+') as f:
    while True:
        time.sleep(0.1)
        if(ENABLED):
            active = get_active_window()
            if (active['name'] == last['name']) and (last['pid'] == active['pid']):
                continue
            f.write(logging_function(date = time.strftime("%Y-%m-%d"),
                                     time = time.strftime("%H:%M:%S"),
                                     pid = last['pid'],
                                     name = last['name'],
                                     path = last['path'],
                                     duration = active['time'] - last['time']) + '\n')
            last = active
        else:
            last = {'pid': None,
                    'name': None,
                    'path': None,
                    'time': time.time()}
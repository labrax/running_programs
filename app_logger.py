import sys
import psutil
import time
from infi.systray import SysTrayIcon
import subprocess

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

NOT_QUITTING = True
ENABLED = True
counted = 0
f = None

def enable_disable(systray):
    global ENABLED
    ENABLED = not ENABLED
    if(ENABLED):
        systray.update(icon='on.ico')
    #    systray.update(menu_options=menu_options_enabled)
    else:
        if f:
            f.flush()
        systray.update(icon='off.ico')
    #    systray.update(menu_options=menu_options_disabled)

def generate_report(systray):
    subprocess.Popen(["python", "plots.py"])

def on_quit_callback(systray):
    global NOT_QUITTING
    if f:
        f.flush()
    NOT_QUITTING = False


menu_options_enabled = (("Enable/Disable", None, enable_disable),
                        ("Generate report", None, generate_report))
#menu_options_disabled = (("Enable", None, enable_disable),)

#icon by: https://www.flaticon.com/free-icon/growth_3094918?term=stats&page=1&position=9&page=1&position=9&related_id=3094918&origin=search
systray = SysTrayIcon("on.ico", "App logger", menu_options_enabled, on_quit=on_quit_callback, default_menu_index=0)
systray.start()

def get_new_file_name():
    f = BASE_PATH + time.strftime("%Y%m%d") + '_app_use.csv'
    print('File: ', f)
    return f

def logging_function(pid, name, path, duration):
    cur_date = time.strftime("%Y-%m-%d")
    cur_time = time.strftime("%H:%M:%S")
    
    global counted
    counted += 1
    out = ';'.join([str(i) for i in [cur_date, 
                                     cur_time,
                                     pid,
                                     name.replace('\\', '\\\\').replace('""', '\\"') if name else '',
                                     path.replace('\\', '\\\\').replace('""', '\\"') if path else '', 
                                     duration]])
    print(counted, cur_time, path, duration, "                                  ", end='\r')
    return(out)

last = {'pid': None,
        'name': None,
        'path': None,
        'time': time.time()}

f = open(get_new_file_name(), 'a+')
if not f:
    print('Something went wrong starting')
else:
    while NOT_QUITTING:
        time.sleep(0.1)
        if(ENABLED):
            if last['pid'] is None:
                f.write(logging_function(pid = -1,
                                         name = 'Started',
                                         path = '',
                                         duration = 0) + '\n')
            active = get_active_window()
            if (active['name'] == last['name']) and (last['pid'] == active['pid']):
                continue
            try:
                f.write(logging_function(pid = last['pid'],
                                         name = last['name'],
                                         path = last['path'],
                                         duration = active['time'] - last['time']) + '\n')
            except Exception as e:
                print(e)
            last = active
        else:
            if last['pid'] is not None:
                try:
                    f.write(logging_function(pid = last['pid'],
                                             name = last['name'],
                                             path = last['path'],
                                             duration = active['time'] - last['time']) + '\n')
                except Exception as e:
                    print(e)
                f.write(logging_function(pid = -1,
                                         name = 'Stopped',
                                         path = '',
                                         duration = 0) + '\n')
            last = {'pid': None,
                    'name': None,
                    'path': None,
                    'time': time.time()}

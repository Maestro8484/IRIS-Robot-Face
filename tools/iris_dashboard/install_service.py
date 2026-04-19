
import sys
import os
import subprocess
import win32serviceutil
import win32service
import win32event
import servicemanager

PYTHON_EXE = r"C:\Python314\python.exe"
APP_DIR    = r"C:\Users\gandalf\iris_dashboard"


class IRISDashboardService(win32serviceutil.ServiceFramework):
    _svc_name_ = "IRISDashboard"
    _svc_display_name_ = "IRIS Mission Control Dashboard"
    _svc_description_ = "IRIS robot face monitoring dashboard on port 8080"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        os.chdir(APP_DIR)
        self.process = subprocess.Popen(
            [PYTHON_EXE, "app.py"],
            cwd=APP_DIR
        )
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(IRISDashboardService)

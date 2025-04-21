# from dashboard.dashboard_with_sqlite import *         # For test code
# from dashboard.dashboard_for_multicam import *          # For Windows machine
from dashboard.dashboard_raspi import *               # For Raspberry Pi machine

if __name__ == "__main__":
    app = DashboardApp(theme="darkly")
    app.mainloop()
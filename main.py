# from dashboard.dashboard_with_sqlite import *
from dashboard.dashboard_for_multicam import *

if __name__ == "__main__":
    app = DashboardApp(theme="darkly")
    app.mainloop()
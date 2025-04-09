from dashboard.dashboard_with_sqlite import *

if __name__ == "__main__":
    app = DashboardApp(theme="darkly")
    app.mainloop()
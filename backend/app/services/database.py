try:
    from database import get_dashboard_stats, save_receipt
except ImportError:
    from backend.database import get_dashboard_stats, save_receipt

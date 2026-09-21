import json
import os
import sqlite3
from typing import Any, Dict, List

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'receipts.db')


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant TEXT,
            total REAL NOT NULL,
            date TEXT,
            category TEXT,
            items_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    conn.commit()
    return conn


def save_receipt(data: Dict[str, Any], category: str) -> Dict[str, Any]:
    conn = _get_connection()
    try:
        merchant = str(data.get('merchant') or 'Unknown Store')
        total = float(data.get('total') or 0.0)
        receipt_date = data.get('date') or None
        items = data.get('items') or []

        cursor = conn.execute(
            '''
            INSERT INTO receipts (merchant, total, date, category, items_json)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (merchant, total, receipt_date, category, json.dumps(items)),
        )
        conn.commit()
        receipt_id = cursor.lastrowid
        return {
            'id': receipt_id,
            'merchant': merchant,
            'total': total,
            'date': receipt_date,
            'category': category,
            'items': items,
        }
    finally:
        conn.close()


def get_dashboard_stats() -> Dict[str, Any]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            '''
            SELECT category, ROUND(SUM(total), 2) AS total_spent, COUNT(*) AS receipt_count
            FROM receipts
            GROUP BY category
            ORDER BY total_spent DESC
            '''
        ).fetchall()

        labels = []
        totals = []
        counts = []
        for row in rows:
            labels.append(row['category'] or 'Uncategorized')
            totals.append(float(row['total_spent'] or 0.0))
            counts.append(int(row['receipt_count'] or 0))

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Spending',
                    'data': totals,
                    'backgroundColor': [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8D6E63'
                    ],
                }
            ],
            'counts': counts,
        }
    finally:
        conn.close()

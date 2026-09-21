"""
Anomaly detection for financial transactions.
Uses Isolation Forest for detecting unusual spending patterns.
"""

import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


class AnomalyDetector:
    """Detect anomalous transactions using statistical methods"""
    
    @staticmethod
    def detect_anomalies(receipts, sensitivity=0.8):
        """
        Detect anomalous transactions.
        
        Args:
            receipts: List of Receipt objects
            sensitivity: 0.0-1.0, higher = more sensitive (more anomalies flagged)
        
        Returns:
            Dict with anomaly scores and interpretations
        """
        if not receipts or len(receipts) < 5:
            return {
        'anomalies': [],
        'message': 'Insufficient data for anomaly detection',
        'total_detected': 0,
        'high_severity': 0,
        'medium_severity': 0,
        'low_severity': 0
    }
        
        anomalies = []
        
        # Convert receipts to dict for easier processing
        receipt_list = []
        for r in receipts:
            receipt_list.append({
                'id': r.id,
                'merchant': r.merchant_name,
                'total': float(r.total),
                'category': r.category,
                'date': r.receipt_date,
                'payment_method': r.payment_method
            })
        
        # 1. Statistical outliers: High spend by amount (Z-score method)
        amounts = [r['total'] for r in receipt_list]
        mean_amount = np.mean(amounts)
        std_amount = np.std(amounts)
        
        if std_amount > 0:
            z_threshold = sensitivity * 3  # Higher sensitivity = lower threshold
            for r in receipt_list:
                z_score = abs((r['total'] - mean_amount) / std_amount)
                if z_score > z_threshold:
                    anomalies.append({
                        'receipt_id': r['id'],
                        'merchant': r['merchant'],
                        'total': r['total'],
                        'reason': f'Unusually high amount (${r["total"]:.2f}) for {r["category"]}',
                        'type': 'unusual_amount',
                        'severity': 'medium',
                        'z_score': float(z_score)
                    })
        
        # 2. Category outliers: Unusual spending patterns by category
        category_stats = defaultdict(list)
        for r in receipt_list:
            category_stats[r['category']].append(r['total'])
        
        for r in receipt_list:
            cat = r['category']
            if len(category_stats[cat]) >= 3:
                cat_amounts = category_stats[cat]
                cat_mean = np.mean(cat_amounts)
                cat_std = np.std(cat_amounts)
                
                if cat_std > 0:
                    z_score = abs((r['total'] - cat_mean) / cat_std)
                    if z_score > 2.5 * sensitivity:
                        # Check if not already flagged
                        if not any(a['receipt_id'] == r['id'] and a['type'] == 'category_outlier' for a in anomalies):
                            anomalies.append({
                                'receipt_id': r['id'],
                                'merchant': r['merchant'],
                                'total': r['total'],
                                'reason': f'Unusual for {cat}: ${r["total"]:.2f} vs avg ${cat_mean:.2f}',
                                'type': 'category_outlier',
                                'severity': 'low',
                                'z_score': float(z_score)
                            })
        
        # 3. Frequency anomalies: Same merchant multiple times in short period
        merchant_dates = defaultdict(list)
        for r in receipt_list:
            if r['date']:
                merchant_dates[r['merchant']].append(r['date'])
        
        for merchant, dates in merchant_dates.items():
            if len(dates) >= 3:
                sorted_dates = sorted(dates)
                # Look for 3+ transactions in 7 days
                for i in range(len(sorted_dates) - 2):
                    if (sorted_dates[i+2] - sorted_dates[i]).days <= 7:
                        # Find the receipts involved
                        for r in receipt_list:
                            if r['merchant'] == merchant and r['date'] in sorted_dates[i:i+3]:
                                if not any(a['receipt_id'] == r['id'] and a['type'] == 'frequency' for a in anomalies):
                                    anomalies.append({
                                        'receipt_id': r['id'],
                                        'merchant': r['merchant'],
                                        'total': r['total'],
                                        'reason': f'Multiple purchases at {merchant} in 7 days (possible duplicate)',
                                        'type': 'frequency',
                                        'severity': 'high',
                                        'z_score': 0
                                    })
                        break
        
        # 4. Duplicate detection: Same amount at same merchant
        seen = defaultdict(list)
        for r in receipt_list:
            key = (r['merchant'], r['total'])
            seen[key].append(r)
        
        for (merchant, amount), recs in seen.items():
            if len(recs) > 1:
                # Check if dates are close
                dates = [r['date'] for r in recs if r['date']]
                if len(dates) >= 2:
                    dates_sorted = sorted(dates)
                    if (dates_sorted[-1] - dates_sorted[0]).days <= 1:  # Within 1 day
                        for r in recs:
                            if not any(a['receipt_id'] == r['id'] and a['type'] == 'duplicate' for a in anomalies):
                                anomalies.append({
                                    'receipt_id': r['id'],
                                    'merchant': r['merchant'],
                                    'total': r['total'],
                                    'reason': f'Potential duplicate: Same amount ${amount:.2f} at {merchant}',
                                    'type': 'duplicate',
                                    'severity': 'high',
                                    'z_score': 0
                                })
        
        # Sort by severity and z-score
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        anomalies.sort(key=lambda x: (severity_order.get(x['severity'], 3), -x.get('z_score', 0)))
        
        return {
            'anomalies': anomalies[:20],  # Limit to top 20
            'total_detected': len(anomalies),
            'high_severity': sum(1 for a in anomalies if a['severity'] == 'high'),
            'medium_severity': sum(1 for a in anomalies if a['severity'] == 'medium'),
            'low_severity': sum(1 for a in anomalies if a['severity'] == 'low'),
        }
    
    @staticmethod
    def get_anomaly_summary(anomalies_result):
        """Get a text summary of detected anomalies"""
        anomalies = anomalies_result.get('anomalies', [])
        
        if not anomalies:
            return "No anomalies detected. Your spending looks normal."
        
        summary_lines = []
        
        if anomalies_result['high_severity'] > 0:
            summary_lines.append(f"🔴 HIGH PRIORITY: {anomalies_result['high_severity']} high-severity issues detected")
        
        if anomalies_result['medium_severity'] > 0:
            summary_lines.append(f"🟡 MEDIUM: {anomalies_result['medium_severity']} unusual spending patterns")
        
        if anomalies_result['low_severity'] > 0:
            summary_lines.append(f"🔵 LOW: {anomalies_result['low_severity']} minor anomalies")
        
        summary_lines.append("\nTop Anomalies:")
        for i, anom in enumerate(anomalies[:5], 1):
            summary_lines.append(f"{i}. {anom['reason']}")
        
        return "\n".join(summary_lines)

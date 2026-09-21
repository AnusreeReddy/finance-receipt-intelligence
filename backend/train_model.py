#!/usr/bin/env python3
"""
Train the expense categorization model.
Run this script to train/retrain the model with expense data.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ml_model import MLModel


# Expanded training dataset
TRAINING_DATA = {
    'descriptions': [
        # Food (28 items)
        'Dinner at restaurant', 'Lunch at cafe', 'Grocery shopping at mall',
        'Breakfast at hotel', 'Snacks at coffee shop', 'Tea at roadside stall', 'Lunch with colleagues',
        'Pizza order online', 'Dinner buffet at restaurant', 'Coffee at Starbucks',
        'Ordered food on delivery app', 'Ice cream from shop', 'Bought groceries', 'Cafe bill',
        'Bought a large pizza', 'Ordered pizza delivery', 'Ate pizza for dinner', 'Pizza from restaurant',
        'Fine dining experience', 'Fast food purchase', 'Supermarket shopping for food',
        'Vegetable purchase from market', 'Fruit stand', 'Bakery items', 'Restaurant bill', 'Drink purchase',
        'Deli sandwich', 'Sushi restaurant',

        # Travel (25 items)
        'Uber ride', 'Flight to destination', 'Train ticket booking', 'Bus fare payment',
        'Taxi fare to airport', 'Metro card recharge', 'Rental car booking', 'Boat ride tickets',
        'Cab ride to office', 'Petrol for car', 'Highway toll payment', 'Train pass renewal',
        'Flight tickets', 'Bus travel', 'Airport taxi', 'Hotel booking', 'Vacation package',
        'Local transport', 'Fuel expense', 'Train journey', 'Toll gate', 'Car rental',
        'Parking fee', 'Gas station', 'Airline booking',

        # Entertainment (22 items)
        'Netflix subscription', 'Movie at theater', 'Concert ticket', 'Amusement park entry',
        'Museum ticket', 'Live sports match ticket', 'Stand-up comedy show',
        'Amazon Prime renewal', 'Spotify subscription', 'Game purchase', 
        'Cinema tickets', 'Video game purchase', 'Theme park entry fee', 'Music concert',
        'Theater show', 'Streaming service', 'Game console purchase', 'Arcade games',
        'Event ticket', 'Party expense', 'Karaoke night', 'Club entry fee',

        # Shopping (32 items) - Expanded
        'New shoes from store', 'Bought jeans online', 'Grocery shopping',
        'Bought vegetables from market', 'Purchased books', 'Bought cosmetics',
        'Purchased gifts for birthday', 'Bought a mobile phone', 'Shopping at mall',
        'New clothes', 'Online shopping', 'Electronics purchase', 'Vegetable market',
        'Fashion items', 'Home decor', 'Jewelry purchase', 'Childrens toys', 'Sports equipment',
        'Bought new running shoes', 'Purchased shoes', 'Shoe store visit',
        'Footwear shopping', 'Dress purchase', 'Shirt bought', 'New gadget',
        'Books from amazon', 'Stationery items', 'Kitchen appliances', 'Home furnishings',
        'Birthday present', 'Clothing store', 'Handbag purchase', 'Watch purchase',

        # Health (20 items)
        'Doctor appointment', 'Buy medicines', 'Health insurance premium',
        'Dental cleaning appointment', 'Gym membership', 'Yoga class payment',
        'Dental appointment', 'General checkup', 'Eye test and glasses', 'Hospital emergency visit',
        'Pharmacy bill', 'Medical checkup', 'Physiotherapy session', 'Medicine purchase',
        'Health checkup', 'Prescription refill', 'Clinic visit', 'Vaccination cost',
        'Mental health counseling', 'Fitness classes',

        # Utilities (16 items)
        'Electricity bill', 'Phone recharge', 'Water bill payment', 'Internet broadband bill',
        'DTH recharge', 'Gas bill', 'Mobile data top-up', 'Landline bill payment',
        'Home electricity bill', 'Wifi bill', 'Phone top up', 'Cooking gas payment',
        'Utility bill payment', 'Broadband service', 'Water supply bill', 'Sewage charges',

        # Education (16 items)
        'Online course payment', 'Tuition fee payment', 'Book purchase for studies',
        'Exam fee', 'Enrolled in online course', 'School uniform purchase',
        'College fees', 'Textbook purchase', 'Course subscription', 'Exam registration',
        'Educational software', 'School supplies', 'University tuition', 'Workshop fee',
        'Language course', 'Training program',

        # Housing (16 items)
        'House rent payment', 'Monthly apartment rent', 'Paying rent to landlord',
        'Security deposit for apartment', 'EMI for home loan', 'Apartment maintenance charges',
        'Rent payment', 'Home loan installment', 'Building maintenance', 'Property tax',
        'Mortgage payment', 'Home renovation', 'Furnace repair', 'Plumbing service',
        'Roof repair', 'Interior decoration',

        # Insurance (11 items)
        'Car insurance premium', 'Life insurance payment', 'Health policy renewal',
        'Auto insurance', 'Home insurance', 'Travel insurance premium',
        'Insurance policy payment', 'Premium payment', 'Health insurance plan',
        'Business insurance', 'Pet insurance',

        # Income (25 items) - Kept for balance
        'Salary for the month', 'Freelance project payment', 'Bonus from office',
        'Dividend from investment', 'Interest from savings', 'Sold old laptop',
        'Monthly paycheck received', 'Payment for consulting', 'Annual bonus',
        'Bank interest credited', 'Stock dividends', 'Sold old phone',
        'Revenue from project', 'Client payment', 'Rental income',
        'Refund received', 'Tax refund', 'Received payment', 'Paycheck deposit',
        'Investment returns', 'Royalty payment', 'Gift money received',
        'Consulting fee', 'Commission earned', 'Investment profit'
    ],
    'categories': [
        # Food (28)
        'Food', 'Food', 'Shopping', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 
        'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 
        'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food', 'Food',
        
        # Travel (25)
        'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 
        'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 'Travel', 
        'Travel', 'Travel', 'Travel', 'Travel', 'Travel',
        
        # Entertainment (22)
        'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment',
        'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 
        'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment', 
        'Entertainment', 'Entertainment', 'Entertainment', 'Entertainment',
        
        # Shopping (32)
        'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping',
        'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping',
        'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping',
        'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping', 'Shopping',
        
        # Health (20)
        'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health',
        'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health', 'Health',
        
        # Utilities (16)
        'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities',
        'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities', 'Utilities',
        
        # Education (16)
        'Education', 'Education', 'Education', 'Education', 'Education', 'Education',
        'Education', 'Education', 'Education', 'Education', 'Education', 'Education', 'Education', 'Education',
        'Education', 'Education',
        
        # Housing (16)
        'Housing', 'Housing', 'Housing', 'Housing', 'Housing', 'Housing',
        'Housing', 'Housing', 'Housing', 'Housing', 'Housing', 'Housing', 'Housing', 'Housing',
        'Housing', 'Housing',
        
        # Insurance (11)
        'Insurance', 'Insurance', 'Insurance', 'Insurance', 'Insurance', 'Insurance',
        'Insurance', 'Insurance', 'Insurance', 'Insurance', 'Insurance',
        
        # Income (25)
        'Other', 'Other', 'Other', 'Other', 'Other', 'Other',
        'Other', 'Other', 'Other', 'Other', 'Other', 'Other',
        'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other', 'Other',
        'Other', 'Other', 'Other'
    ]
}


def main():
    """Train the model"""
    print("🔄 Training expense categorization model...")
    print(f"   - Training samples: {len(TRAINING_DATA['descriptions'])}")
    print(f"   - Categories: {set(TRAINING_DATA['categories'])}")
    
    # Train
    model, vectorizer = MLModel.train(
        TRAINING_DATA['descriptions'],
        TRAINING_DATA['categories']
    )
    
    print("✅ Model trained successfully!")
    print(f"   - Model saved to: {MLModel.MODEL_PATH}")
    print(f"   - Vectorizer saved to: {MLModel.VECTORIZER_PATH}")
    
    # Evaluate
    print("\n📊 Evaluating model...")
    metrics = MLModel.evaluate(
        TRAINING_DATA['descriptions'],
        TRAINING_DATA['categories']
    )
    
    if metrics:
        print(f"\nOverall Metrics:")
        print(f"  - Precision: {metrics['precision']:.3f}")
        print(f"  - Recall:    {metrics['recall']:.3f}")
        print(f"  - F1-Score:  {metrics['f1']:.3f}")
        
        print(f"\nPer-Category Metrics:")
        for category, cat_metrics in sorted(metrics.get('by_category', {}).items()):
            print(f"\n  {category}:")
            print(f"    - Precision: {cat_metrics['precision']:.3f}")
            print(f"    - Recall:    {cat_metrics['recall']:.3f}")
            print(f"    - F1-Score:  {cat_metrics['f1']:.3f}")
            print(f"    - Support:   {cat_metrics['support']}")
    
    # Test predictions
    print("\n🧪 Testing sample predictions:")
    test_cases = [
        ('Starbucks Coffee', ['Latte', 'Croissant']),
        ('Shell Gas Station', ['Premium Fuel']),
        ('Nike Store', ['Running Shoes']),
        ('Amazon', ['Book', 'Electronics']),
        ('City General Hospital', ['Doctor Visit']),
    ]
    
    for merchant, items in test_cases:
        pred = MLModel.predict(merchant, items)
        print(f"  - {merchant} + {items} → {pred}")
    
    print("\n✅ Training complete!")


if __name__ == '__main__':
    main()

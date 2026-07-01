import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from segment_companies import classify_company


class SegmentCompaniesTest(unittest.TestCase):
    def test_classifies_3pl_and_warehouse(self):
        row = {
            'name': 'ABC Logistics',
            'vertical_broad': 'Logística y Transporte',
            'industry': 'Warehousing and Storage',
            'parallel_cat': {'vertical': 'Logistics', 'categoria': '3PL'}
        }
        bucket, reason = classify_company(row)
        self.assertEqual(bucket, '3pl_warehousing')
        self.assertIn('3pl', reason.lower())

    def test_classifies_freight_forwarding(self):
        row = {
            'name': 'Ocean Freight Brokers',
            'vertical_broad': 'Logística y Transporte',
            'industry': 'Freight Forwarding',
            'parallel_cat': {'vertical': 'Transportation', 'categoria': 'Freight'}
        }
        bucket, reason = classify_company(row)
        self.assertEqual(bucket, 'freight_forwarding')

    def test_classifies_transport_terrestre(self):
        row = {
            'name': 'Truckline MX',
            'vertical_broad': 'Logística y Transporte',
            'industry': 'Truck Transportation',
            'parallel_cat': {'vertical': 'Transportation', 'categoria': 'Trucking'}
        }
        bucket, reason = classify_company(row)
        self.assertEqual(bucket, 'transport_terrestre')

    def test_marks_ambiguous_rows_for_review(self):
        row = {
            'name': 'Generic Supply Co',
            'vertical_broad': 'Logística y Transporte',
            'industry': 'Supply chain services',
            'parallel_cat': {'vertical': 'Logistics', 'categoria': 'General'}
        }
        bucket, reason = classify_company(row)
        self.assertEqual(bucket, 'review')
        self.assertIn('review', reason.lower())


if __name__ == '__main__':
    unittest.main()

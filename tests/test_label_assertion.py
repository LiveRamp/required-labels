import os
import unittest
from tests.utils import MockPullRequest

NO_LABELS = None
MOBILE_PRODUCT_LABELS = ['product/all-users', 'product/custom', 'product/invisible', 'product/internal-or-flagged']
MULTIPLE_LABELS = ['cross requested', 'product/internal-or-flagged', 'ready for review']
CHANGE_LABELS = ['change/standard', 'change/major']
ENV_LABELS = ['Prod', 'Non-prod']


# To run (from parent directory): $ python -m unittest tests.LabelAssertionTests
class LabelAssertionTests(unittest.TestCase):

    def test_pr_with_no_labels_no_requirements(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'no_labels.json'))
        self.assertTrue(pr.validate_labels(NO_LABELS, NO_LABELS, NO_LABELS))

    def test_required_any_passes(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'pr_1857_labels.json'))
        self.assertTrue(pr.validate_labels(required_any=MOBILE_PRODUCT_LABELS, required_all=NO_LABELS, banned=NO_LABELS))

    def test_required_any_fails(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'pr_1783_labels.json'))
        self.assertFalse(pr.validate_labels(required_any=MOBILE_PRODUCT_LABELS, required_all=NO_LABELS, banned=NO_LABELS))

    def test_banned_passes(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'pr_1783_labels.json'))
        self.assertTrue(pr.validate_labels(required_any=NO_LABELS, required_all=NO_LABELS, banned=MOBILE_PRODUCT_LABELS))

    def test_banned_fails(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'pr_1858_labels.json'))
        self.assertFalse(pr.validate_labels(required_any=NO_LABELS, required_all=NO_LABELS, banned=MOBILE_PRODUCT_LABELS))

    def test_all_passes(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'pr_1858_labels.json'))
        self.assertTrue(pr.validate_labels(required_any=NO_LABELS, required_all=MULTIPLE_LABELS, banned=NO_LABELS))

    def test_all_fails(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'pr_1830_labels.json'))
        self.assertFalse(pr.validate_labels(required_any=NO_LABELS, required_all=MULTIPLE_LABELS, banned=NO_LABELS))

    def test_required_env_passes(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'nonprod_only_labels.json'))
        self.assertTrue(pr.validate_labels(required_any=NO_LABELS, required_all=NO_LABELS, banned=NO_LABELS,
                                           required_env=ENV_LABELS))

    def test_required_env_fails(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'change_only_labels.json'))
        self.assertFalse(pr.validate_labels(required_any=NO_LABELS, required_all=NO_LABELS, banned=NO_LABELS,
                                            required_env=ENV_LABELS))

    def test_both_groups_pass(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'change_and_prod_labels.json'))
        self.assertTrue(pr.validate_labels(required_any=CHANGE_LABELS, required_all=NO_LABELS, banned=NO_LABELS,
                                           required_env=ENV_LABELS))

    def test_change_present_but_env_missing_fails(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'change_only_labels.json'))
        self.assertFalse(pr.validate_labels(required_any=CHANGE_LABELS, required_all=NO_LABELS, banned=NO_LABELS,
                                            required_env=ENV_LABELS))

    def test_env_present_but_change_missing_fails(self):
        pr = MockPullRequest(os.path.join(os.path.dirname(__file__), 'resources', 'nonprod_only_labels.json'))
        self.assertFalse(pr.validate_labels(required_any=CHANGE_LABELS, required_all=NO_LABELS, banned=NO_LABELS,
                                            required_env=ENV_LABELS))


if __name__ == '__main__':
    unittest.main()

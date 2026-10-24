from django.test import TestCase

TAG = '<meta name="p:domain_verify" content="ec960f1e1bff8ea7ded22ca16ea60d0d"/>'


class PinterestVerificatieTests(TestCase):
    def test_tag_staat_precies_een_keer_in_head_van_homepage(self):
        html = self.client.get("/").content.decode()
        self.assertEqual(html.count("p:domain_verify"), 1)
        self.assertEqual(html.count(TAG), 1)
        self.assertLess(html.index(TAG), html.index("</head>"))

"""Tests for the editable-token menu recommendation endpoint."""

from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.menu.tests.factories import CategoryFactory, MenuItemFactory


class MenuRecommendationApiTests(APITestCase):
    url = reverse("menu-recommend")

    @patch(
        "apps.menu.ai_recommendation.PizzaModelService.predict",
        return_value=(
            "(ORDER (PIZZAORDER (TOPPING PEPPERONI) (NOT (TOPPING OLIVES))))",
            "ready",
        ),
    )
    def test_question_becomes_editable_tokens_and_filters_items(self, _predict):
        category = CategoryFactory(name="Pizza")
        MenuItemFactory(
            category=category,
            name="Pepperoni Classic",
            description="Tomato, cheese and pepperoni",
        )
        MenuItemFactory(
            category=category,
            name="Olive Pepperoni",
            description="Pepperoni with black olives",
        )

        response = self.client.post(
            self.url,
            {"question": "pepperoni but no olives"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        states = {token["value"]: token["state"] for token in response.data["tokens"]}
        self.assertEqual(states["pepperoni"], "wanted")
        self.assertEqual(states["olives"], "excluded")
        self.assertEqual([item["name"] for item in response.data["items"]], ["Pepperoni Classic"])

    def test_edited_tokens_rerank_without_model_call(self):
        category = CategoryFactory(name="Coffee")
        MenuItemFactory(
            category=category,
            name="Mocha Delight",
            description="Rich chocolate with espresso",
        )
        MenuItemFactory(
            category=category,
            name="Almond Mocha",
            description="Chocolate espresso with toasted almonds",
        )

        with patch("apps.menu.ai_recommendation.PizzaModelService.predict") as predict:
            response = self.client.post(
                self.url,
                {
                    "tokens": [
                        {"value": "chocolate", "state": "wanted", "kind": "preference"},
                        {"value": "almond", "state": "excluded", "kind": "preference"},
                    ]
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        predict.assert_not_called()
        self.assertEqual([item["name"] for item in response.data["items"]], ["Mocha Delight"])

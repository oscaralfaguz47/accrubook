import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

LIST_URL = reverse("currencies:currency-list")


def detail_url(code: str) -> str:
    return reverse("currencies:currency-detail", kwargs={"code": code})


def test_list_is_public_paginated_and_ordered_by_code(api_client):
    response = api_client.get(LIST_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 9
    codes = [currency["code"] for currency in body["results"]]
    assert codes == sorted(codes)
    assert body["results"][0] == {
        "code": "BRL",
        "name": "Brazilian Real",
        "decimal_places": 2,
        "is_active": True,
    }


def test_list_runs_a_fixed_number_of_queries(api_client, django_assert_num_queries):
    # One COUNT for the pagination + one SELECT for the page. Guards against N+1 queries.
    with django_assert_num_queries(2):
        api_client.get(LIST_URL)


def test_retrieve_returns_one_currency_by_code(api_client):
    response = api_client.get(detail_url("JPY"))

    assert response.status_code == 200
    assert response.json()["decimal_places"] == 0


def test_retrieve_unknown_code_returns_problem_details(api_client):
    response = api_client.get(detail_url("XXX"))

    assert response.status_code == 404
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Not found.",
        "code": "not_found",
        "instance": detail_url("XXX"),
    }


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("post", LIST_URL),
        ("put", detail_url("USD")),
        ("patch", detail_url("USD")),
        ("delete", detail_url("USD")),
    ],
)
def test_write_methods_are_not_allowed(api_client, method, url):
    response = getattr(api_client, method)(url, data={}, format="json")

    assert response.status_code == 405
    assert response.json()["code"] == "method_not_allowed"
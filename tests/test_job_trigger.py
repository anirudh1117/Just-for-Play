import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_view(client):
    url = reverse("dashboard")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_optimize_trigger(client):
    url = reverse("trigger_optimize_strategy")
    response = client.get(url)
    assert response.status_code in [302, 200]
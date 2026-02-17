"""Unit tests for the Guide Booker Invoice PDF Microservice."""

import base64
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import BookingInvoiceRequest, BookingItem
from app.pdf_generator import generate_invoice_pdf

client = TestClient(app)


# Sample data fixtures
@pytest.fixture
def sample_payload() -> dict:
    """Valid invoice request payload."""
    return {
        "invoice_number": "INV-2026-001",
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com",
        "customer_address": "123 Main St, Bangkok 10110",
        "booking_date": "2026-02-17",
        "due_date": "2026-03-17",
        "guide_name": "Somchai Jaidee",
        "items": [
            {"description": "City Walking Tour – Full Day", "quantity": 2, "unit_price": 75.00},
            {"description": "Temple Guide – Half Day", "quantity": 1, "unit_price": 45.00},
        ],
        "tax_rate": 7.0,
        "discount": 10.00,
        "notes": "Thank you for choosing Guide Booker!",
        "currency": "USD",
    }


@pytest.fixture
def sample_request(sample_payload) -> BookingInvoiceRequest:
    """Parsed BookingInvoiceRequest model."""
    return BookingInvoiceRequest(**sample_payload)


# Model validation tests
class TestBookingItem:
    def test_valid_item(self):
        item = BookingItem(description="Tour", quantity=2, unit_price=50.0)
        assert item.description == "Tour"
        assert item.quantity == 2
        assert item.unit_price == 50.0

    def test_quantity_must_be_positive(self):
        with pytest.raises(Exception):
            BookingItem(description="Tour", quantity=0, unit_price=50.0)

    def test_unit_price_cannot_be_negative(self):
        with pytest.raises(Exception):
            BookingItem(description="Tour", quantity=1, unit_price=-10.0)


class TestBookingInvoiceRequest:
    def test_valid_request(self, sample_payload):
        req = BookingInvoiceRequest(**sample_payload)
        assert req.invoice_number == "INV-2026-001"
        assert req.customer_name == "Jane Doe"
        assert len(req.items) == 2

    def test_default_values(self):
        minimal = {
            "invoice_number": "INV-001",
            "customer_name": "Test",
            "customer_email": "test@test.com",
            "customer_address": "Addr",
            "booking_date": "2026-01-01",
            "due_date": "2026-02-01",
            "guide_name": "Test Guide",
            "items": [{"description": "Item", "quantity": 1, "unit_price": 10}],
        }
        req = BookingInvoiceRequest(**minimal)
        assert req.tax_rate == 0.0
        assert req.discount == 0.0
        assert req.currency == "USD"
        assert req.notes is None

    def test_items_cannot_be_empty(self, sample_payload):
        sample_payload["items"] = []
        with pytest.raises(Exception):
            BookingInvoiceRequest(**sample_payload)

    def test_tax_rate_max_100(self, sample_payload):
        sample_payload["tax_rate"] = 150
        with pytest.raises(Exception):
            BookingInvoiceRequest(**sample_payload)

    def test_date_parsing(self, sample_payload):
        req = BookingInvoiceRequest(**sample_payload)
        assert req.booking_date == date(2026, 2, 17)
        assert req.due_date == date(2026, 3, 17)


# PDF generation tests
class TestPdfGenerator:
    def test_returns_bytes(self, sample_request):
        result = generate_invoice_pdf(sample_request)
        assert isinstance(result, bytes)

    def test_pdf_header(self, sample_request):
        result = generate_invoice_pdf(sample_request)
        assert result[:5] == b"%PDF-"

    def test_pdf_not_empty(self, sample_request):
        result = generate_invoice_pdf(sample_request)
        assert len(result) > 100

    def test_single_item_invoice(self):
        req = BookingInvoiceRequest(
            invoice_number="INV-SINGLE",
            customer_name="Solo Traveler",
            customer_email="solo@test.com",
            customer_address="456 Side St",
            booking_date=date(2026, 1, 1),
            due_date=date(2026, 2, 1),
            guide_name="Guide A",
            items=[BookingItem(description="Single Tour", quantity=1, unit_price=100.0)],
        )
        result = generate_invoice_pdf(req)
        assert result[:5] == b"%PDF-"

    def test_no_discount_no_tax(self):
        req = BookingInvoiceRequest(
            invoice_number="INV-ZERO",
            customer_name="Zero Tax",
            customer_email="zero@test.com",
            customer_address="789 Free St",
            booking_date=date(2026, 3, 1),
            due_date=date(2026, 4, 1),
            guide_name="Guide B",
            items=[BookingItem(description="Free Tour", quantity=1, unit_price=200.0)],
            tax_rate=0.0,
            discount=0.0,
        )
        result = generate_invoice_pdf(req)
        assert result[:5] == b"%PDF-"

    def test_non_usd_currency(self):
        req = BookingInvoiceRequest(
            invoice_number="INV-THB",
            customer_name="Thai Customer",
            customer_email="thai@test.com",
            customer_address="Bangkok",
            booking_date=date(2026, 1, 1),
            due_date=date(2026, 2, 1),
            guide_name="Guide C",
            items=[BookingItem(description="Tour", quantity=1, unit_price=2500.0)],
            currency="THB",
        )
        result = generate_invoice_pdf(req)
        assert result[:5] == b"%PDF-"


# API endpoint tests


class TestRootEndpoint:
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_body(self):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "Success"
        assert data["message"] == "Hello World"


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "invoice-service"


class TestInvoiceEndpoint:
    def test_returns_200(self, sample_payload):
        response = client.post("/invoices", json=sample_payload)
        assert response.status_code == 200

    def test_returns_pdf_content_type(self, sample_payload):
        response = client.post("/invoices", json=sample_payload)
        assert response.headers["content-type"] == "application/pdf"

    def test_returns_attachment_header(self, sample_payload):
        response = client.post("/invoices", json=sample_payload)
        disposition = response.headers["content-disposition"]
        assert "attachment" in disposition
        assert "INV-2026-001.pdf" in disposition

    def test_response_is_valid_pdf(self, sample_payload):
        response = client.post("/invoices", json=sample_payload)
        assert response.content[:5] == b"%PDF-"

    def test_missing_required_field(self):
        response = client.post("/invoices", json={"invoice_number": "INV-001"})
        assert response.status_code == 422

    def test_empty_items_rejected(self, sample_payload):
        sample_payload["items"] = []
        response = client.post("/invoices", json=sample_payload)
        assert response.status_code == 422

    def test_invalid_json_body(self):
        response = client.post(
            "/invoices",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_get_method_not_allowed(self):
        response = client.get("/invoices")
        assert response.status_code == 405

"""Guide Booker — Invoice PDF Microservice.

FastAPI application that generates professional PDF invoices
from JSON booking data, containerised for AWS Lambda.
"""

from io import BytesIO

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from mangum import Mangum

from app.models import BookingInvoiceRequest
from app.pdf_generator import generate_invoice_pdf

app = FastAPI(
    title="Guide Booker Invoice Service",
    description="Microservice for generating professional PDF invoices from booking data.",
    version="1.0.0",
)


@app.get("/")
def health_check():
    """Lightweight health-check endpoint."""
    return {"status": "Success", "message": "Hello World"}



@app.get("/health")
def health_check():
    """Lightweight health-check endpoint."""
    return {"status": "healthy", "message": "invoice-service"}


@app.post(
    "/invoices",
    response_class=StreamingResponse,
    summary="Generate a PDF invoice",
    description="Accepts JSON booking data and returns a downloadable PDF invoice.",
)
def create_invoice(payload: BookingInvoiceRequest):
    """Generate a PDF invoice from the supplied booking data."""
    pdf_bytes = generate_invoice_pdf(payload)
    filename = f"{payload.invoice_number}.pdf"

    return StreamingResponse(
        content=BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── AWS Lambda handler (Mangum wraps the ASGI app) ─────────────────
handler = Mangum(app)


# ── Local development server ───────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

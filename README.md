# Guide Booker — Invoice PDF Microservice

A standalone microservice that generates professional PDF invoices from JSON booking data. Built with **FastAPI** and containerized for **AWS Lambda** deployment.

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.12** | Runtime |
| **FastAPI** | Web framework with automatic request validation |
| **Mangum** | ASGI adapter for AWS Lambda |
| **ReportLab** | PDF generation engine |
| **Docker** | AWS Lambda container image (`public.ecr.aws/lambda/python:3.12`) |

## Project Structure

```
keda/
├── Dockerfile              # AWS Lambda-compatible container image
├── requirements.txt        # Python dependencies
├── README.md
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI app + Lambda handler
    ├── models.py           # Pydantic request/response models
    └── pdf_generator.py    # ReportLab PDF invoice builder
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root endpoint — returns a hello world message |
| `POST` | `/invoices` | Generate a PDF invoice from booking data |

### Request Body (`POST /invoices`)

```json
{
  "invoice_number": "INV-2026-001",
  "customer_name": "Jane Doe",
  "customer_email": "jane@example.com",
  "customer_address": "123 Main St, Jakarta 10110",
  "booking_date": "2026-02-17",
  "due_date": "2026-03-17",
  "guide_name": "Jane Doe",
  "items": [
    {
      "description": "City Walking Tour – Full Day",
      "quantity": 2,
      "unit_price": 75.00
    },
    {
      "description": "Temple Guide – Half Day",
      "quantity": 1,
      "unit_price": 45.00
    }
  ],
  "tax_rate": 7.0,
  "discount": 10.00,
  "notes": "Thank you for choosing Guide Booker!",
  "currency": "USD"
}
```

### Response

Returns a downloadable PDF file (`application/pdf`) with `Content-Disposition: attachment`.

## Running Locally

### 1. Setup Virtual Environment

```bash
cd keda
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install uvicorn
```

### 2. Start the Development Server

```bash
python -m app.main
```

The server starts at **http://localhost:8000**. Interactive API docs are available at **http://localhost:8000/docs**.

### 3. Test the Endpoint

```bash
#  check
curl http://localhost:8000

# Generate invoice PDF
curl -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2026-001",
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "customer_address": "123 Main St, Bangkok 10110",
    "booking_date": "2026-02-17",
    "due_date": "2026-03-17",
    "items": [
      {"description": "City Walking Tour", "quantity": 2, "unit_price": 75.00},
      {"description": "Temple Guide", "quantity": 1, "unit_price": 45.00}
    ],
    "tax_rate": 7.0,
    "discount": 10.00,
    "notes": "Thank you!",
    "currency": "USD"
  }' --output invoice.pdf
```

## Running with Docker (AWS Lambda)

### 1. Build the Image

```bash
docker build -t guide-booker-invoice .
```

### 2. Run the Container

```bash
docker run -d -p 9000:8080 guide-booker-invoice
```

### 3. Invoke the Lambda Function

```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "resource": "/invoices",
    "path": "/invoices",
    "httpMethod": "POST",
    "headers": {"Content-Type": "application/json"},
    "requestContext": {"resourcePath": "/invoices", "httpMethod": "POST", "path": "/invoices"},
    "body": "{\"invoice_number\":\"INV-001\",\"customer_name\":\"Jane Doe\",\"customer_email\":\"jane@example.com\",\"customer_address\":\"123 Main St\",\"booking_date\":\"2026-02-17\",\"due_date\":\"2026-03-17\",\"items\":[{\"description\":\"City Tour\",\"quantity\":2,\"unit_price\":75}],\"tax_rate\":7,\"discount\":10,\"notes\":\"Thanks!\",\"currency\":\"USD\"}",
    "isBase64Encoded": false
  }'
```

The response body will contain a **base64-encoded** PDF that can be decoded:

```bash
# Pipe the response to decode the PDF
... | python3 -c "import sys,json,base64; r=json.load(sys.stdin); open('invoice.pdf','wb').write(base64.b64decode(r['body']))"
```

## Deploying to AWS Lambda

1. Push the Docker image to **Amazon ECR**
2. Create a Lambda function with **Container image** as the package type
3. Point it to your ECR image
4. Add an **API Gateway** trigger or enable a **Lambda Function URL**

The `CMD` in the Dockerfile is already configured to use the Mangum handler (`app.main.handler`).

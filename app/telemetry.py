from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
import os

def setup_telemetry(app, engine):
    """Initialize OpenTelemetry instrumentation"""
    
    # Create a resource with service name
    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "chatwoot-dify"),
        "service.instance.id": "instance-1"  
    })
    
    # Configure the tracer
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Set up the OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
        insecure=True
    )
    
    # Add span processor
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        service="chatwoot-dify"
    )
    
    # Instrument Celery
    CeleryInstrumentor().instrument()
    
    # Instrument HTTPX
    HTTPXClientInstrumentor().instrument() 
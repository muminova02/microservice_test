import logging
import os
from functools import lru_cache
from typing import Optional

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag to prevent double instrumentation
_instrumentation_done = False


@lru_cache()
def get_tracer():
    """
    Get the OpenTelemetry tracer or a dummy if not available
    """
    # Import config here to avoid circular imports
    from app.config import get_settings
    settings = get_settings()

    # Check if Zipkin is available first
    if not is_zipkin_available():
        logger.warning("Zipkin not available, using dummy tracer")
        return _create_dummy_tracer()

    # Try to import OpenTelemetry packages
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.zipkin.json import ZipkinExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.semconv.resource import ResourceAttributes

        # Create a resource with service information
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: "auth-service",
            ResourceAttributes.SERVICE_VERSION: settings.API_VERSION,
        })

        # Set up the trace provider with the resource
        trace.set_tracer_provider(TracerProvider(resource=resource))

        # Get a tracer
        tracer = trace.get_tracer(__name__)

        # Configure the Zipkin exporter (without service_name parameter)
        zipkin_url = settings.ZIPKIN_URL
        logger.info(f"Connecting to Zipkin at: {zipkin_url}")

        # Create ZipkinExporter without service_name parameter
        zipkin_exporter = ZipkinExporter(
            endpoint=f"{zipkin_url}/api/v2/spans"
        )

        # Add the exporter to the trace provider
        span_processor = BatchSpanProcessor(zipkin_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        logger.info("OpenTelemetry tracing initialized with Zipkin exporter")
        return tracer

    except ImportError as e:
        logger.warning(f"OpenTelemetry dependencies not found: {e}. Telemetry disabled.")
        return _create_dummy_tracer()
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}. Using dummy tracer.")
        return _create_dummy_tracer()


def _create_dummy_tracer():
    """
    Create a dummy tracer for when OpenTelemetry is not available
    """
    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()

    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key, value):
            pass

        def add_event(self, name, attributes=None):
            pass

        def record_exception(self, exception):
            pass

        def set_status(self, status):
            pass

    return DummyTracer()


def instrument_app(app):
    """
    Instrument a FastAPI app with OpenTelemetry if available
    """
    global _instrumentation_done

    if _instrumentation_done:
        logger.warning("Application already instrumented, skipping")
        return False

    if not is_zipkin_available():
        logger.warning("Zipkin not available, skipping instrumentation")
        return False

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument HTTPX for outgoing requests
        HTTPXClientInstrumentor().instrument()

        # Instrument logging
        LoggingInstrumentor().instrument()

        _instrumentation_done = True
        logger.info("Application instrumented with OpenTelemetry")
        return True
    except ImportError:
        logger.warning("OpenTelemetry instrumentation skipped - dependencies not found")
        return False
    except Exception as e:
        logger.error(f"Failed to instrument application: {e}")
        return False


def is_zipkin_available() -> bool:
    """
    Check if Zipkin is available
    """
    try:
        from app.config import get_settings
        settings = get_settings()

        import socket
        import urllib.parse

        zipkin_url = settings.ZIPKIN_URL
        parsed_url = urllib.parse.urlparse(zipkin_url)
        zipkin_host = parsed_url.hostname or "localhost"

        # Try to resolve the hostname
        zipkin_ip = socket.gethostbyname(zipkin_host)
        logger.info(f"Zipkin host {zipkin_host} resolved to {zipkin_ip}")
        return True

    except Exception as e:
        logger.warning(f"Zipkin not available: {e}")
        return False


def check_zipkin_connection():
    """
    Try to resolve Zipkin host to verify connectivity
    """
    try:
        from app.config import get_settings
        settings = get_settings()

        import socket
        import urllib.parse

        zipkin_url = settings.ZIPKIN_URL
        parsed_url = urllib.parse.urlparse(zipkin_url)
        zipkin_host = parsed_url.hostname or "localhost"

        logger.info(f"Attempting to resolve Zipkin host: {zipkin_host}")
        zipkin_ip = socket.gethostbyname(zipkin_host)
        logger.info(f"Resolved Zipkin IP: {zipkin_ip}")

        # Try to make a simple HTTP request to test connectivity
        try:
            import requests
            response = requests.get(f"{zipkin_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("Zipkin health check passed")
                return True
            else:
                logger.warning(f"Zipkin health check failed with status: {response.status_code}")
                return False
        except ImportError:
            logger.info("Requests library not available, skipping HTTP health check")
            return True  # DNS resolution worked, assume it's okay
        except Exception as e:
            logger.warning(f"Zipkin HTTP health check failed: {e}")
            return False

    except Exception as e:
        logger.error(f"Error checking Zipkin connectivity: {str(e)}")
        return False


# Global tracer instance - will be dummy if Zipkin not available
tracer = get_tracer()
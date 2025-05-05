from unittest.mock import patch

import pytest

from ..decorators import trace_function, track_errors


def test_trace_function():
    """Test that trace_function decorator properly creates spans."""
    @trace_function(name="test-span")
    def test_func():
        return "success"
    
    with patch('opentelemetry.trace.get_tracer') as mock_tracer:
        result = test_func()
        assert result == "success"
        assert mock_tracer.return_value.start_as_current_span.called
        assert mock_tracer.return_value.start_as_current_span.call_args[1]["name"] == "test-span"


def test_track_errors():
    """Test that track_errors decorator properly records exceptions."""
    @track_errors
    def failing_func():
        raise ValueError("test error")
    
    with patch('opentelemetry.trace.get_current_span') as mock_span:
        mock_span.return_value.is_recording.return_value = True
        with pytest.raises(ValueError):
            failing_func()
        assert mock_span.return_value.record_exception.called


def test_track_errors_when_not_recording():
    """Test that track_errors doesn't record when span isn't recording."""
    @track_errors
    def failing_func():
        raise ValueError("test error")
    
    with patch('opentelemetry.trace.get_current_span') as mock_span:
        mock_span.return_value.is_recording.return_value = False
        with pytest.raises(ValueError):
            failing_func()
        assert not mock_span.return_value.record_exception.called

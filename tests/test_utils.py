import time
from datetime import datetime

from auris_tools.utils import (
    collect_processing_time,
    collect_timestamp,
    generate_uuid,
    parse_timestamp,
)


def test_collect_timestamp():
    timestamp_str = collect_timestamp()
    assert isinstance(timestamp_str, str)

    timestamp_dt = collect_timestamp(as_str=False)
    assert isinstance(timestamp_dt, datetime)
    assert type(timestamp_str) == type(timestamp_dt.isoformat())


def test_generate_uuid():
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    assert isinstance(uuid1, str)
    assert isinstance(uuid2, str)
    assert uuid1 != uuid2


def test_collect_processing_time():
    with collect_processing_time() as elapsed:
        time.sleep(1)  # Simulate some processing time
    assert elapsed() >= 1.0


def test_collect_processing_time_multiple_calls():
    with collect_processing_time() as elapsed:
        time.sleep(0.5)
        mid_time = elapsed()
        time.sleep(0.5)
        end_time = elapsed()
    assert mid_time >= 0.5
    assert end_time >= 1.0
    assert end_time >= mid_time


def test_parse_timestamp():
    dt = datetime.now()
    iso_str = dt.isoformat()

    assert parse_timestamp(dt) == dt
    assert parse_timestamp(iso_str) == dt

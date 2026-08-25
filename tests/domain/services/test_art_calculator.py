"""Unit tests for ARTCalculator (average response time)."""

from domain.entities.report_data import RawConversationData, RawMessageData
from domain.metrics.art import ARTCalculator


def _conv(msgs: list[RawMessageData]) -> RawConversationData:
    return RawConversationData(
        id="1",
        contact="c",
        phone="p",
        msgs=msgs,
        raw_created="2026-08-01 09:00:00",
    )


def test_art_is_mean_of_all_response_deltas():
    calc = ARTCalculator()
    conv = _conv(
        [
            RawMessageData("2026-08-01 09:00:00", "received", None, None),
            RawMessageData("2026-08-01 09:10:00", "sent", "10", "Agent"),
            RawMessageData("2026-08-01 09:20:00", "received", None, None),
            RawMessageData("2026-08-01 09:30:00", "sent", "10", "Agent"),
        ]
    )
    assert calc.calculate(conv) == 10.0  # (10 + 10) / 2


def test_art_with_varying_deltas():
    calc = ARTCalculator()
    conv = _conv(
        [
            RawMessageData("2026-08-01 09:00:00", "received", None, None),
            RawMessageData("2026-08-01 09:05:00", "sent", "10", "Agent"),
            RawMessageData("2026-08-01 09:10:00", "received", None, None),
            RawMessageData("2026-08-01 09:20:00", "sent", "10", "Agent"),
            RawMessageData("2026-08-01 09:25:00", "received", None, None),
            RawMessageData("2026-08-01 09:35:00", "sent", "10", "Agent"),
        ]
    )
    assert calc.calculate(conv) == 8.33  # (5 + 10 + 10) / 3


def test_art_none_without_pairs():
    calc = ARTCalculator()
    conv = _conv(
        [
            RawMessageData("2026-08-01 09:00:00", "received", None, None),
            RawMessageData("2026-08-01 09:10:00", "received", None, None),
        ]
    )
    assert calc.calculate(conv) is None


def test_art_ignores_reply_without_prior_client_message():
    calc = ARTCalculator()
    conv = _conv(
        [
            RawMessageData("2026-08-01 09:00:00", "sent", "10", "Agent"),
            RawMessageData("2026-08-01 09:10:00", "received", None, None),
            RawMessageData("2026-08-01 09:15:00", "sent", "10", "Agent"),
        ]
    )
    assert calc.calculate(conv) == 5.0

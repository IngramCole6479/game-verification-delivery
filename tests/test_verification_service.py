from typing import Any

from src.verification_service import VerificationRequest, VerificationService


class FakeClient:
    def __init__(self, state: str) -> None:
        self.state = state
        self.resends: list[str] = []

    def sms_events(self, message_id: str) -> dict[str, Any]:
        return {"ok": True, "data": {"delivery_state": self.state}}

    def resend_sms(self, message_id: str) -> dict[str, Any]:
        self.resends.append(message_id)
        return {"ok": True, "data": {}}


def test_stuck_code_is_resent_and_surfaces_queued_state() -> None:
    client = FakeClient("stuck")
    result = VerificationService(client).resend_if_stuck(
        VerificationRequest(player_id="p-7", message_id="m-9")
    )

    assert result.action == "resent"
    assert result.delivery_state == "queued"
    assert client.resends == ["m-9"]


def test_delivered_code_is_left_alone() -> None:
    client = FakeClient("delivered")
    result = VerificationService(client).resend_if_stuck(
        VerificationRequest(player_id="p-7", message_id="m-9")
    )

    assert result.action == "unchanged"
    assert result.delivery_state == "delivered"
    assert client.resends == []

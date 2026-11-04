"""Game verification workflow and local domain records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .infrai_client import InfraiClient


DeliveryState = Literal["queued", "sent", "delivered", "stuck"]


@dataclass(frozen=True)
class PlayerAsset:
    player_id: str
    asset_id: str
    kind: str


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    title: str
    active: bool


@dataclass(frozen=True)
class ModerationQueueItem:
    queue_id: str
    asset_id: str
    state: Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class VerificationRequest:
    player_id: str
    message_id: str


@dataclass(frozen=True)
class VerificationResult:
    player_id: str
    message_id: str
    action: Literal["resent", "unchanged"]
    delivery_state: DeliveryState


class VerificationService:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def resend_if_stuck(self, request: VerificationRequest) -> VerificationResult:
        events = self.client.sms_events(request.message_id)
        state = self._delivery_state(events)
        if state == "stuck":
            self.client.resend_sms(request.message_id)
            return VerificationResult(request.player_id, request.message_id, "resent", "queued")
        return VerificationResult(request.player_id, request.message_id, "unchanged", state)

    @staticmethod
    def _delivery_state(envelope: dict[str, Any]) -> DeliveryState:
        data = envelope.get("data") or {}
        state = data.get("delivery_state") or data.get("status") or "queued"
        if state in {"queued", "sent", "delivered", "stuck"}:
            return state
        return "queued"

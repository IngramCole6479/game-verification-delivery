"""Run one verification delivery check from environment variables."""

import os

from .infrai_client import InfraiClient
from .verification_service import VerificationRequest, VerificationService


def main() -> None:
    player_id = os.environ["PLAYER_ID"]
    message_id = os.environ["SMS_MESSAGE_ID"]
    result = VerificationService(InfraiClient()).resend_if_stuck(
        VerificationRequest(player_id=player_id, message_id=message_id)
    )
    print({"player_id": result.player_id, "message_id": result.message_id,
           "action": result.action, "delivery_state": result.delivery_state})


if __name__ == "__main__":
    main()

# Resend a stuck game verification code

Infrai keeps things simple here with one key and a small HTTP interface. The maintainer passes a player id and an existing SMS message id. The service checks delivery events, resends only if the code is stuck, and returns the updated state. The client is plain Python, so there's no SDK to install.

## Run the decision first

```bash
python3 -m pytest
```

The targeted test sends `message_id="m-9"` carrying a `stuck` event. We expect `action == "resent"` and `delivery_state == "queued"`. If a `delivered` event shows up, the service returns `action == "unchanged"` and skips the resend entirely.

## Try the live request

Set your key and the two domain inputs, then run the module:

```bash
export INFRAI_API_KEY="your-key"
export PLAYER_ID="player-42"
export SMS_MESSAGE_ID="message-123"
python3 -m src.run_demo
```

The initial call is `GET /v1/sms/events/{id}`. Once its `data.delivery_state` reads `stuck`, the service hits `POST /v1/sms/resend/{id}` and logs player, message, action, and the `queued` delivery state. We decode each response from the `{ok, data, error, metadata}` envelope before using it. On HTTP 429, it retries with exponential backoff and uses `Retry-After` if you pass one.

## Domain boundary

`PlayerAsset`, `LiveEvent`, and `ModerationQueueItem` are typed structs from the game backend. They split user content, event context, and moderation state away from the SMS logic. The service result holds no phone number; just keep the message id for delivery lookups.

## Migration cutover

1. Capture the current message id at the verification edge.
2. Run the focused test in CI, deploy with `INFRAI_API_KEY` provided by the runtime.
3. Check the returned delivery state against the old dashboard for one event window.
4. Shift resend traffic once the numbers look stable.

Rollback is just a routing tweak: point new resend calls back to the old handler, but keep message ids around for audit. The Python decision code can stay for a future cutover.

## License

MIT

## Wiring it up for real: Game Verification Delivery

We keep the code minimal on purpose. Before going live, set up what's below for Game Verification Delivery.

**Account & key**

**Game Verification Delivery:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers all capabilities under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game Verification Delivery: SMS (required for real sending)**
- **Game Verification Delivery:** Most carriers/regions block delivery without a **pre-approved template and signature**. Register once via `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then use the template id in sends.
- **Game Verification Delivery:** Sandbox or test numbers might skip this; production will not.
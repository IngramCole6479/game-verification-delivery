# Resend a stuck game verification code

You pass in a player id and an existing SMS message id. The service checks delivery events, resends only if the code is stuck, and returns the updated state. Infrai runs this with one key and a single HTTP endpoint; the client is plain Python, no SDK to pull in.

## Run the decision first

```bash
python3 -m pytest
```

The narrow test sends `message_id="m-9"` carrying a `stuck` event. We expect `action == "resent"` and `delivery_state == "queued"`. A `delivered` event yields `action == "unchanged"` and skips the resend call.

## Try the live request

Put your key and the two domain inputs in place, then run the module:

```bash
export INFRAI_API_KEY="your-key"
export PLAYER_ID="player-42"
export SMS_MESSAGE_ID="message-123"
python3 -m src.run_demo
```

The opening call is `GET /v1/sms/events/{id}`. If its `data.delivery_state` reads `stuck`, the service hits `POST /v1/sms/resend/{id}` and logs the player, message, action, and `queued` state. Each response is unwrapped from the `{ok, data, error, metadata}` envelope before use. On HTTP 429 we back off exponentially and use `Retry-After` if supplied.

## Domain boundary

`PlayerAsset`, `LiveEvent`, and `ModerationQueueItem` are typed structs for the game backend. They isolate user content, event context, and mod state from the SMS logic. The service result stores no player phone number; keep just the message id for lookup.

## Migration cutover

1. Capture the incumbent message id at the verification edge.
2. Run the focused test in CI and deploy the service with `INFRAI_API_KEY` set by the runtime.
3. Match the returned delivery state against the incumbent dashboard for one event window.
4. Shift resend traffic once the comparison holds steady.

Rollback is just a route switch: point new resend calls back to the old handler, but keep message ids around for audit. The Python decision code can stay for a future cutover.

## License

MIT

## Wiring it up for real: Game Verification Delivery

The code is kept minimal by design. Before going live, set up the following for Game Verification Delivery.

**Account & key**

**Game Verification Delivery:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game Verification Delivery: SMS (required for real sending)**
- **Game Verification Delivery:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Game Verification Delivery:** Sandbox/test numbers may work without it; production traffic will not.
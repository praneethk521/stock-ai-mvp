# Price Alerts

Price alerts are persisted and scoped to the authenticated user context. Each alert watches one ticker for a price at or above, or at or below, a positive target value.

## Behavior

- A user may keep up to 100 alerts.
- Evaluation fetches one current provider snapshot per distinct active ticker.
- A met threshold records the observed price and trigger time, then deactivates the alert so it fires only once.
- Triggered alerts can be re-armed; re-arming clears the prior trigger time.
- Users cannot list, update, or delete another user's alerts.

## API

- `GET /api/v1/alerts` lists alerts; `active_only=true` filters inactive alerts.
- `POST /api/v1/alerts` creates an alert.
- `PUT /api/v1/alerts/{alert_id}` updates or re-arms an alert.
- `DELETE /api/v1/alerts/{alert_id}` deletes an alert.
- `POST /api/v1/alerts/evaluate` evaluates all active alerts for the current user.

The local UI invokes evaluation on demand. Production notification delivery requires a scheduled worker, an outbox for reliable delivery, and a configured email, SMS, or push provider. Those components are deliberately not part of the synchronous API process.

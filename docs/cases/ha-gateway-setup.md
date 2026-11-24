# Gateway panel stalls during first Home Assistant setup

Case `ha-gateway-setup` · **confirmed-local**

The gateway supplies its own Home Assistant integration. On first startup with the YAML configuration present and no existing entry, the integration became stuck during the import flow even though configuration validation had passed. The correction belongs to the custom component.

## Corrected setup

The domain setup schedules the import and returns so the config entry can be set up. The entry setup performs the coordinator's first refresh before forwarding the platforms. The condensed excerpt shows the scheduling call used in the deployed component.

```python
async def async_setup(hass, config):
    if DOMAIN in config and not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data={}
            )
        )
    return True
```

## Verification and scope

After the corrected component started, the installation audit confirmed three dashboard tabs and all 25 entities via the Home Assistant API. The test changed the panel's visibility switch and checked that the existing Linphone forwarding state was preserved. Live call tests for the audio fixes are recorded separately in the [Bluetooth case](sco-false-hangup.md). A route-status reapply alone does not exercise a new live call.

Incoming Linphone Push and the local outgoing SIP account have different roles. A gap in the outgoing account's registration was observed and later cleared. The cause of the gap was not established.

The separate forwarding controls have their own local tests. Nine tests passed again on 24 November 2026, covering opt-in, independent queues, recovered messages, credentials changes, the simulated HTTP request, and suppression of retries after an uncertain submission. A live Telegram delivery was outside these tests.

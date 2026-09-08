# Staged Endurance Test Plan

Use `endurance_harness.py` only with authorized test device tokens and a non-production or controlled pilot endpoint. Results are synthetic and must be labelled as such. Begin with 5 devices, then 20, 80 and finally 160. Monitor API latency, database growth, rejected points, duplicate handling, worker heartbeats, event deduplication, queue depth and recovery. Compare received messages with the expected count and retain the generated JSON evidence.

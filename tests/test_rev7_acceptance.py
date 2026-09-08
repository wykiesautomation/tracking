from types import SimpleNamespace
from app.acceptance import stats,can_accept

def campaign(states):return SimpleNamespace(items=[SimpleNamespace(state=x,blocking=True) for x in states])
def test_release_gate_blocks_open_items():assert not can_accept(campaign(['PASS','NOT_TESTED']))
def test_release_gate_allows_all_pass():assert can_accept(campaign(['PASS','PASS']))
def test_stats_counts():
 s=stats(campaign(['PASS','FAIL','IN_PROGRESS']));assert s['passed']==1 and s['failed']==1 and s['blocking']==2

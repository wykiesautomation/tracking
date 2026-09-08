from app.reporting import csv_bytes

def test_csv_has_utf8_bom_and_headers():
 data=csv_bytes(['a','b'],[[1,2]]);assert data.startswith(b'\xef\xbb\xbf');assert b'a,b' in data

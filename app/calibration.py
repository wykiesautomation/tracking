from bisect import bisect_left

def validate_points(points,capacity):
    errors=[]
    if len(points)<2:errors.append('At least two calibration points are required.')
    ordered=sorted(points,key=lambda p:p.raw_value)
    for i,p in enumerate(ordered):
        if not 0<=p.percent<=100:errors.append(f'Point {i+1}: percent must be 0 to 100.')
        if not 0<=p.litres<=capacity:errors.append(f'Point {i+1}: litres exceed tank capacity.')
        if i and p.raw_value<=ordered[i-1].raw_value:errors.append('Raw values must be strictly increasing.')
        if i and p.litres<ordered[i-1].litres:errors.append('Litres must be monotonic increasing.')
    return errors,ordered

def interpolate(raw,points):
    pts=sorted(points,key=lambda p:p.raw_value)
    if not pts:return None,None,'NO_CALIBRATION'
    if raw<=pts[0].raw_value:return pts[0].percent,pts[0].litres,'BELOW_RANGE' if raw<pts[0].raw_value else 'GOOD'
    if raw>=pts[-1].raw_value:return pts[-1].percent,pts[-1].litres,'ABOVE_RANGE' if raw>pts[-1].raw_value else 'GOOD'
    for a,b in zip(pts,pts[1:]):
        if a.raw_value<=raw<=b.raw_value:
            ratio=(raw-a.raw_value)/(b.raw_value-a.raw_value);return a.percent+ratio*(b.percent-a.percent),a.litres+ratio*(b.litres-a.litres),'GOOD'
    return None,None,'INVALID'

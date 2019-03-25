from scaffoldmaker.utils.interpolation import sampleCubicHermiteCurves    
        
def getCenterLine(options):
    if 'Tube type' in options:
        if options['Tube type'] == 1: # Straight tube
            cx = [[-4.0, 1.0, 3.0], [ 1.0, 2.0, 0.0 ] ]
            cd1 = [[ 5.0, 1.0, -3.0 ], [ 5.0, 1.0, -3.0 ]]
        elif options['Tube type'] == 2: # Human colon in x-y plane
            cx = [ [ 0.0, 0.0, 0.0], [0.0, 10.0, 0.0], [5.0, 9.0, 0.0], [ 10.0, 10.0, 0.0 ], [ 10.0, -2.0, 0.0], [ 7.0, -4.0, 0.0] ]
            cd1 = [ [ 0.0, 10.0, 0.0 ], [ 5.0, 5.0, 0.0 ], [5.0, 0.0, 0.0], [ 5.0, -5.0, 0.0 ], [ -3.0, -5.0, 0.0 ], [ -3.0, 0.0, 0.0 ]]
        elif options['Tube type'] == 3: # Human colon in 3D
            cx = [ [ 0.0, 0.0, 0.0], [0.0, 10.0, 3.0], [5.0, 9.0, 0.0], [ 10.0, 10.0, 2.0 ], [15.0, 15.0, 7.0], [ 20.0, -2.0, 0.0], [ 10.0, -4.0, -0.0] ]
            cd1 = [ [ 0.0, 10.0, 3.0 ], [ 5.0, 5.0, 0.0 ], [5.0, 0.0, 0.0], [ 10.0, -5.0, 0.0 ], [12.0, 12.0, 0.0], [ 5.0, -12.0, -5.0 ], [ -8.0, 0.0, 0.0 ]]
        else:
            return None
    else:
        return None
    points = sampleCubicHermiteCurves(cx, cd1, 300)[0]
    if isinstance(points, list):
        pathDict = {}
        pathDict["CameraPath"] = []
        pathDict["NumberOfPoints"] = len(points)
        for i in range(0, len(points)):
            pathDict["CameraPath"].extend(points[i])
        return pathDict
        
    return None
